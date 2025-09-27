from __future__ import annotations
import sys
import logging
from pathlib import Path
from acemcli.logging_setup import setup_logging
from acemcli.orchestrator import compute_all, to_ndjson
from acemcli.models import Category

# Create module logger
logger = logging.getLogger(__name__)




def infer_category(url: str) -> Category:
    """Infer the category of a URL (MODEL, DATASET, or CODE)."""
    logger.debug(f"Inferring category for URL: {url}")
    
    if "/datasets/" in url:
        logger.debug(f"URL categorized as DATASET: {url}")
        return "DATASET"
    if url.startswith("https://huggingface.co/"):
        logger.debug(f"URL categorized as MODEL: {url}")
        return "MODEL"
    
    logger.debug(f"URL categorized as CODE: {url}")
    return "CODE"




def main(url_file: str) -> int:
    """Main CLI function to process URL file and compute metrics."""
    setup_logging()
    logger.info(f"Starting ACME CLI with URL file: {url_file}")
    
    p = Path(url_file)
    if not p.is_absolute() or not p.exists():
        error_msg = "URL_FILE must be an absolute path to an existing file"
        logger.error(f"Invalid URL file: {error_msg}")
        print(error_msg, file=sys.stderr)
        return 1

    logger.info(f"Reading URLs from file: {p}")
    try:
        lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        logger.info(f"Found {len(lines)} URLs in file")
    except Exception as e:
        logger.error(f"Failed to read URL file: {e}")
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    pairs: list[tuple[str, Category]] = []
    for ln in lines:
        cat = infer_category(ln)
        if cat == "MODEL":
            pairs.append((ln, cat))
            logger.debug(f"Added MODEL URL to processing queue: {ln}")
        else:
            logger.debug(f"Skipping non-MODEL URL: {ln} (category: {cat})")

    logger.info(f"Processing {len(pairs)} MODEL URLs")
    
    try:
        processed_count = 0
        for res in compute_all(pairs):
            sys.stdout.buffer.write(to_ndjson(res))
            processed_count += 1
            logger.debug(f"Processed and output result for: {res.name}")
        
        logger.info(f"Successfully processed {processed_count} URLs")
        return 0
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m acmecli.cli /absolute/path/to/URL_FILE", file=sys.stderr)
        raise SystemExit(1)
    
    # Setup logging before running main
    setup_logging()
    logger.info("CLI started from command line")
    
    exit_code = main(sys.argv[1])
    logger.info(f"CLI finished with exit code: {exit_code}")
    raise SystemExit(exit_code)