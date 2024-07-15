import pandas as pd
from scapy.all import *

from ..utils.fsbst import FixSizeBST

class FlowStorage:
    def __init__(self, fix_size=10000):
        self._storage = FixSizeBST(fix_size)

    def extract_flow_key_for_packet(self, pkt):
        src_ip = pkt['IP'].src
        dst_ip = pkt['IP'].dst

        if pkt.haslayer('TCP'):
            src_port = pkt['TCP'].sport
            dst_port = pkt['TCP'].dport
        elif pkt.haslayer('UDP'):
            src_port = pkt['UDP'].sport
            dst_port = pkt['UDP'].dport

        # Create one flow_key for src -> dst and dst -> src
        if int(pkt['IP'].src.split(".")[0]) > int(pkt['IP'].dst.split(".")[0]):
            return f"{src_ip}:{src_port}<-->{dst_ip}:{dst_port}"
        else:
            return f"{dst_ip}:{dst_port}<-->{src_ip}:{src_port}"

    def filter(self, packet):
        if (not packet.haslayer("IP")) or ((not packet.haslayer('TCP') and (not packet.haslayer('UDP')))):
            return True

        if packet.haslayer('TCP'):
            src_port = packet['TCP'].sport
            dst_port = packet['TCP'].dport
        elif packet.haslayer('UDP'):
            src_port = packet['UDP'].sport
            dst_port = packet['UDP'].dport 

        # Work only with TLS
        if src_port != 443 and dst_port != 443:
            return True

        return False

    def get_flows_for_packet(self, pkt):
        flow_key = self.extract_flow_key_for_packet(pkt)
        return self._storage.get_value(flow_key)

    def add_new_flow(self, flow, pkt):
        flow_key = self.extract_flow_key_for_packet(pkt)

        if not self._storage.get_value(flow_key):
            self._storage.add_new_node(flow_key, [])

        self._storage.get_value(flow_key).append(flow)

    def _remove_from_flows(self, flow_key, flow):
        flows = self._storage.get_value(flow_key)
        if not flows:
            print("Warning: Flow cannot be deleted because FlowStorage did not contain flows for packet")
            return
        flows.remove(flow)

    def _clear_flow_key(self, flow_key):
        if self._storage.get_value(flow_key) is not None and not self._storage.get_value(flow_key):
            self._storage.delete(flow_key)


    def remove_flow_for_packet(self, flow, pkt):
        flow_key = self.extract_flow_key_for_packet(pkt)
        self._remove_from_flows(flow_key, flow)
        self._clear_flow_key(flow_key)

    def get_total_size(self):
        return len(self._storage.items())

    def items(self):
        return self._storage.items()
