from scapy.all import *
from ..utils.concurrent_queue import ConcurrentQueue

class Sniffer:
    def __init__(self, consumer, iface):
        self._input_queue = ConcurrentQueue()
        self._consumer = consumer
        self._iface = iface
        self._consumer.set_input(self._input_queue)

    def sniff_packets(self):
        sniff(iface=self._iface, prn=self._input_queue.append)

    def run(self):
        self._consumer.start()
        self.sniff_packets()
        self._consumer.join()