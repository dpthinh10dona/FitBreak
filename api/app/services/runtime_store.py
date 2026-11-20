"""Shared runtime state backed by Redis with a process-local dev fallback."""

from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from datetime import date

try:
    from redis.asyncio import Redis
except ImportError:  # pragma: no cover
    Redis = None


logger = logging.getLogger(__name__)


class DailyQuotaStore:
    def __init__(self) -> None:
        redis_url = os.getenv("REDIS_URL", "").strip()
        self._redis = Redis.from_url(redis_url, decode_responses=True) if redis_url and Redis else None
        self._fallback: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(user_id: str) -> str:
        return f"fitbreak:chatbot-quota:{date.today().isoformat()}:{user_id}"

    async def get(self, user_id: str) -> int:
        key = self._key(user_id)
        if self._redis is not None:
            try:
                value = await self._redis.get(key)
                return int(value or 0)
            except Exception as exc:
                logger.warning("Redis quota read failed; using local fallback: %s", exc)
        async with self._lock:
            return self._fallback[key]

    async def increment(self, user_id: str) -> int:
        key = self._key(user_id)
        if self._redis is not None:
            try:
                async with self._redis.pipeline(transaction=True) as pipe:
                    pipe.incr(key)
                    pipe.expire(key, 172800)
                    result = await pipe.execute()
                return int(result[0])
            except Exception as exc:
                logger.warning("Redis quota increment failed; using local fallback: %s", exc)
        async with self._lock:
            self._fallback[key] += 1
            return self._fallback[key]


daily_chatbot_quota = DailyQuotaStore()
