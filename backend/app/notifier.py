from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


async def send_alert(event_type: str, payload: dict[str, Any]) -> bool:
    if not settings.alert_webhook_url:
        return False
    body = {
        "source": "sentinelx",
        "event_type": event_type,
        "payload": payload,
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(settings.alert_webhook_url, json=body)
            response.raise_for_status()
        return True
    except Exception:
        return False
