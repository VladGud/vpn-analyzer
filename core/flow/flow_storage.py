import pandas as pd
from scapy.all import *

from ..utils.fsbst import FixSizeBST

class FlowStorage:
    def __init__(self, fix_size=10):
        self._storage = FixSizeBST(fix_size)

    def _extract_packet_info(self, pkt):
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
        return (not packet.haslayer("IP")) or ((not packet.haslayer('TCP') and (not packet.haslayer('UDP'))))

    def get_flows_for_packet(self, pkt):
        flow_key = self._extract_packet_info(pkt)
        return self._storage.get_value(flow_key)

    def add_new_flow(self, flow, pkt):
        flow_key = self._extract_packet_info(pkt)

        if not self._storage.get_value(flow_key):
            self._storage.add_new_node(flow_key, [])

        self._storage.get_value(flow_key).append(flow)


    def get_features_for_all_flows(self):
        result_features_list = []

        for flow_key, flows in self._storage.items():
            for flow in flows:
                df = flow.get_features()
                df.insert(0, "Flow", flow_key)
                result_features_list.append(df)

        result_df = pd.concat(result_features_list, ignore_index=True, sort=False)
        return result_df
