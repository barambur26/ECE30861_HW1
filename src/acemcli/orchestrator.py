from __future__ import annotations
import concurrent.futures as cf
from typing import Iterable
import orjson
from acmecli.metrics.base import all_metrics
from acmecli.models import MetricResult, Category


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


def _compute_one(url: str, category: Category) -> MetricResult:
for m in all_metrics():
if m.supports(url, category):
res = m.compute(url, category)
net = 0.0
net += WEIGHTS["ramp_up_time"] * res.ramp_up_time
net += WEIGHTS["bus_factor"] * res.bus_factor
net += WEIGHTS["performance_claims"] * res.performance_claims
net += WEIGHTS["license"] * res.license
net += WEIGHTS["size_score.desktop_pc"] * res.size_score["desktop_pc"]
net += WEIGHTS["dataset_and_code_score"] * res.dataset_and_code_score
net += WEIGHTS["dataset_quality"] * res.dataset_quality
net += WEIGHTS["code_quality"] * res.code_quality
res.net_score = max(0.0, min(1.0, net))
res.net_score_latency = 0
return res
raise ValueError(f"No metric supports URL: {url}")


def compute_all(pairs: Iterable[tuple[str, Category]]) -> Iterable[MetricResult]:
with cf.ThreadPoolExecutor(max_workers=8) as ex:
futures = [ex.submit(_compute_one, u, c) for (u, c) in pairs]
for fut in cf.as_completed(futures):
yield fut.result()


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