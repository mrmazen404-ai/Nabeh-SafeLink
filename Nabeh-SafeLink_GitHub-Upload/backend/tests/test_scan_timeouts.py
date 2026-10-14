import asyncio

import pytest

from app.config import settings
from app.scans import service


@pytest.mark.anyio
async def test_text_scan_uses_local_fallback_when_ai_times_out(monkeypatch):
    async def hanging_analysis(**_kwargs):
        await asyncio.sleep(0.05)

    monkeypatch.setattr(service, "analyze_sms_message", hanging_analysis)
    monkeypatch.setattr(settings, "SCAN_AI_TIMEOUT_SECONDS", 0.001)

    result = await service.ScanService.process_text_scan("السلام عليكم", language="ar")

    assert result["classification"] == "SAFE"
    assert result["source"] == "LOCAL_TIMEOUT_FALLBACK"
    assert result["explanation"]["provider"] == "LOCAL_TIMEOUT_FALLBACK"
