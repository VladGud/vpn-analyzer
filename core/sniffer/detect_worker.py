import time
import threading
from ..utils.concurrent_queue import ConcurrentQueue
from ..flow import FlowStorage, Flow


class DetectWorker(threading.Thread):
    def __init__(self, model_pipeline, threshold_packet_number=10, predict_rate=5, input_queue=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.input_queue = input_queue
        self.flow_storage = FlowStorage()
        self.threshold_packet_number = threshold_packet_number

    def run(self):
        while True:
            if not self.input_queue.empty():
                packet = self.input_queue.pop()
                self._packet_processing(packet)
            else:
                time.sleep(0.1)

    def set_input(self, input_queue):
        self.input_queue = input_queue

    def _flow_detect(self, flow, flow_key):
        if (flow.get_packet_number() % predict_rate != 0) or (flow.get_packet_number() < self.threshold_packet_number):
            return

        feature = flow.get_features()
        if feature.isnull().any().any():
            return

        feature = feature.drop([
                'Description', 
                'max_interpacket_interval',
                'min_interpacket_interval',
                'max_packet_length',
                'min_packet_length',
                'mode_packet_length'
            ], axis=1)

        if self.model_pipeline.predict(feature) == 'vpn':
            print(f"Found vpn flow {flow_key}")

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
            self._flow_detect(flow, f"{packet['IP'].src} -- {packet['IP'].dst}")

