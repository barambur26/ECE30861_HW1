from __future__ import annotations
import logging
import os

# Logging framework via a $log_file and $log_level (Blas)


def setup_logging() -> None:
    """
    Set up logging based on environment variables.
    
    Environment variables:
    - LOG_LEVEL: 0 (silent/critical), 1 (info), 2 (debug)
    - LOG_FILE: Optional file path for logging output
    """
    level_map = {"0": logging.CRITICAL, "1": logging.INFO, "2": logging.DEBUG}
    lvl = level_map.get(os.environ.get("LOG_LEVEL", "0"), logging.CRITICAL)
    logfile = os.environ.get("LOG_FILE")

    handlers = []
    
    # Add file handler if LOG_FILE is specified
    if logfile:
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setLevel(lvl)
        handlers.append(fh)
    
    # Always add console/stream handler
    sh = logging.StreamHandler()
    sh.setLevel(lvl)
    handlers.append(sh)

    # Configure basic logging
    logging.basicConfig(
        level=lvl, 
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
        handlers=handlers,
        force=True  # This ensures we override any existing configuration
    )
