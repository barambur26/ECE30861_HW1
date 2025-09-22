from __future__ import annotations
import concurrent.futures as cf
import logging
from typing import Iterable
import orjson
from acmecli.metrics.base import all_metrics
from acmecli.models import MetricResult, Category

# Create module logger
logger = logging.getLogger(__name__)

WEIGHTS = {
    "ramp_up_time": 0.15,
    "bus_factor": 0.15,
    "performance_claims": 0.10,
    "license": 0.10,
    "size_score.desktop_pc": 0.10,
    "dataset_and_code_score": 0.10,
    "dataset_quality": 0.15,
    "code_quality": 0.15,
}

def _merge(base: MetricResult, add: MetricResult) -> MetricResult:
    """Merge two MetricResult objects, preferring non-zero values from 'add'."""
    logger.debug(f"Merging metric results for {base.name}")
    
    def pick(a: float, b: float) -> float:
        return b if isinstance(b, (int, float)) and b not in (0, 0.0) else a

    base.ramp_up_time = pick(base.ramp_up_time, add.ramp_up_time)
    base.ramp_up_time_latency = max(base.ramp_up_time_latency, add.ramp_up_time_latency)

    base.bus_factor = pick(base.bus_factor, add.bus_factor)
    base.bus_factor_latency = max(base.bus_factor_latency, add.bus_factor_latency)

    base.performance_claims = pick(base.performance_claims, add.performance_claims)
    base.performance_claims_latency = max(base.performance_claims_latency, add.performance_claims_latency)

    base.license = pick(base.license, add.license)
    base.license_latency = max(base.license_latency, add.license_latency)

    for k in base.size_score:
        base.size_score[k] = pick(base.size_score[k], add.size_score.get(k, 0.0))
    base.size_score_latency = max(base.size_score_latency, add.size_score_latency)

    base.dataset_and_code_score = pick(base.dataset_and_code_score, add.dataset_and_code_score)
    base.dataset_and_code_score_latency = max(base.dataset_and_code_score_latency, add.dataset_and_code_score_latency)

    base.dataset_quality = pick(base.dataset_quality, add.dataset_quality)
    base.dataset_quality_latency = max(base.dataset_quality_latency, add.dataset_quality_latency)

    base.code_quality = pick(base.code_quality, add.code_quality)
    base.code_quality_latency = max(base.code_quality_latency, add.code_quality_latency)

    return base

def _compute_one(url: str, category: Category) -> MetricResult:
    """Compute all metrics for a single URL."""
    logger.info(f"Computing metrics for {category} URL: {url}")
    
    contributing = [m for m in all_metrics() if m.supports(url, category)]
    logger.debug(f"Found {len(contributing)} contributing metrics: {[m.name for m in contributing]}")
    
    if not contributing:
        error_msg = f"No metric supports URL: {url}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug(f"Computing individual metrics for {url}")
    results = []
    for metric in contributing:
        try:
            result = metric.compute(url, category)
            results.append(result)
            logger.debug(f"Metric {metric.name} completed for {url}")
        except Exception as e:
            logger.error(f"Metric {metric.name} failed for {url}: {e}")
            raise
    
    logger.debug(f"Merging {len(results)} metric results for {url}")
    base = results[0]
    for r in results[1:]:
        base = _merge(base, r)

    logger.debug(f"Computing weighted net score for {url}")
    net = 0.0
    net += WEIGHTS["ramp_up_time"] * base.ramp_up_time
    net += WEIGHTS["bus_factor"] * base.bus_factor
    net += WEIGHTS["performance_claims"] * base.performance_claims
    net += WEIGHTS["license"] * base.license
    net += WEIGHTS["size_score.desktop_pc"] * base.size_score["desktop_pc"]
    net += WEIGHTS["dataset_and_code_score"] * base.dataset_and_code_score
    net += WEIGHTS["dataset_quality"] * base.dataset_quality
    net += WEIGHTS["code_quality"] * base.code_quality
    
    base.net_score = max(0.0, min(1.0, net))
    base.net_score_latency = 0
    
    logger.info(f"Completed metrics computation for {url} with net score: {base.net_score:.3f}")
    return base

def compute_all(pairs: Iterable[tuple[str, Category]]) -> Iterable[MetricResult]:
    """Compute metrics for all URL pairs in parallel."""
    pairs_list = list(pairs)
    logger.info(f"Starting parallel computation for {len(pairs_list)} URLs with max_workers=8")
    
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(_compute_one, u, c) for (u, c) in pairs_list]
        logger.debug(f"Submitted {len(futures)} tasks to thread pool")
        
        completed_count = 0
        for fut in cf.as_completed(futures):
            try:
                result = fut.result()
                completed_count += 1
                logger.debug(f"Completed {completed_count}/{len(futures)} tasks")
                yield result
            except Exception as e:
                logger.error(f"Task failed with exception: {e}")
                raise
        
        logger.info(f"All {len(futures)} tasks completed successfully")

def to_ndjson(res: MetricResult) -> bytes:
    """Convert MetricResult to NDJSON bytes."""
    logger.debug(f"Converting result to NDJSON for {res.name}")
    
    payload = {
        "name": res.name,
        "category": res.category,
        "net_score": res.net_score,
        "net_score_latency": res.net_score_latency,
        "ramp_up_time": res.ramp_up_time,
        "ramp_up_time_latency": res.ramp_up_time_latency,
        "bus_factor": res.bus_factor,
        "bus_factor_latency": res.bus_factor_latency,
        "performance_claims": res.performance_claims,
        "performance_claims_latency": res.performance_claims_latency,
        "license": res.license,
        "license_latency": res.license_latency,
        "size_score": res.size_score,
        "size_score_latency": res.size_score_latency,
        "dataset_and_code_score": res.dataset_and_code_score,
        "dataset_and_code_score_latency": res.dataset_and_code_score_latency,
        "dataset_quality": res.dataset_quality,
        "dataset_quality_latency": res.dataset_quality_latency,
        "code_quality": res.code_quality,
        "code_quality_latency": res.code_quality_latency,
    }
    
    try:
        json_bytes = orjson.dumps(payload) + b"\n"
        logger.debug(f"Successfully serialized result for {res.name} ({len(json_bytes)} bytes)")
        return json_bytes
    except Exception as e:
        logger.error(f"Failed to serialize result for {res.name}: {e}")
        raise
