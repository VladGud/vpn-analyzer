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

    def run(self):
        while True:
            if not self.input_queue.empty():
                packet = self.input_queue.pop()
                self._packet_processing(packet)
            else:
                time.sleep(0.1)

    def set_input(self, input_queue):
        self.input_queue = input_queue

    def update_possible_vpn_flow(self, packet):
        flow_key = ''.join(sorted(f"{packet['IP'].src} -- {packet['IP'].dst}"))
        self.possible_vpn_flow[flow_key] += 1
        if self.possible_vpn_flow[flow_key] >= self.detect_threshold:
            print()
            print(f"Found vpn flow: {self.flow_storage.extract_flow_key_for_packet(packet)}.")
            print(f"The current number of flow being processed: {self.flow_storage.get_total_size()}")
            print(f"The total number of VPN connections to this node: {self.possible_vpn_flow[flow_key]}")
            print()

    def _flow_detect(self, flow, packet):
        flow_packet_number = flow.get_packet_number()
        if (flow_packet_number % self.predict_rate != 0) or (flow_packet_number < self.start_threshold_packet_number):
            return

        if flow_packet_number > self.end_packet_number_threshold:
            self.flow_storage.remove_flow_for_packet(flow, packet)

        feature = flow.get_features()
        if feature.isnull().any().any():
            return

        feature = feature.drop([
                'Description',
            ], axis=1)

        if self.model_pipeline.predict(feature) == 'vpn':
            self.update_possible_vpn_flow(packet)
            self.flow_storage.remove_flow_for_packet(flow, packet)

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

