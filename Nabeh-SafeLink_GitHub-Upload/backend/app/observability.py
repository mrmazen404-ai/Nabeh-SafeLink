"""Central, security-conscious application logging for Nabeh SafeLink."""

from __future__ import annotations

import contextvars
import hashlib
import logging
import os
import re
import time
from typing import Any

_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_SECRET_KEY_RE = re.compile(r"(token|secret|password|passwd|api[_-]?key|authorization|accessToken|code_hash|otp)", re.I)


def set_request_id(value: str):
    return _REQUEST_ID.set(value or "-")


def reset_request_id(token: contextvars.Token) -> None:
    _REQUEST_ID.reset(token)


def request_id() -> str:
    return _REQUEST_ID.get()


def configure_logging() -> None:
    """Configure terminal logs once; never log secrets or request bodies."""
    level_name = os.getenv("NABEH_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    root.setLevel(level)
    for noisy in ("httpx", "httpcore", "hpack", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id()
        return True


# Install the filter on the root handlers after basicConfig has created them.
def install_request_id_filter() -> None:
    for handler in logging.getLogger().handlers:
        if not any(isinstance(item, _RequestIdFilter) for item in handler.filters):
            handler.addFilter(_RequestIdFilter())


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Log structured key/value fields after removing sensitive values."""
    safe_fields = []
    for key, value in fields.items():
        if _SECRET_KEY_RE.search(key):
            value = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 240:
            value = value[:240] + "…"
        safe_fields.append(f"{key}={value}")
    logger.log(level, "%s%s", event, (" | " + " ".join(safe_fields)) if safe_fields else "")


def safe_error(error: BaseException) -> str:
    """Return an error type only; provider responses may contain secrets or PII."""
    return type(error).__name__


def mask_email(email: str) -> str:
    value = (email or "").strip().lower()
    if "@" not in value:
        return "[invalid-email]"
    local, domain = value.split("@", 1)
    first = local[:1] or "*"
    return f"{first}***@{domain}"


def resource_id(value: str) -> str:
    """Stable short identifier for logs without exposing input data."""
    return hashlib.sha256((value or "").encode("utf-8", "ignore")).hexdigest()[:12]


def elapsed_ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)
