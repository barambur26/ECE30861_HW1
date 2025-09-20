from acmecli.orchestrator import _merge
from acmecli.models import MetricResult, SizeScore

def _mk():
    return MetricResult(
        name="n/x", category="MODEL",
        net_score=0.0, net_score_latency=0,
        ramp_up_time=0.0, ramp_up_time_latency=0,
        bus_factor=0.0, bus_factor_latency=0,
        performance_claims=0.0, performance_claims_latency=0,
        license=0.0, license_latency=0,
        size_score=SizeScore(raspberry_pi=0.0, jetson_nano=0.0, desktop_pc=0.0, aws_server=0.0),
        size_score_latency=0,
        dataset_and_code_score=0.0, dataset_and_code_score_latency=0,
        dataset_quality=0.0, dataset_quality_latency=0,
        code_quality=0.0, code_quality_latency=0,
    )

def test_merge_overlays_non_zero_fields():
    a, b = _mk(), _mk()
    b.dataset_quality = 0.9
    b.size_score["desktop_pc"] = 0.8
    out = _merge(a, b)
    assert out.dataset_quality == 0.9
    assert out.size_score["desktop_pc"] == 0.8
