"""Server-side medical document storage that never exposes the service key."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from supabase import Client, create_client


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _service_client() -> Client | None:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        return None
    return create_client(url, key)


def persist_medical_document(object_name: str, content: bytes, content_type: str) -> bool:
    """Upload with the backend-only service role. Returns False in local dev fallback."""
    client = _service_client()
    if client is None:
        logger.warning("SUPABASE_SERVICE_ROLE_KEY is missing; document is only processed locally.")
        return False

    bucket = os.getenv("SUPABASE_MEDICAL_BUCKET", "FitBreak Medical Knowledge")
    try:
        client.storage.get_bucket(bucket)
    except Exception:
        client.storage.create_bucket(bucket, options={"public": False})

    client.storage.from_(bucket).upload(
        object_name,
        content,
        {"content-type": content_type, "upsert": "false"},
    )
    return True
