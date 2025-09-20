from __future__ import annotations
from typing import Protocol, runtime_checkable
from acmecli.models import MetricResult, Category

@runtime_checkable
class Metric(Protocol):
    @property
    def name(self) -> str: ...
    def supports(self, url: str, category: Category) -> bool: ...
    def compute(self, url: str, category: Category) -> MetricResult: ...

_REGISTRY: list[Metric] = []

def register(metric: Metric) -> None:
    _REGISTRY.append(metric)

def all_metrics() -> list[Metric]:
    return list(_REGISTRY)
