from utils import *
from flow import FlowStorage, Flow
import threading
import time

class Worker(threading.Thread):
    def __init__(self, input_collection: ConcurrentQueue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.input_collection = input_collection
        self.flow_storage = FlowStorage()

    def run(self):
        while True:
            if not self.input_collection.empty():
                packet = self.input_collection.pop()
                self.packet_processing(packet)
                print(self.flow_storage.storage)
            else:
                time.sleep(0.1)

    def packet_processing(self, packet):
        if self.flow_storage.filter(packet):
            return

        flows = self.flow_storage.get_flows_for_packet(packet)
        if not flows:
            flow = Flow()
            self.flow_storage.add_new_flow(flow, packet)
            flows = self.flow_storage.get_flows_for_packet(packet)

        for flow in flows:
            flow.add_new_packet(packet)