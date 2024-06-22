import abc
import numpy as np
import pandas as pd
from scapy.all import *

from .feature import FeatureInterface
from .utils import filter_outliners


class FunctionInterface(abc.ABC):
    @abc.abstractmethod
    def name(self):
        pass

    @abc.abstractmethod
    def __call__(self, array):
        pass

class MeanFunction(FunctionInterface):
    def name(self):
        return "mean_func"

    def __call__(self, array):
        return np.mean(array)

class SumFunction(FunctionInterface):
    def name(self):
        return "sum_func"

    def __call__(self, array):
        return np.sum(array)


class InterpacketIntervalFunctionPerTimeFeature(FeatureInterface):
    def __init__(self, func, max_interpacket_interval_time=0.2):
        self.current_interval_time = None
        self.interpacket_intervals = {}
        self.max_interpacket_interval_time = max_interpacket_interval_time
        self.func = func

        self.MAX_FEATURE = f"max_feature_{func.name()}_per{max_interpacket_interval_time}"
        self.MIN_FEATURE = f"min_feature_{func.name()}_per{max_interpacket_interval_time}"
        self.STD_FEATURE = f"std_feature_{func.name()}_per{max_interpacket_interval_time}"
        self.MEAN_FEATURE = f"mean_feature_{func.name()}_per{max_interpacket_interval_time}"

    def extract_feature(self, packet):
        new_packet_time = float(packet.time)

        if not self.current_interval_time:
            self.current_interval_time = new_packet_time
            self.interpacket_intervals[new_packet_time] = []
            return

        new_interpacket_interval = new_packet_time - self.current_interval_time
        if new_interpacket_interval < self.max_interpacket_interval_time:
            self.interpacket_intervals[self.current_interval_time].append(new_interpacket_interval)
        else:
            self.current_interval_time = new_packet_time
            self.interpacket_intervals[new_packet_time] = []

    def _data_filtering(self):
        # clear_data = []
        for interpacket_interval in self.interpacket_intervals.values():
            if interpacket_interval:
                interpacket_interval = list(filter_outliners(interpacket_interval))
                # clear_data.append(interpacket_interval)
                yield interpacket_interval

        # return clear_data
        
    def _create_result_feature_array(self):
        data_array = []
        for data in self._data_filtering():
            if data:
                data_array.append(self.func(data))

        return data_array

    def get_feature(self):
        result_feature_array = self._create_result_feature_array()

        data = {}
        if result_feature_array:
            data[self.MAX_FEATURE]  = [np.max(result_feature_array)]
            data[self.MIN_FEATURE]  = [np.min(result_feature_array)]
            data[self.STD_FEATURE]  = [np.std(result_feature_array)]
            data[self.MEAN_FEATURE] = [np.mean(result_feature_array)]
        else:
            data[self.MAX_FEATURE] = [np.NaN]
            data[self.MIN_FEATURE] = [None]
            data[self.STD_FEATURE] = [None]
            data[self.MEAN_FEATURE] = [None]

        return pd.DataFrame(data)
