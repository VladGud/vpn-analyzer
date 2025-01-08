import time
import sys
import threading
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from ..utils.concurrent_queue import ConcurrentQueue
from ..flow.flow import Flow
from ..flow.flow_storage import FlowStorage

class DetectWorker(threading.Thread):
    def __init__(
            self,
            model_pipeline,
            start_packet_number_threshold=30,
            end_packet_number_threshold=40,
            predict_rate=5,
            flow_storage_size=1000,
            flow_number_for_detect=1,
            detection_time_interval=10,
            vpn_to_novpn_ratio = 0.0,
            total_detected_flow_threshold = 3,
            input_queue=None
    ):
        threading.Thread.__init__(self)
        self.daemon = True        

        self.input_queue = input_queue

        self.flow_storage = FlowStorage(fix_size=flow_storage_size)
        self.model_pipeline = model_pipeline

        self.predict_rate = predict_rate
        self.start_threshold_packet_number = start_packet_number_threshold
        self.end_packet_number_threshold = end_packet_number_threshold

        self.possible_vpn_flow = defaultdict(int)
        self.possible_non_vpn_flow = defaultdict(int)
        
        # detect threshold
        self.detection_time_vpn_flows = defaultdict(list)
        self.flow_number_for_detect = flow_number_for_detect
        self.detection_time_interval = detection_time_interval
        self.total_detected_flow_threshold = total_detected_flow_threshold
        self.vpn_to_novpn_ratio = vpn_to_novpn_ratio

        self.extract_time = []
        self.model_pipeline_time = []

        # print stats:
        self.flow_lines = defaultdict(int)
        self.total_lines = 60

    def run(self):
        while True:
            if not self.input_queue.empty():
                packet = self.input_queue.pop()
                self._packet_processing(packet)
            else:
                time.sleep(0.1)

    def set_input(self, input_queue):
        self.input_queue = input_queue

    # def _extract_flow_key(self, packet):
    #     return ''.join(sorted(f"{packet['IP'].src} -- {packet['IP'].dst}"))
    def _extract_flow_key(self, packet):
        flow_key = self.flow_storage.extract_flow_key_for_packet(packet)
        node_1, node_2 = flow_key.split('<-->')
        return f"{node_1.split(':')[0]}<-->{node_2.split(':')[0]}"

    def _show_time_relate(self, flow):
        self.extract_time.append(flow.get_time_spent())
        self.model_pipeline_time.append(self.model_pipeline.get_average_time_spent())
        if len(self.extract_time) > 200:
            sns.histplot(self.extract_time, kde=True)
            plt.title("Distribution of feature extraction operation time")
            plt.show()

            sns.histplot(self.model_pipeline_time, kde=True)
            plt.title("Distribution of model pipeline predict operation time")
            plt.show()

    def is_vpn_flow(self, flow_key):
        if self.possible_vpn_flow[flow_key] < self.total_detected_flow_threshold:
            return False

        while self.detection_time_vpn_flows[flow_key][0] - self.detection_time_vpn_flows[flow_key][-1] > self.detection_time_interval:
            self.detection_time_vpn_flows[flow_key].pop(0)

        if len(self.detection_time_vpn_flows[flow_key]) < self.flow_number_for_detect:
            return False

        if self.possible_vpn_flow[flow_key] / self.possible_non_vpn_flow[flow_key] < self.vpn_to_novpn_ratio:
            return False

        return True

    def _clear_console(self):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def _print_statistic(self, flow, packet):
        if self.total_lines > 40:
            self._clear_console()
            self.total_lines = 0
            self.flow_lines = {}

        flow_group = self._extract_flow_key(packet)
        if flow_group not in self.flow_lines:
            self.flow_lines[flow_group] = self.total_lines
            self.total_lines += 8

        stats = (
            f"Flow Group: {flow_group}\n"
            f"  Elapsed time: {packet.time - flow.get_create_timestamp():.2f}s\n"
            f"  Feature extraction time: {flow.get_time_spent():.2f}s\n"
            f"  Avg model predict time: {self.model_pipeline.get_average_time_spent():.2f}s\n"
            f"  VPN flows to node: {self.possible_vpn_flow[self._extract_flow_key(packet)]}\n"
            f"  Non-VPN flows to node: {self.possible_non_vpn_flow[self._extract_flow_key(packet)]}\n"
            f"  Total flow length: {flow.get_total_length()}\n"
        )

        line_number = self.flow_lines[flow_group]
        sys.stdout.write(f"\033[{line_number + 1}H\033[2K")
        sys.stdout.write(stats)
        sys.stdout.flush()


        sys.stdout.write(f"\033[{self.total_lines + 1}H")
        sys.stdout.flush()

    def _update_possible_vpn_flow(self, flow, packet):
        flow_key = self._extract_flow_key(packet)
        self.detection_time_vpn_flows[flow_key].append(time.time())
        if self.is_vpn_flow(flow_key):
            self._print_statistic(flow, packet)

    def _flow_detect(self, flow, packet):
        flow_packet_number = flow.get_packet_number()
        
        if flow_packet_number > self.end_packet_number_threshold or (packet.time - flow.get_create_timestamp()) > 3:
            self.flow_storage.remove_flow_for_packet(flow, packet)
            return

        if (flow_packet_number < self.start_threshold_packet_number) or (flow_packet_number % self.predict_rate != 0):
            return

        feature = flow.get_features()
        if feature.isnull().any().any():
            self.flow_storage.remove_flow_for_packet(flow, packet)
            return

        if self.model_pipeline.filter(feature).any():
            self.flow_storage.remove_flow_for_packet(flow, packet)
            return

        # print((self.model_pipeline.predict(feature) == np.array([1])).all(), self.model_pipeline.predict(feature))
        if self.model_pipeline.predict(feature) == 'vpn' or (self.model_pipeline.predict(feature) == np.array([1])).all():
            self.possible_vpn_flow[self._extract_flow_key(packet)] += 1
            self._update_possible_vpn_flow(flow, packet)
        else:
            self.possible_non_vpn_flow[self._extract_flow_key(packet)] += 1

    def _add_new_flow(self, packet):
        flow = Flow()
        self.flow_storage.add_new_flow(flow, packet)
        flow.add_new_packet(packet)

    def _packet_processing(self, packet):
        if self.flow_storage.filter(packet):
            return

        flows = self.flow_storage.get_flows_for_packet(packet)
        if not flows:
            self._add_new_flow(packet)
            return

        for flow in flows:
            flow.add_new_packet(packet)
            self._flow_detect(flow, packet)

