"""Centralized logging with file rotation.

Writes to ``logs/app.log`` and rotates by day (keep 7 days). Also logs
request/response info via the middleware defined in :mod:`app.main`.
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from app.core.config import LOG_DIR

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FORMAT_DETAIL = "%(asctime)s | %(levelname)-8s | %(name)s | %(pathname)s:%(lineno)d | %(message)s"

logger = logging.getLogger("blog")


def setup_logging(debug: bool = False) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_FORMAT_DETAIL if debug else _FORMAT)

    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log", when="midnight", backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(_FORMAT))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
