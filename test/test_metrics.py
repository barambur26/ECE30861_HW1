from __future__ import annotations
from acemcli.metrics.hf_api import HFAPIMetric


def test_supports_hf_model():
    m = HFAPIMetric()
    assert m.supports("https://huggingface.co/google/gemma-3-270m", "MODEL")