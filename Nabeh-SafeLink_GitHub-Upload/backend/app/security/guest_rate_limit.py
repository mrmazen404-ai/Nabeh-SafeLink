"""Distributed rate limiting for the public guest scan endpoint.

Uses Upstash Redis REST directly, so it works in async FastAPI/Vercel
without a persistent Redis connection or a blocking Redis client.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException, Request

from app.observability import elapsed_ms, log_event, resource_id, safe_error

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


class UpstashRateLimiter:
    """Atomic fixed-window limiter backed by an Upstash Redis REST command."""

    LUA_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
""".strip()

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        limit: int = 10,
        window_seconds: int = 60,
        timeout_seconds: float = 2.5,
        fail_closed: bool = False,
    ) -> None:
        self.url = (url or os.getenv("UPSTASH_REDIS_REST_URL", "")).rstrip("/")
        self.token = token or os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self.timeout_seconds = max(0.5, float(timeout_seconds))
        self.fail_closed = fail_closed

    @property
    def configured(self) -> bool:
        return bool(self.url and self.token)

    async def check(self, identity: str) -> RateLimitDecision:
        started = time.perf_counter()
        identity_id = resource_id(identity)
        if not self.configured:
            if self.fail_closed:
                log_event(logger, logging.ERROR, "rate_limit_unconfigured_fail_closed", identity_id=identity_id)
                return RateLimitDecision(False, self.limit, 0, self.window_seconds)
            log_event(logger, logging.WARNING, "rate_limit_unconfigured_fail_open", identity_id=identity_id)
            return RateLimitDecision(True, self.limit, self.limit, 0)

        window_id = int(time.time()) // self.window_seconds
        key = f"nabeh:guest:scan:{self._hash_identity(identity)}:{window_id}"
        payload = ["EVAL", self.LUA_SCRIPT, "1", key, str(self.window_seconds)]

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=payload,
                )
                response.raise_for_status()
                body: Any = response.json()
                result = body.get("result") if isinstance(body, dict) else None
                current = int(result[0])
                ttl = max(1, int(result[1]))
        except Exception as error:
            log_event(logger, logging.ERROR, "rate_limit_provider_failed", identity_id=identity_id, error_type=safe_error(error), duration_ms=elapsed_ms(started))
            if self.fail_closed:
                return RateLimitDecision(False, self.limit, 0, self.window_seconds)
            # Availability of Redis must not take down local development.
            return RateLimitDecision(True, self.limit, self.limit, 0)

        remaining = max(0, self.limit - current)
        decision = RateLimitDecision(
            allowed=current <= self.limit,
            limit=self.limit,
            remaining=remaining,
            retry_after=ttl if current >= self.limit else 0,
        )
        log_event(logger, logging.INFO, "rate_limit_checked", identity_id=identity_id, allowed=decision.allowed, remaining=decision.remaining, duration_ms=elapsed_ms(started))
        return decision

    @staticmethod
    def _hash_identity(identity: str) -> str:
        # Never place a raw IP address in Redis keys or logs.
        salt = os.getenv("NABEH_RATE_LIMIT_SALT", "development-only-change-me").encode()
        return hmac.new(salt, identity.encode("utf-8", "ignore"), hashlib.sha256).hexdigest()[:32]


def client_identity(request: Request) -> str:
    """Return a stable client identity.

    X-Forwarded-For is used only when explicitly enabled because clients can
    forge it outside a trusted reverse proxy.
    """
    if os.getenv("NABEH_TRUST_PROXY_HEADERS", "false").lower() in {"1", "true", "yes"}:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


_guest_limiter = UpstashRateLimiter(
    limit=int(os.getenv("NABEH_GUEST_RATE_LIMIT", "10")),
    window_seconds=int(os.getenv("NABEH_GUEST_RATE_WINDOW_SECONDS", "60")),
    fail_closed=os.getenv("NABEH_RATE_LIMIT_FAIL_CLOSED", "false").lower() in {"1", "true", "yes"},
)


async def enforce_guest_rate_limit(request: Request) -> None:
    decision = await _guest_limiter.check(client_identity(request))
    if not decision.allowed:
        log_event(logger, logging.WARNING, "guest_rate_limit_blocked", remaining=decision.remaining, retry_after=decision.retry_after)
        raise HTTPException(
            status_code=429,
            detail="عدد محاولات فحص الضيف مرتفع مؤقتاً. حاول لاحقاً.",
            headers={
                "Retry-After": str(decision.retry_after or 60),
                "X-RateLimit-Limit": str(decision.limit),
                "X-RateLimit-Remaining": "0",
                "Cache-Control": "no-store",
            },
        )
