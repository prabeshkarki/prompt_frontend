# app/logger.py
from __future__ import annotations

import logging
import os


def _build_logger() -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    return logging.getLogger("product-chatbot")


logger = _build_logger()