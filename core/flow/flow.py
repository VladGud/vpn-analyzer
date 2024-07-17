from datetime import datetime
from ..feature.feature_storage import FeatureStorage

class Flow:
    def __init__(self, filter_lambda=lambda pkt: True):
        self.compiled_filter = filter_lambda
        self.feature_extractor = FeatureStorage()
        self.packet_number = 0
        self.total_length = 0
        self.create_timestamp = None

    def get_time(self):
        return self.create_timestamp

    def get_total_length(self):
        return self.total_length

    def filter(self, packet):
        return self.compiled_filter(packet)

    def _update_flow_info(self, packet):
        if not self.create_timestamp:
            self.create_timestamp = packet.time
        self.total_length += len(packet)
        self.packet_number += 1

    def add_new_packet(self, packet):
        self.feature_extractor.extract_features(packet)
        self._update_flow_info(packet)

    def get_features(self):
        df = self.feature_extractor.get_features()
        return df

    def get_time_series_features(self):
        df = self.feature_extractor.get_time_series_features()
        return df

    def get_packet_number(self):
        return self.packet_number
