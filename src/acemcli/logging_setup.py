from __future__ import annotations
import logging, os


def setup_logging() -> None:
level_map = {"0": logging.CRITICAL, "1": logging.INFO, "2": logging.DEBUG}
lvl = level_map.get(os.environ.get("LOG_LEVEL", "0"), logging.CRITICAL)
logfile = os.environ.get("LOG_FILE")


handlers = []
if logfile:
fh = logging.FileHandler(logfile, encoding="utf-8")
fh.setLevel(lvl)
handlers.append(fh)
sh = logging.StreamHandler()
sh.setLevel(lvl)
handlers.append(sh)


logging.basicConfig(level=lvl, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=handlers)