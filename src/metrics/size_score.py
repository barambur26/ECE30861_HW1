from __future__ import annotations
import logging, tempfile, time
from pathlib import Path
from huggingface_hub import snapshot_download
from src.models import MetricResult, Category, SizeScore
from src.metrics.base import register

log = logging.getLogger(__name__)

class SizeScoreMetric:
    # ClassVar to satisfy your Protocol
    name = "size_score"

    def supports(self, url: str, category: Category) -> bool:
        return url.startswith("https://huggingface.co/") and category == "MODEL"

    def _size_to_score(self, b: int, caps: dict[str, int]) -> SizeScore:
        def s(cap: int) -> float:
            return max(0.0, min(1.0, 1.0 - (b / cap)))
        return {
            "raspberry_pi": s(caps["raspberry_pi"]),
            "jetson_nano": s(caps["jetson_nano"]),
            "desktop_pc": s(caps["desktop_pc"]),
            "aws_server":  s(caps["aws_server"]),
        }

    def compute(self, url: str, category: Category) -> MetricResult:
        t0 = time.perf_counter()
        namespace, repo = url.rstrip("/").split("/")[3:5]

        weights_bytes = 0
        try:
            with tempfile.TemporaryDirectory() as tmp:
                local_dir = snapshot_download(
                    repo_id=f"{namespace}/{repo}",
                    local_dir=tmp,
                    local_dir_use_symlinks=False,
                )
                p = Path(local_dir)
                files = [f for f in p.rglob("*") if f.is_file()]
                weights_bytes = sum(
                    f.stat().st_size for f in files
                    if f.suffix in {".bin", ".safetensors", ".h5"}
                )
        except Exception as e:
            log.warning("size_score: snapshot failed for %s/%s: %s", namespace, repo, e)

        caps = {
            "raspberry_pi": 250_000_000,
            "jetson_nano": 500_000_000,
            "desktop_pc":  4_000_000_000,
            "aws_server":  16_000_000_000,
        }
        size_score = self._size_to_score(weights_bytes, caps)
        log.info("size_score %s/%s bytes=%d score=%s", namespace, repo, weights_bytes, size_score)

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return MetricResult(
            name=f"{namespace}/{repo}", category=category,
            net_score=0.0, net_score_latency=0,
            ramp_up_time=0.0, ramp_up_time_latency=0,
            bus_factor=0.0, bus_factor_latency=0,
            performance_claims=0.0, performance_claims_latency=0,
            license=0.0, license_latency=0,
            size_score=size_score, size_score_latency=latency_ms,
            dataset_and_code_score=0.0, dataset_and_code_score_latency=0,
            dataset_quality=0.0, dataset_quality_latency=0,
            code_quality=0.0, code_quality_latency=0,
        )

register(SizeScoreMetric())
