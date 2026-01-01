from __future__ import annotations

import json
import os
import urllib.request

from app.core.logging import logger

CS_ALERT_WEBHOOK_URL = os.getenv("CS_ALERT_WEBHOOK_URL", "").strip()


def alert_customer_service(payload: dict) -> None:
    """
    Server-side alert. Always logs.
    If CS_ALERT_WEBHOOK_URL is set, also POSTs JSON to it.
    """
    logger.warning("CUSTOMER_SERVICE_ALERT: %s", payload)

    if not CS_ALERT_WEBHOOK_URL:
        return

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            CS_ALERT_WEBHOOK_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            _ = resp.read()
    except Exception:
        logger.exception("Failed to POST customer service alert webhook.")