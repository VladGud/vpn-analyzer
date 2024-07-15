from ..feature.feature_storage import FeatureStorage


class Flow:
    def __init__(self, filter_lambda=lambda pkt: True):
        self.compiled_filter = filter_lambda
        self.feature_extractor = FeatureStorage()
        self.packet_number = 0

    def filter(self, packet):
        return self.compiled_filter(packet)

    def add_new_packet(self, packet):
        self.feature_extractor.extract_features(packet)
        self.packet_number += 1

    def get_features(self):
        df = self.feature_extractor.get_features()
        return df

    def get_time_series_features(self):
        df = self.feature_extractor.get_time_series_features()
        return df

    def get_packet_number(self):
        return self.packet_number
