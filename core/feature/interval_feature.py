import abc
import numpy as np
import pandas as pd
from scapy.all import *

from .feature import FeatureInterface
from ..utils.filter_outliners import filter_outliners


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

        self.MAX_FEATURE = f"max_feature_{func.name()}_interpacket_interval_per_{max_interpacket_interval_time}"
        self.MIN_FEATURE = f"min_feature_{func.name()}_interpacket_interval_per_{max_interpacket_interval_time}"
        self.STD_FEATURE = f"std_feature_{func.name()}_interpacket_interval_per_{max_interpacket_interval_time}"
        self.MEAN_FEATURE = f"mean_feature_{func.name()}_interpacket_interval_per_{max_interpacket_interval_time}"

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
        for interpacket_interval in self.interpacket_intervals.values():
            if len(interpacket_interval) > 1:
                interpacket_interval = list(filter_outliners(interpacket_interval))
                yield interpacket_interval
        
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
            data[self.MAX_FEATURE] = [np.nan]
            data[self.MIN_FEATURE] = [np.nan]
            data[self.STD_FEATURE] = [np.nan]
            data[self.MEAN_FEATURE] = [np.nan]

        return pd.DataFrame(data)

class PacketLengthFunctionPerTimeFeature(FeatureInterface):
    def __init__(self, func, max_interpacket_interval_time=0.2):
        self.current_interval_time = None
        self.packet_length_flows = {}
        self.max_interpacket_interval_time = max_interpacket_interval_time
        self.func = func

        self.MAX_FEATURE = f"max_feature_{func.name()}_packet_length_per_{max_interpacket_interval_time}"
        self.MIN_FEATURE = f"min_feature_{func.name()}_packet_length_per_{max_interpacket_interval_time}"
        self.STD_FEATURE = f"std_feature_{func.name()}_packet_length_per_{max_interpacket_interval_time}"
        self.MEAN_FEATURE = f"mean_feature_{func.name()}_packet_length_per_{max_interpacket_interval_time}"

    def extract_feature(self, packet):
        new_packet_time = float(packet.time)

        if not self.current_interval_time:
            self.current_interval_time = new_packet_time
            self.packet_length_flows[new_packet_time] = [len(packet)]
            return

        new_interpacket_interval = new_packet_time - self.current_interval_time
        if new_interpacket_interval < self.max_interpacket_interval_time:
            self.packet_length_flows[self.current_interval_time].append(len(packet))
        else:
            self.current_interval_time = new_packet_time
            self.packet_length_flows[new_packet_time] = [len(packet)]

    def _data_filtering(self):
        for packet_length_flow in self.packet_length_flows.values():
            if len(packet_length_flow) > 2:
                packet_length_flow = list(filter_outliners(packet_length_flow))
                yield packet_length_flow
        
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
            data[self.MAX_FEATURE] = [np.nan]
            data[self.MIN_FEATURE] = [np.nan]
            data[self.STD_FEATURE] = [np.nan]
            data[self.MEAN_FEATURE] = [np.nan]

        return pd.DataFrame(data)

class PacketNumberPerTimeFeature(FeatureInterface):
    def __init__(self, max_interpacket_interval_time=0.2):
        self.current_interval_time = None
        self.packet_number_per_time = {}
        self.max_interpacket_interval_time = max_interpacket_interval_time

        self.MAX_FEATURE = f"max_feature_packet_number_per_{max_interpacket_interval_time}"
        self.MIN_FEATURE = f"min_feature_packet_number_per_{max_interpacket_interval_time}"
        self.STD_FEATURE = f"std_feature_packet_number_per_{max_interpacket_interval_time}"
        self.MEAN_FEATURE = f"mean_feature_packet_number_per_{max_interpacket_interval_time}"

    def extract_feature(self, packet):
        new_packet_time = float(packet.time)

        if not self.current_interval_time:
            self.current_interval_time = new_packet_time
            self.packet_number_per_time[new_packet_time] = 1
            return

        new_interpacket_interval = new_packet_time - self.current_interval_time
        if new_interpacket_interval < self.max_interpacket_interval_time:
            self.packet_number_per_time[self.current_interval_time] += 1
        else:
            self.current_interval_time = new_packet_time
            self.packet_number_per_time[new_packet_time] = 1

    def get_feature(self):
        result_feature_array = list(self.packet_number_per_time.values())

        data = {}
        if result_feature_array:
            data[self.MAX_FEATURE]  = [np.max(result_feature_array)]
            data[self.MIN_FEATURE]  = [np.min(result_feature_array)]
            data[self.STD_FEATURE]  = [np.std(result_feature_array)]
            data[self.MEAN_FEATURE] = [np.mean(result_feature_array)]
        else:
            data[self.MAX_FEATURE] = [np.nan]
            data[self.MIN_FEATURE] = [np.nan]
            data[self.STD_FEATURE] = [np.nan]
            data[self.MEAN_FEATURE] = [np.nan]

        return pd.DataFrame(data)
