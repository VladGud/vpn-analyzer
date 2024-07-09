from scapy.all import *
from .concurrent_queue import ConcurrentQueue

class Sniffer:
    def __init__(self, consumer, threads_count=1):
        self._input_queue = ConcurrentQueue()
        self._consumer = consumer
        self._consumer.set_input(self._input_queue)

    def sniff_packets(self):
        sniff(prn=self.col.append)

    def run(self):
        self.consumer.start()
        self.sniff_packets()
        self.consumer.join()