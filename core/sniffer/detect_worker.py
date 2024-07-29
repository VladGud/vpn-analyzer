import time
import threading
from collections import defaultdict

import seaborn as sns
import matplotlib.pyplot as plt

from ..utils.concurrent_queue import ConcurrentQueue
from ..flow.flow import Flow
from ..flow.flow_storage import FlowStorage


class DetectWorker(threading.Thread):
    def __init__(
            self,
            model_pipeline,
            start_packet_number_threshold=40,
            end_packet_number_threshold=60,
            predict_rate=5,
            detect_threshold=10,
            flow_storage_size=1000,
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

        self.detect_threshold = detect_threshold
        self.possible_vpn_flow = defaultdict(int)
        self.possible_non_vpn_flow = defaultdict(int)

        self.extract_time = []
        self.model_pipeline_time = []

    def run(self):
        while True:
            if not self.input_queue.empty():
                packet = self.input_queue.pop()
                self._packet_processing(packet)
            else:
                time.sleep(0.1)

    def set_input(self, input_queue):
        self.input_queue = input_queue

    def _extract_flow_key(self, packet):
        return ''.join(sorted(f"{packet['IP'].src} -- {packet['IP'].dst}"))

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

    def _print_statistic(self, flow, packet):
        print()
        print(f"Last found vpn flow: {self.flow_storage.extract_flow_key_for_packet(packet)}.")
        print(f"The time elapsed since the beginning of the flow creation: {packet.time- flow.get_create_timestamp()}")
        print(f"Time spent on feature extraction: {flow.get_time_spent()}")
        print(f"Average time spent on model pipeline predict: {self.model_pipeline.get_average_time_spent()}")
        print(f"The total number of VPN flow to this node: {self.possible_vpn_flow[self._extract_flow_key(packet)]}")
        print(f"The total number of Non-VPN flow to this node: {self.possible_non_vpn_flow[self._extract_flow_key(packet)]}")
        print(f"Total length of flow: {flow.get_total_length()}")
        print(f"The current number of flow being processed: {self.flow_storage.get_total_size()}")
        print()
        # self._show_time_relate(flow)

    def _update_possible_vpn_flow(self, flow, packet):
        flow_key = self._extract_flow_key(packet)
        if self.possible_vpn_flow[flow_key] - self.possible_non_vpn_flow[flow_key] >= self.detect_threshold:
            self._print_statistic(flow, packet)

    def _flow_detect(self, flow, packet):
        flow_packet_number = flow.get_packet_number()
        if (flow_packet_number % self.predict_rate != 0) or (flow_packet_number <= self.start_threshold_packet_number):
            return

        if flow_packet_number > self.end_packet_number_threshold:
            self.flow_storage.remove_flow_for_packet(flow, packet)

        feature = flow.get_features()
        if feature.isnull().any().any():
            return

        if self.model_pipeline.predict(feature) == 'vpn':
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

