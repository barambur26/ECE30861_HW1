from __future__ import annotations
import sys
from pathlib import Path
from acmecli.logging_setup import setup_logging
from acmecli.orchestrator import compute_all, to_ndjson
from acmecli.models import Category




def infer_category(url: str) -> Category:
if "/datasets/" in url:
return "DATASET"
if url.startswith("https://huggingface.co/"):
return "MODEL"
return "CODE"




def main(url_file: str) -> int:
setup_logging()
p = Path(url_file)
if not p.is_absolute() or not p.exists():
print("URL_FILE must be an absolute path to an existing file", file=sys.stderr)
return 1


lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
pairs: list[tuple[str, Category]] = []
for ln in lines:
cat = infer_category(ln)
if cat == "MODEL":
pairs.append((ln, cat))


try:
for res in compute_all(pairs):
sys.stdout.buffer.write(to_ndjson(res))
return 0
except Exception as e:
print(f"Error: {e}", file=sys.stderr)
return 1


if __name__ == "__main__":
if len(sys.argv) < 2:
print("Usage: python -m acmecli.cli /absolute/path/to/URL_FILE", file=sys.stderr)
raise SystemExit(1)
raise SystemExit(main(sys.argv[1]))