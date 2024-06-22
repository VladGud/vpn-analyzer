import unittest

import pandas as pd
from pathlib import Path
from tqdm import tqdm
from scapy.all import PcapReader

from core.flow import FlowStorage, Flow, BloomFilter


class TestFlowStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_file = Path("vpn-pcap/xray-order.pcap")
        cls.flow_storage = FlowStorage()
        cls.pcap_file = PcapReader(str(cls.source_file))

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

    def test_flow_storage(self):
        for packet in tqdm(self.pcap_file):
            if self._non_filterable_packet(packet):
                continue

            flows = self.flow_storage.get_flows_for_packet(packet)
            if not flows:
                flows = self._test_add_new_flow(packet)

            for flow in flows:
                flow.add_new_packet(packet)


if __name__ == '__main__':
    unittest.main()