import time
import threading
from collections import defaultdict
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
            detect_threshold=3,
            input_queue=None
    ):
        threading.Thread.__init__(self)
        self.daemon = True        

        self.input_queue = input_queue

        self.flow_storage = FlowStorage()        
        self.model_pipeline = model_pipeline

        self.predict_rate = predict_rate
        self.start_threshold_packet_number = start_packet_number_threshold
        self.end_packet_number_threshold = end_packet_number_threshold

        self.detect_threshold = detect_threshold
        self.possible_vpn_flow = defaultdict(int)
        self.possible_non_vpn_flow = defaultdict(int)

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

    def print_statistic(self, flow, packet):
        print()
        print(f"Last found vpn flow: {self.flow_storage.extract_flow_key_for_packet(packet)}.")
        print(f"Time spent on detecting the latest VPN flow: {packet.time- flow.get_time()}")
        print(f"The total number of VPN flow to this node: {self.possible_vpn_flow[self._extract_flow_key(packet)]}")
        # print(f"The total number of Non-VPN flow to this node: {self.possible_non_vpn_flow[self._extract_flow_key(packet)]}")
        print(f"Total length of flow: {flow.get_total_length()}")
        print(f"The current number of flow being processed: {self.flow_storage.get_total_size()}")
        print()

    def _update_possible_vpn_flow(self, flow, packet):
        flow_key = self._extract_flow_key(packet)
        self.possible_vpn_flow[flow_key] += 1
        if self.possible_vpn_flow[flow_key] >= self.detect_threshold:
            self.print_statistic(flow, packet)

    def _flow_detect(self, flow, packet):
        flow_packet_number = flow.get_packet_number()
        if (flow_packet_number % self.predict_rate != 0) or (flow_packet_number < self.start_threshold_packet_number):
            return

        if flow_packet_number > self.end_packet_number_threshold:
            self.flow_storage.remove_flow_for_packet(flow, packet)

        feature = flow.get_features()
        if feature.isnull().any().any():
            return

        if self.model_pipeline.predict(feature) == 'vpn':
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

