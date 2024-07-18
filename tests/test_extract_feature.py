from pathlib import Path

from .test_extract_feature_base import TestExtractFeatureFromFlowBase


class TestExtractFeatureFromFlow(TestExtractFeatureFromFlowBase):
    @classmethod
    def setUpClass(cls):
        cls.get_feature_lambda = lambda flow: flow.get_features()
        super(TestExtractFeatureFromFlow, cls).setUpClass()



    def test_flow_storage(self):
        self._test_flow_storage()