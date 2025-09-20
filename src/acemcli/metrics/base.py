from __future__ import annotations
from typing import Protocol, runtime_checkable, ClassVar
from acmecli.models import MetricResult, Category

@runtime_checkable
class Metric(Protocol):
    # Declare `name` as a class attribute for all metrics
    name: ClassVar[str]

    def supports(self, url: str, category: Category) -> bool: ...
    def compute(self, url: str, category: Category) -> MetricResult: ...

# Module-level registry
_REGISTRY: list[Metric] = []

def register(metric: Metric) -> None:
    _REGISTRY.append(metric)

def all_metrics() -> list[Metric]:
    return list(_REGISTRY)
