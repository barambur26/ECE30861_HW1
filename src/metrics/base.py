from __future__ import annotations
import logging
from typing import Protocol, runtime_checkable, ClassVar
from src.models import MetricResult, Category

# Create module logger
logger = logging.getLogger(__name__)

@runtime_checkable
class Metric(Protocol):
    # Declare `name` as a class attribute for all metrics
    name: ClassVar[str]

    def supports(self, url: str, category: Category) -> bool: ...
    def compute(self, url: str, category: Category) -> MetricResult: ...

# Module-level registry
_REGISTRY: list[Metric] = []

def register(metric: Metric) -> None:
    """Register a metric in the global registry."""
    logger.debug(f"Registering metric: {metric.name}")
    _REGISTRY.append(metric)
    logger.info(f"Metric '{metric.name}' registered successfully. Total metrics: {len(_REGISTRY)}")

def all_metrics() -> list[Metric]:
    """Get all registered metrics."""
    logger.debug(f"Retrieving all registered metrics (count: {len(_REGISTRY)})")
    if not _REGISTRY:
        logger.warning("No metrics are currently registered!")
    return list(_REGISTRY)
