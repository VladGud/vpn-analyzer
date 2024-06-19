from scapy.all import *
from worker import Worker
from utils import ConcurrentQueue

class Sniffer:
    def __init__(self, output_col: ConcurrentQueue, threads_count=1):
        self.col = ConcurrentQueue()
        self.output_col = output_col
        self.consumers = [Worker(self.col) for _ in range(threads_count)]

    def sniff_packets(self):
        sniff(prn=self.col.append)

    def run(self):
        for consumer in self.consumers:
            consumer.start()
            self.sniff_packets()

        for consumer in self.consumers:
            consumer.join()

if __name__ == "__main__":
    output_col = ConcurrentQueue()
    sniff = Sniffer(output_col=output_col, threads_count=1)
    thread_sniff = threading.Thread(target=sniff.run, args=())
    thread_sniff.start()
