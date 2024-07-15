import pandas as pd

from .feature import InterpacketIntervalFeature, PacketLengthFeature
from .interval_feature import (
    InterpacketIntervalFunctionPerTimeFeature,
    PacketLengthFunctionPerTimeFeature,
    PacketNumberPerTimeFeature,
    MeanFunction,
    SumFunction
)

class FeatureStorage:
    def __init__(self):
        self.features = [
            InterpacketIntervalFeature(),
            PacketLengthFeature(),
            InterpacketIntervalFunctionPerTimeFeature(func=MeanFunction()),
            InterpacketIntervalFunctionPerTimeFeature(func=SumFunction()),
            InterpacketIntervalFunctionPerTimeFeature(func=MeanFunction(), max_interpacket_interval_time=0.05),
            InterpacketIntervalFunctionPerTimeFeature(func=SumFunction(), max_interpacket_interval_time=0.05),
            PacketLengthFunctionPerTimeFeature(func=MeanFunction()),
            PacketLengthFunctionPerTimeFeature(func=SumFunction()),
            PacketLengthFunctionPerTimeFeature(func=MeanFunction(), max_interpacket_interval_time=0.05),
            PacketLengthFunctionPerTimeFeature(func=SumFunction(), max_interpacket_interval_time=0.05),
            PacketNumberPerTimeFeature(),
        ]

    def extract_features(self, packet):
        for feature in self.features:
            feature.extract_feature(packet)

    def _concatenate_features_dfs(self, get_feature_fn):
        feature_dfs = []
        for feature in self.features:
            feature_dfs.append(get_feature_fn(feature))

        return pd.concat(feature_dfs, axis=1)

    def get_features(self):
        return self._concatenate_features_dfs(get_feature_fn=lambda feature: feature.get_feature())

    def get_time_series_features(self):
        return self._concatenate_features_dfs(get_feature_fn=lambda feature: feature.get_time_series_feature())
