from scapy.all import *
import statistics
import pandas as pd


class FeatureInterface:
    def extract_feature(self, packet):
        pass

    def get_feature(self):
        pass


class InterpacketIntervalFeature(FeatureInterface):
    MAX_INTERPACKET_INTERVAL = "max_interpacket_interval"
    MIN_INTERPACKET_INTERVAL = "min_interpacket_interval"
    AVG_INTERPACKET_INTERVAL = "avg_interpacket_interval"
    SUM_INTERPACKET_INTERVAL = "sum_interpacket_interval"

    def __init__(self):
        self.packet_times = []

    def extract_feature(self, packet):
        self.packet_times.append(packet.time)

    def get_feature(self):
        interpacket_intervals = [b - a for a, b in zip(self.packet_times, self.packet_times[1:])]

        data = {}

        if len(self.packet_times) < 2:
            data[self.MAX_INTERPACKET_INTERVAL] = [None]
            data[self.MIN_INTERPACKET_INTERVAL] = [None]
            data[self.AVG_INTERPACKET_INTERVAL] = [None]
            data[self.SUM_INTERPACKET_INTERVAL] = [None]
        else:
            data[self.MAX_INTERPACKET_INTERVAL] = [max(interpacket_intervals)]
            data[self.MIN_INTERPACKET_INTERVAL] = [min(interpacket_intervals)]
            data[self.AVG_INTERPACKET_INTERVAL] = [statistics.mean(interpacket_intervals)]
            data[self.SUM_INTERPACKET_INTERVAL] = [self.packet_times[-1] - self.packet_times[0]]

        return pd.DataFrame(data)


class PacketLengthFeature(FeatureInterface):
    MAX_PACKET_LENGTH = "max_packet_length"
    MIN_PACKET_LENGTH = "min_packet_length"
    AVG_PACKET_LENGTH = "avg_packet_length"
    SUM_PACKET_LENGTH = "sum_packet_length"
    MODE_PACKET_LENGTH = "mode_packet_length"

    def __init__(self):
        self.packet_lengths = []

    def extract_feature(self, packet):
        self.packet_lengths.append(len(packet))

    def get_feature(self):
        data = {}

        if len(self.packet_lengths) < 1:
            data[self.MAX_PACKET_LENGTH] = [None] # TODO: Add list?
            data[self.MIN_PACKET_LENGTH] = [None]
            data[self.AVG_PACKET_LENGTH] = [None]
            data[self.SUM_PACKET_LENGTH] = [None]
            data[self.MODE_PACKET_LENGTH] = [None]
        else:
            data[self.MAX_PACKET_LENGTH] = [max(self.packet_lengths)]
            data[self.MIN_PACKET_LENGTH] = [min(self.packet_lengths)]
            data[self.AVG_PACKET_LENGTH] = [statistics.mean(self.packet_lengths)]
            data[self.SUM_PACKET_LENGTH] = [sum(self.packet_lengths)]
            data[self.MODE_PACKET_LENGTH] = [statistics.mode(self.packet_lengths)]

        return pd.DataFrame(data)


class FeatureStorage:
    def __init__(self):
        self.features = [InterpacketIntervalFeature(), PacketLengthFeature()]

    def extract_features(self, packet):
        for feature in self.features:
            feature.extract_feature(packet)

    def get_features(self):
        feature_dfs = []
        for feature in self.features:
            feature_dfs.append(feature.get_feature())

        return pd.concat(feature_dfs, axis=1)