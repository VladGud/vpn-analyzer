from pathlib import Path

from .test_extract_feature_base import TestExtractFeatureFromFlowBase


class TestExtractTimeSeriesFeatureFromFlow(TestExtractFeatureFromFlowBase):
    @classmethod
    def setUpClass(cls):
        cls.get_feature_lambda = lambda flow: flow.get_time_series_features()
        super(TestExtractTimeSeriesFeatureFromFlow, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.source_file = Path("_".join(["time-series", str(cls.source_file.stem)]))
        super(TestExtractTimeSeriesFeatureFromFlow, cls).tearDownClass()

    def test_flow_storage(self):
        self._test_flow_storage()