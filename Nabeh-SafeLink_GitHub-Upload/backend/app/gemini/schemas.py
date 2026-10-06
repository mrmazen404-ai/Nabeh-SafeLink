"""Strict, bounded schemas for untrusted Gemini output."""

from __future__ import annotations

import html
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean_text(value: str, max_length: int) -> str:
    value = _CONTROL_CHARS.sub("", html.unescape(value or ""))
    value = re.sub(r"<[^>]*>", "", value)
    return value.strip()[:max_length]


class GeminiExplanation(BaseModel):
    """Only fields that the UI is allowed to receive from the model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=600)
    reasons: list[str] = Field(default_factory=list, max_length=5)
    recommendation: str = Field(min_length=1, max_length=500)
    limitations: list[str] = Field(default_factory=list, max_length=5)
    claimed_sender: str = Field(default="غير محددة", max_length=160)
    official_domain: str = Field(default="غير متاح", max_length=253)
    lure_type: str = Field(default="غير محدد", max_length=160)
    authenticity_status: str = Field(default="UNKNOWN", max_length=80)

    @field_validator("summary", "recommendation", "claimed_sender", "official_domain", "lure_type", "authenticity_status")
    @classmethod
    def clean_scalar(cls, value: str) -> str:
        return _clean_text(value, 600)

    @field_validator("reasons", "limitations")
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        return [_clean_text(item, 300) for item in values if _clean_text(item, 300)]


def validate_gemini_payload(payload: Any, *, fallback: dict[str, Any]) -> dict[str, Any]:
    """Validate model data and return only the allow-listed schema fields."""
    try:
        parsed = GeminiExplanation.model_validate(payload)
        return parsed.model_dump()
    except Exception:
        # Do not expose validation errors or raw model output to clients/logs.
        safe_fallback = {
            "summary": fallback.get("summary", "تعذر التحقق من تفسير الذكاء الاصطناعي."),
            "reasons": fallback.get("reasons", []),
            "recommendation": fallback.get("recommendation", "توخ الحذر وتحقق من المصدر."),
            "limitations": ["تم استخدام التفسير المحلي لأن مخرجات مزود الذكاء الاصطناعي غير صالحة."],
            "claimed_sender": "غير محددة",
            "official_domain": "غير متاح",
            "lure_type": "غير محدد",
            "authenticity_status": "UNKNOWN",
        }
        return GeminiExplanation.model_validate(safe_fallback).model_dump()
