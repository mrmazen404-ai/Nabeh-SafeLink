"""
Unit and Integration Tests for Gemini AI Client
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.gemini.client import generate_explanation, _local_explanation, _default_rec


@pytest.mark.asyncio
async def test_generate_explanation_live_arabic():
    res = await generate_explanation(
        input_value="http://paypa1-verify-login.com/secure",
        classification="DANGEROUS",
        language="ar"
    )
    assert res is not None
    assert "summary" in res
    assert "reasons" in res
    assert "recommendation" in res
    assert res["provider"].startswith("GEMINI") or res["provider"] == "TEMPLATE"


@pytest.mark.asyncio
async def test_generate_explanation_live_english():
    res = await generate_explanation(
        input_value="https://www.google.com",
        classification="SAFE",
        language="en"
    )
    assert res is not None
    assert "summary" in res
    assert "reasons" in res
    assert "recommendation" in res


def test_local_explanation_fallback():
    exp_ar = _local_explanation("DANGEROUS", "ar")
    assert "تحذير خطير" in exp_ar["summary"]
    assert exp_ar["provider"] == "TEMPLATE"

    exp_en = _local_explanation("SAFE", "en")
    assert "safe" in exp_en["summary"].lower()
    assert exp_en["provider"] == "TEMPLATE"


def test_default_rec():
    assert "المتابعة" in _default_rec("SAFE", "ar")
    assert "safely" in _default_rec("SAFE", "en")


@pytest.mark.asyncio
async def test_gemini_missing_key_fallback():
    with patch("app.gemini.client.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = ""
        res = await generate_explanation("http://test.com", "SUSPICIOUS", "ar")
        assert res["provider"] == "TEMPLATE"
        assert "مشبوه" in res["summary"]
