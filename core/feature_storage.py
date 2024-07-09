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
            PacketLengthFunctionPerTimeFeature(func=MeanFunction()),
            PacketLengthFunctionPerTimeFeature(func=SumFunction()),
            PacketNumberPerTimeFeature(),
        ]

    def extract_features(self, packet):
        for feature in self.features:
            feature.extract_feature(packet)

    def get_features(self):
        feature_dfs = []
        for feature in self.features:
            feature_dfs.append(feature.get_feature())

        return pd.concat(feature_dfs, axis=1)