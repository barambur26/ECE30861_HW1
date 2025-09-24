from __future__ import annotations
import concurrent.futures as cf
import logging
from typing import Iterable, List, Tuple
import orjson
from acmecli.metrics.base import all_metrics
from acmecli.models import MetricResult, Category
from acmecli.config import load_config

log = logging.getLogger(__name__)

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
    contributing = [m for m in all_metrics() if m.supports(url, category)]
    if not contributing:
        raise ValueError(f"No metric supports URL: {url}")

    results = [m.compute(url, category) for m in contributing]
    base = results[0]
    for r in results[1:]:
        base = _merge(base, r)

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
    return base

def compute_all(pairs: Iterable[tuple[str, Category]]) -> Tuple[List[MetricResult], List[tuple[str, str]]]:
    cfg = load_config()
    results: List[MetricResult] = []
    errors: List[tuple[str, str]] = []

    with cf.ThreadPoolExecutor(max_workers=cfg.workers) as ex:
        future_map = {ex.submit(_compute_one, u, c): (u, c) for (u, c) in pairs}
        for fut in cf.as_completed(future_map):
            url, cat = future_map[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                msg = f"{type(e).__name__}: {e}"
                errors.append((url, msg))
                log.warning("compute failed for %s (%s): %s", url, cat, msg)
    return results, errors

def to_ndjson(res: MetricResult) -> bytes:
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
    return orjson.dumps(payload) + b"\n"
