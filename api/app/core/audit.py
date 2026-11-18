"""PII-safe structured audit events."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from fastapi import Request

logger = logging.getLogger("fitbreak.audit")


def _opaque(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:16]


def audit_event(event: str, request: Request, *, user_id: str | None = None, outcome: str) -> None:
    # Never log passwords, JWTs, raw email addresses or request bodies.
    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "outcome": outcome,
        "user_ref": _opaque(user_id),
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "")[:160],
    }, ensure_ascii=False))

