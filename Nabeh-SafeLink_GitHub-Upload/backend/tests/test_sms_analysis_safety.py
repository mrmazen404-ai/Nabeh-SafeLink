import asyncio

from app.gemini.client import SMS_SYSTEM_INSTRUCTION, _local_sms_analysis
from app.gemini.schemas import validate_gemini_sms_payload
from app.scans.service import ScanService
from app.scans.text_rules import analyze_message_indicators


def test_absence_of_indicators_is_unknown_not_safe():
    for text in ("السلام عليكم", "موعد الاجتماع غداً", "تحديث التطبيق متاح"):
        result = analyze_message_indicators(text)
        assert result["classification"] == "UNKNOWN"
        assert result["confidence"] is None
        assert result["fraud_probability"] is None


def test_explicit_credential_request_is_suspicious_not_dangerous():
    result = analyze_message_indicators("أدخل رمز التحقق وكلمة المرور الآن")
    assert result["classification"] == "SUSPICIOUS"
    assert "credential_request" in result["indicators"]
    assert result["fraud_probability"] is None


def test_security_advice_not_misread_as_credential_collection():
    result = analyze_message_indicators("لا تشارك رمز التحقق أو كلمة المرور مع أي شخص")
    assert result["classification"] == "UNKNOWN"


def test_single_brand_or_url_does_not_establish_a_sms_verdict():
    result = analyze_message_indicators("مصرف الراجحي https://example.com")
    assert result["classification"] == "UNKNOWN"


def test_local_sms_fallback_uses_link_evidence_but_never_fabricates_probability():
    neutral = _local_sms_analysis("السلام عليكم", "", "ar")
    assert neutral["classification"] == "UNKNOWN"
    assert neutral["fraud_probability"] is None

    strong_link = _local_sms_analysis(
        "رسالة إشعار", "https://example.invalid", "ar",
        {"url_combined_verdict": {"classification": "DANGEROUS"}},
    )
    assert strong_link["classification"] == "DANGEROUS"


def test_sms_gemini_schema_drops_unapproved_fields_and_rejects_invalid_enum():
    fallback = {
        "classification": "UNKNOWN",
        "summary": "غير حاسم",
        "recommendation": "تحقق من المصدر مستقلاً.",
    }
    result = validate_gemini_sms_payload({
        "classification": "SAFE",
        "summary": "No risk indicators found.",
        "recommendation": "Verify independently.",
        "fraud_probability": 0.0,
        "api_key": "must-not-pass",
    }, fallback=fallback)
    assert result["classification"] == "SAFE"
    assert "fraud_probability" not in result
    assert "api_key" not in result

    invalid = validate_gemini_sms_payload({
        "classification": "CERTAINLY_SAFE",
        "summary": "unsafe invalid result",
        "recommendation": "trust it",
    }, fallback=fallback)
    assert invalid["classification"] == "UNKNOWN"
    assert invalid["provider"] == "LOCAL_SCHEMA_FALLBACK"
    assert "unsafe invalid result" not in repr(invalid)


def test_sms_prompt_treats_message_as_untrusted_and_allows_abstention():
    prompt = SMS_SYSTEM_INSTRUCTION.lower()
    assert "untrusted data" in prompt
    assert "unknown" in prompt
    assert "100% safe" in prompt
    assert "do not return confidence/probability" in prompt


def test_llm_dangerous_label_is_capped_without_dangerous_link_evidence():
    result = ScanService._enforce_text_safety_floor(
        {"classification": "UNKNOWN", "confidence": None},
        {"classification": "UNKNOWN", "confidence": None},
        {"classification": "SUSPICIOUS", "confidence": None},
    )
    assert result["classification"] == "SUSPICIOUS"


def test_sms_pipeline_never_returns_safe_without_sender_authentication(monkeypatch):
    from app.scans import service as scan_service
    from app.config import settings

    async def model_says_safe(**_kwargs):
        return {
            "classification": "SAFE",
            "summary": "No indicators found.",
            "recommendation": "You may trust it.",
            "provider": "GEMINI_AI",
        }

    monkeypatch.setattr(scan_service, "analyze_sms_message", model_says_safe)
    monkeypatch.setattr(scan_service, "setting_enabled_fail_closed", lambda _key: True)
    monkeypatch.setattr(settings, "SCAN_TOTAL_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(settings, "SCAN_AI_TIMEOUT_SECONDS", 4)
    result = asyncio.run(ScanService.process_text_scan("السلام عليكم", language="ar"))
    assert result["classification"] == "UNKNOWN"
    assert result["confidence"] is None
    assert result["fraud_probability"] is None
    assert result["explanation"]["authenticity_status"] == "غير متحقق"


def test_clean_link_reputation_does_not_make_sms_safe(monkeypatch):
    from app.scans import service as scan_service
    from app.config import settings

    async def model_says_safe(**_kwargs):
        return {
            "classification": "SAFE",
            "summary": "No indicators found.",
            "recommendation": "You may trust it.",
            "provider": "GEMINI_AI",
        }

    async def clean_link(**_kwargs):
        return {"status": "SAFE", "harmless": 80, "malicious": 0, "suspicious": 0, "total_engines": 80}

    monkeypatch.setattr(scan_service, "predict_url", lambda _url: {"classification": "SAFE", "phishing_prob": 0.0, "confidence": 0.99})
    monkeypatch.setattr(scan_service, "check_url_virustotal", clean_link)
    monkeypatch.setattr(scan_service, "analyze_sms_message", model_says_safe)
    monkeypatch.setattr(scan_service, "setting_enabled_fail_closed", lambda _key: True)
    monkeypatch.setattr(settings, "SCAN_TOTAL_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(settings, "SCAN_AI_TIMEOUT_SECONDS", 4)
    result = asyncio.run(ScanService.process_text_scan("إشعار: https://example.com", language="ar"))
    assert result["classification"] == "UNKNOWN"
    assert result["confidence"] is None


def test_gemini_alone_cannot_set_dangerous_sms_verdict(monkeypatch):
    from app.scans import service as scan_service
    from app.config import settings

    async def model_says_dangerous(**_kwargs):
        return {
            "classification": "DANGEROUS",
            "summary": "Potential fraud.",
            "recommendation": "Do not click.",
            "provider": "GEMINI_AI",
        }

    monkeypatch.setattr(scan_service, "analyze_sms_message", model_says_dangerous)
    monkeypatch.setattr(scan_service, "setting_enabled_fail_closed", lambda _key: True)
    monkeypatch.setattr(settings, "SCAN_TOTAL_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(settings, "SCAN_AI_TIMEOUT_SECONDS", 4)
    result = asyncio.run(ScanService.process_text_scan("السلام عليكم", language="ar"))
    assert result["classification"] == "SUSPICIOUS"
    assert result["fraud_probability"] is None


def test_text_scan_timeout_does_not_mark_greeting_safe(monkeypatch):
    from app.scans import service as scan_service
    from app.config import settings

    async def hanging_analysis(**_kwargs):
        await asyncio.sleep(0.02)

    monkeypatch.setattr(scan_service, "analyze_sms_message", hanging_analysis)
    monkeypatch.setattr(scan_service, "setting_enabled_fail_closed", lambda _key: True)
    monkeypatch.setattr(settings, "SCAN_AI_TIMEOUT_SECONDS", 0.001)
    result = asyncio.run(ScanService.process_text_scan("السلام عليكم", language="ar"))
    assert result["classification"] == "UNKNOWN"
    assert result["fraud_probability"] is None
