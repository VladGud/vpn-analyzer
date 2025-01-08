import sys
import unittest
import copy

import numpy
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from scapy.all import PcapReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.flow.flow import Flow
from core.flow.flow_storage import FlowStorage


class TestExtractFeatureFromFlowBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_file = Path("normal-traffic-mac-v2.pcap")
        cls.flow_storage = FlowStorage()
        cls.pcap_file = PcapReader(str(cls.source_file))
        cls.max_packet_number_on_flow = 30
        cls.min_packet_number_on_flow = 27

        cls.expected_label = "vpn"
        cls.result_false_predict = {}
        cls.result_true_predict = {}

    @classmethod
    def create_label(cls, df):
        normal_df = df[~df['Flow'].str.contains('147.45.49.23')].copy() 
        normal_df['label'] = 'normal'
        
        vpn_df = df[df['Flow'].str.contains('147.45.49.23')].copy()
        vpn_df['label'] = 'vpn'

        df = pd.concat([normal_df, vpn_df], ignore_index=True)

        return df

    @classmethod
    def create_result_feature_df(cls):
        result_features_list = []
        counter = 0
        for flow_key, flows in cls.flow_storage.items():
            for flow in flows:
                if flow.get_packet_number() < cls.min_packet_number_on_flow:
                    continue
                df = cls.get_feature_lambda(flow) # Implement it in Derived class
                df.insert(0, "Flow", flow_key)
                counter += 1
                result_features_list.append(df)

        return pd.concat(result_features_list, ignore_index=True, sort=False)

    @classmethod
    def tearDownClass(cls):
        cls.pcap_file.close()

        result_df = cls.create_result_feature_df()
        result_df = cls.create_label(result_df)

        print(result_df)
        result_df.to_csv(str(cls.source_file.with_suffix('.csv')))

    def _test_add_new_flow(self, packet):
        flow = Flow()

        self.flow_storage.add_new_flow(flow, packet)
        self.assertTrue(flow in self.flow_storage.get_flows_for_packet(packet), "Added flow didn't find in storage")

        return [flow]

    def _test_flow_storage(self):
        for packet in tqdm(self.pcap_file):
            if self.flow_storage.filter(packet):
                continue

            flows = self.flow_storage.get_flows_for_packet(packet)
            if not flows:
                flows = self._test_add_new_flow(packet)
            
            for flow in flows:
                if flow.get_packet_number() <= self.max_packet_number_on_flow:
                    flow.add_new_packet(packet)

