from __future__ import annotations
from acmecli.cli import infer_category


def test_infer_category_model():
assert infer_category("https://huggingface.co/google/gemma-3-270m") == "MODEL"