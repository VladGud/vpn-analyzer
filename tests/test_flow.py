import unittest
import copy

import numpy
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from scapy.all import PcapReader

from core.model_pipeline import ModelPipeline
from core.flow import FlowStorage, Flow, BloomFilter


class TestFlowStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_file = Path("vpn-pcap/v2rayng-vless-quic-order.pcap")
        cls.flow_storage = FlowStorage()
        cls.pcap_file = PcapReader(str(cls.source_file))

        cls.model_pipeline = ModelPipeline.load_models(
            'models/0_9495/power_transformer.pkl',
            'models/0_9495/ica.pkl',
            'models/0_9495/clf.pkl'
        )

        cls.expected_label = "vpn"
        cls.result_false_predict = {}
        cls.result_true_predict = {}

    @classmethod
    def create_label(cls, df):
        normal_df = df[~df['Flow'].str.contains('81.200.154.28')].copy() 
        normal_df['label'] = 'normal'
        
        vpn_df = df[df['Flow'].str.contains('81.200.154.28')].copy()
        vpn_df['label'] = 'vpn'

        df = pd.concat([normal_df, vpn_df], ignore_index=True)

        return df

    @classmethod
    def tearDownClass(cls):
        cls.pcap_file.close()

        result_df = cls.flow_storage.get_features_for_all_flows()
        result_df = cls.create_label(result_df)

        print(result_df)

        result_df.to_csv(str(cls.source_file.with_suffix('.csv')))

    def _test_add_new_flow(self, packet):
        flow = Flow()

        self.assertTrue(self.flow_storage.add_new_flow(flow, packet), "Flow didn't store in storage")
        self.assertTrue(flow in self.flow_storage.get_flows_for_packet(packet), "Flow didn't find in storage")

        return [flow]

    def _non_filterable_packet(self, packet):
        return (not packet.haslayer("IP")) or ((not packet.haslayer('TCP') and (not packet.haslayer('UDP'))))

    # def _predict(self, flow):
    #     # flow = copy.deepcopy(flow)
    #     packet_number = flow.get_packet_number()
    #     if packet_number % 5 != 0:
    #         return

    #     feature = flow.get_features()
    #     if feature.isnull().any().any():
    #         return

    #     feature = feature.drop(['Description', 'max_interpacket_interval', 'min_interpacket_interval', 'max_packet_length', 'min_packet_length', 'mode_packet_length'], axis=1)

    #     if self.model_pipeline.predict(feature) == self.expected_label:
    #         if packet_number in self.result_true_predict.keys():
    #             self.result_true_predict[packet_number] += 1
    #         else:
    #             self.result_true_predict[packet_number] = 1
    #     else:
    #         if packet_number in self.result_false_predict.keys():
    #             self.result_false_predict[packet_number] += 1
    #         else:
    #             self.result_false_predict[packet_number] = 1
            

    def test_flow_storage(self):
        for packet in tqdm(self.pcap_file):
            if self.flow_storage.filter(packet):
                continue

            flows = self.flow_storage.get_flows_for_packet(packet)
            if not flows:
                flows = self._test_add_new_flow(packet)

            for flow in flows:
                flow.add_new_packet(packet)
                # self._predict(flow)


if __name__ == '__main__':
    unittest.main()