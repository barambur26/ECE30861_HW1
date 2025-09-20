from __future__ import annotations
import logging, tempfile, time
from pathlib import Path
from huggingface_hub import snapshot_download
from acmecli.models import MetricResult, Category
from acmecli.metrics.base import register

log = logging.getLogger(__name__)

KEYS = ("train", "test", "validation", "split", "license", "citation", "doi", "benchmark")

class DatasetQualityMetric:
    name = "dataset_quality"

    def supports(self, url: str, category: Category) -> bool:
        return url.startswith("https://huggingface.co/") and category == "DATASET"

    def _score_from_text(self, text: str) -> float:
        t = (text or "").lower()
        hits = sum(1 for k in KEYS if k in t)
        base = 0.3
        return max(0.0, min(1.0, base + 0.7 * (hits / max(1, len(KEYS)))))

    def compute(self, url: str, category: Category) -> MetricResult:
        t0 = time.perf_counter()
        namespace, repo = url.rstrip("/").split("/")[3:5]

        text = ""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                local_dir = snapshot_download(repo_id=f"{namespace}/{repo}", local_dir=tmp, local_dir_use_symlinks=False)
                p = Path(local_dir)
                files = [f for f in p.rglob("*") if f.is_file()]
                readme = next((f for f in files if f.name.lower().startswith("readme")), None)
                if readme:
                    text = readme.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            log.warning("dataset_quality: snapshot failed for %s/%s: %s", namespace, repo, e)

        score = self._score_from_text(text)
        log.info("dataset_quality: %s/%s score=%.3f", namespace, repo, score)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        return MetricResult(
            name=f"{namespace}/{repo}", category=category,
            net_score=0.0, net_score_latency=0,
            ramp_up_time=0.0, ramp_up_time_latency=0,
            bus_factor=0.0, bus_factor_latency=0,
            performance_claims=0.0, performance_claims_latency=0,
            license=0.0, license_latency=0,
            size_score={"raspberry_pi": 0.0, "jetson_nano": 0.0, "desktop_pc": 0.0, "aws_server": 0.0},
            size_score_latency=0,
            dataset_and_code_score=0.0, dataset_and_code_score_latency=0,
            dataset_quality=score, dataset_quality_latency=latency_ms,
            code_quality=0.0, code_quality_latency=0,
        )

register(DatasetQualityMetric())
