import pytest
from app.scans.service import ScanService
from app.gemini.client import _local_sms_analysis


def test_extract_url_from_text_naked_domains_and_explicit_urls():
    # 1. Explicit http/https
    assert ScanService.extract_url_from_text("رابط الفحص https://example.com/test") == "https://example.com/test"
    assert ScanService.extract_url_from_text("زر موقعنا http://my-site.org") == "http://my-site.org"

    # 2. www. prefix
    assert ScanService.extract_url_from_text("زوروا موقعنا www.alrajhibank.com.sa") == "www.alrajhibank.com.sa"

    # 3. Naked domains without http/https or www
    assert ScanService.extract_url_from_text("تحديث البيانات عبر bank-alrajhi-update.com/login الآن") == "bank-alrajhi-update.com/login"
    assert ScanService.extract_url_from_text("سدد الغرامة من خلال stc-pay-portal.sa فوراً") == "stc-pay-portal.sa"

    # 4. Text without any URL or domain
    assert ScanService.extract_url_from_text("السلام عليكم ورحمة الله وبركاته كيف حالك اليوم؟") == ""


def test_analyze_text_phishing_no_false_positives_for_normal_text():
    # Normal text without phishing keywords or links should be SAFE
    res = ScanService.analyze_text_phishing("مرحباً بك، تذكرة الطيران الخاصة برحلتك القادمة جاهزة ويمكنك استلامها في أي وقت.", has_embedded_url=False)
    assert res["classification"] == "SAFE"

    # Text with phishing keywords and embedded URL should be DANGEROUS/SUSPICIOUS
    phishing_res = ScanService.analyze_text_phishing("حسابك البنكي موقوف يرجى تحديث كلمة المرور عبر البطاقة", has_embedded_url=True)
    assert phishing_res["classification"] in {"DANGEROUS", "SUSPICIOUS"}


def test_local_sms_analysis_normal_text_is_safe():
    normal_text = "رسالة تذكير بموعد الاجتماع الدوري لمجلس الإدارة غداً الساعة العاشرة صباحاً في القاعة الرئيسية."
    res = _local_sms_analysis(text_content=normal_text, extracted_url="", language="ar")
    assert res["classification"] == "SAFE"
    assert res["fraud_probability"] <= 0.05
    # When no known brand is mentioned, official_portal_url MUST be "غير متاح"
    assert res["official_portal_url"] == "غير متاح"


def test_local_sms_analysis_known_brand_matches_official_portal():
    kuraimi_text = "جائزة من بنك الكريمي ادخل https://kuraimi-fake.com/login"
    res = _local_sms_analysis(text_content=kuraimi_text, extracted_url="https://kuraimi-fake.com/login", language="ar")
    assert res["official_portal_url"] == "https://www.kuraimibank.com"


def test_dynamic_social_engineering_risk_scores():
    # 1. Benign normal greeting
    benign_res = _local_sms_analysis(text_content="مرحباً أهلاً وسهلاً بك", extracted_url="", language="ar")
    assert benign_res["urgency_pressure_score"] <= 10
    assert benign_res["credential_theft_score"] <= 5
    assert benign_res["identity_spoofing_score"] <= 5

    # 2. Text with urgency pressure ("مهلة ساعة فوري")
    urgency_res = _local_sms_analysis(text_content="عاجل فوري مهلة ساعة واحدة لإتمام الإجراء", extracted_url="", language="ar")
    assert urgency_res["urgency_pressure_score"] >= 60

    # 3. Text with OTP & credential theft ("رمز OTP كلمة المرور")
    otp_res = _local_sms_analysis(text_content="أدخل رمز OTP وكلمة المرور لتأكيد الحساب", extracted_url="", language="ar")
    assert otp_res["credential_theft_score"] >= 60

    # 4. Text with brand spoofing ("مصرف الراجحي")
    brand_res = _local_sms_analysis(text_content="تنبيه من مصرف الراجحي بخصوص بطاقتك", extracted_url="", language="ar")
    assert brand_res["identity_spoofing_score"] >= 75


def test_sanitize_official_portal_url_removes_generic_hallucinations():
    from app.gemini.client import _sanitize_official_portal_url

    # 1. Hallucinated portal in a message without a known brand -> forced to "غير متاح"
    hallucinated_payload = {"official_portal_url": "https://www.my.gov.sa", "summary": "Test"}
    cleaned_1 = _sanitize_official_portal_url(hallucinated_payload, "رسالة عادية لا تنتمي لأي جهة", "")
    assert cleaned_1["official_portal_url"] == "غير متاح"

    # 2. Known brand mentioned -> sanitized to exact verified brand portal
    kuraimi_payload = {"official_portal_url": "https://fake.com", "summary": "Test"}
    cleaned_2 = _sanitize_official_portal_url(kuraimi_payload, "تحديث حسابك في بنك الكريمي", "https://fake-link.com")
    assert cleaned_2["official_portal_url"] == "https://www.kuraimibank.com"





def test_url_explanation_cannot_return_generic_hallucinated_portal_or_domain():
    from app.gemini.client import _validated_model_result

    result = _validated_model_result(
        {
            "summary": "Test result",
            "reasons": [],
            "recommendation": "Be cautious",
            "official_portal_url": "https://www.my.gov.sa/login",
            "official_domain": "my.gov.sa",
        },
        model_name="test-model",
        provider="GEMINI",
        classification="SUSPICIOUS",
        language="en",
        input_value="https://example.net/verify",
        evidence={},
    )
    assert result["official_portal_url"] == "غير متاح"
    assert result["official_domain"] == "غير متاح"


def test_sanitizer_recognizes_brand_tokens_but_not_substrings():
    from app.gemini.client import _sanitize_official_portal_url

    unrelated = _sanitize_official_portal_url(
        {"official_portal_url": "https://www.stc.com.sa", "official_domain": "stc.com.sa"},
        "Bestchoice update: your weekly summary is ready",
        "",
    )
    assert unrelated["official_portal_url"] == "غير متاح"

    branded = _sanitize_official_portal_url(
        {"official_portal_url": "https://fake.example", "official_domain": "fake.example"},
        "Your PayPal account needs verification",
        "https://paypal-login.example/verify",
    )
    assert branded["official_portal_url"] == "https://www.paypal.com"
    assert branded["official_domain"] == "paypal.com"
