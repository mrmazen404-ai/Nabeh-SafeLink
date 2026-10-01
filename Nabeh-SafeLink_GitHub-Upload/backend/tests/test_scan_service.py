"""
Unit and Integration Tests for ScanService and Dynamic Hybrid Decision Matrix
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.scans.service import ScanService


def test_extract_url_from_text():
    text_with_url = "عزيزي العميل، يرجى تحديث بياناتك عبر الرابط التالي: https://bank-verify.com/login اليوم"
    extracted = ScanService.extract_url_from_text(text_with_url)
    assert extracted == "https://bank-verify.com/login"

    text_without_url = "تم إيداع الراتب في حسابك في البنك الأهلي"
    assert ScanService.extract_url_from_text(text_without_url) == ""


def test_analyze_text_phishing():
    # Normal banking notification without embedded URL should not be marked DANGEROUS
    normal_text = "تم إيداع الراتب في حسابك في البنك الأهلي"
    res_normal = ScanService.analyze_text_phishing(normal_text, has_embedded_url=False)
    assert res_normal["classification"] == "SUSPICIOUS"

    # Suspicious SMS with embedded URL should trigger higher severity
    suspicious_text = "عزيزي العميل، تم إيقاف حسابك البنكي. يرجى تحديث بطاقة سداد عبر الرابط"
    res_phish = ScanService.analyze_text_phishing(suspicious_text, has_embedded_url=True)
    assert res_phish["classification"] == "DANGEROUS"


def test_combine_scan_results_whitelist():
    ml_res = {"source": "WHITELIST", "classification": "SAFE", "phishing_prob": 0.01}
    vt_res = {"status": "UNKNOWN"}

    combined = ScanService.combine_scan_results(vt_res, ml_res)
    assert combined["classification"] == "UNKNOWN"


def test_combine_scan_results_hybrid():
    # Both engines detect danger
    vt_danger = {"status": "DANGEROUS", "malicious": 5, "suspicious": 2, "total_engines": 70}
    ml_danger = {"classification": "DANGEROUS", "phishing_prob": 0.92, "source": "LOCAL"}

    combined = ScanService.combine_scan_results(vt_danger, ml_danger)
    assert combined["classification"] == "DANGEROUS"
    assert combined["confidence"] >= 0.85
    assert combined["source"] == "RISK_SIGNAL"


def test_combine_scan_results_fallback_when_vt_unknown():
    # VirusTotal fails / rate-limited
    vt_unknown = {"status": "UNKNOWN", "error": "Rate limit"}
    ml_danger = {"classification": "DANGEROUS", "phishing_prob": 0.88, "source": "LOCAL"}

    combined = ScanService.combine_scan_results(vt_unknown, ml_danger)
    assert combined["classification"] == "DANGEROUS"
    assert combined["source"] == "RISK_SIGNAL"


@pytest.mark.asyncio
async def test_process_scan_graceful_degradation():
    with patch("app.scans.service.check_url_virustotal", new_callable=AsyncMock) as mock_vt, \
         patch("app.scans.service.generate_explanation", new_callable=AsyncMock) as mock_gemini, \
         patch("app.scans.service.supabase") as mock_supabase:

        # Mock VirusTotal failure
        mock_vt.side_effect = Exception("VirusTotal API Down")

        # Mock Gemini success
        mock_gemini.return_value = {
            "summary": "الرابط مشبوه وفق التحليل المحلي",
            "recommendation": "توخَّ الحذر",
            "provider": "GEMINI"
        }

        # Mock Supabase insert
        mock_supabase.table().insert().execute.return_value.data = [{"id": "scan_123"}]

        result = await ScanService.process_authenticated_scan("URL", "http://paypa1-secure-login.com", user_id="user_test_123")

        assert result["scan_id"] == "scan_123"
        assert result["classification"] == "UNKNOWN"
        assert result["explanation"]["provider"] == "GEMINI"


def test_no_valid_scanner_evidence_is_unknown():
    result = ScanService.combine_scan_results(
        {"status": "UNKNOWN", "total_engines": 0},
        {"classification": "UNKNOWN", "source": "MODEL_UNAVAILABLE"},
    )
    assert result["classification"] == "UNKNOWN"
    assert result["confidence"] is None


def test_text_without_known_keywords_is_not_declared_safe():
    result = ScanService.analyze_text_phishing("Hello, are we meeting at 5?")
    assert result["classification"] == "UNKNOWN"
    assert result["confidence"] is None


@pytest.mark.asyncio
async def test_guest_scan_does_not_call_external_providers_or_database():
    with patch("app.scans.service.check_url_virustotal", new_callable=AsyncMock) as mock_vt, \
         patch("app.scans.service.generate_explanation", new_callable=AsyncMock) as mock_gemini, \
         patch("app.scans.service.predict_url", return_value={"classification": "UNKNOWN", "source": "MODEL_UNAVAILABLE"}), \
         patch("app.scans.service.supabase") as mock_supabase:
        result = await ScanService.process_guest_scan("URL", "https://example.test", language="en")

        assert result["is_guest"] is True
        assert result["scan_id"] is None
        assert result["classification"] == "UNKNOWN"
        assert result["virustotal"]["status"] == "NOT_REQUESTED"
        mock_vt.assert_not_awaited()
        mock_gemini.assert_not_awaited()
        mock_supabase.table.assert_not_called()
