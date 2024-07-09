import hashlib
import pandas as pd
from scapy.all import *

from .feature_storage import FeatureStorage


class Flow:
    def __init__(self, filter_lambda=lambda pkt: True, desc="All packet"):
        self.compiled_filter = filter_lambda
        self.feature_extractor = FeatureStorage()
        self.desc = desc
        self.packet_number = 0

    def filter(self, packet):
        return self.compiled_filter(packet)

    def add_new_packet(self, packet):
        self.feature_extractor.extract_features(packet)
        self.packet_number += 1

    def get_features(self):
        df = self.feature_extractor.get_features()
        df.insert(0, "Description", self.desc)
        return df

    def get_packet_number(self):
        return self.packet_number

def sha256_hash(data):
    return hashlib.sha256(data.encode())


class BloomFilter:
    threshold = 2
    size = 100

    @staticmethod
    def extract_raw_ip_bytes(pkt):
        if pkt.haslayer('IP'):
            raw_bytes = bytes(pkt['IP'])
            return raw_bytes

    @classmethod
    def filter(cls, pkt):
        pkt_bytes = FlowStorage.extract_raw_ip_bytes(pkt)
        if pkt_bytes is None:
            return None

        counter = [0]*(cls.size//2*cls.threshold) # magic
        for i in range(cls.size):
            calculated_index = sha256_hash(f"{pkt_bytes}{i}")%cls.size
            if counter[calculated_index] < cls.threshold:
                counter[calculated_index] += 1

        if min(counter) == cls.threshold:
            return sha256_hash(pkt_bytes)


class FlowStorage:
    def __init__(self):
        self.storage = {}

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
        if flow_key not in self.storage.keys():
            return None

        return self.storage[flow_key]

    def add_new_flow(self, flow, pkt):
        flow_key = self._extract_packet_info(pkt)
        if flow_key is None:
            return False

        if flow_key not in self.storage.keys():
        	self.storage[flow_key] = []

        self.storage[flow_key].append(flow)

        return True

    def get_features_for_all_flows(self):
        result_features_list = []

        for flow_key, flows in self.storage.items():
            for flow in flows:
                df = flow.get_features()
                df.insert(0, "Flow", flow_key)
                result_features_list.append(df)

        result_df = pd.concat(result_features_list, ignore_index=True, sort=False)
        return result_df
