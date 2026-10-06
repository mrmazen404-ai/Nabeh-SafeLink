"""
Gemini AI Client for Nabeh SafeLink
Provides non-blocking async security explanations using Google GenAI SDK (client.aio)
with structured JSON output and multi-model fallback resilience.
"""

import os
import json
import re
import logging
from google import genai
from google.genai import types
from app.config import settings
from app.gemini.schemas import validate_gemini_payload
from app.observability import log_event, resource_id, safe_error

client = None
_client_api_key = None
logger = logging.getLogger(__name__)


def _validated_model_result(
    parsed: dict,
    *,
    model_name: str,
    provider: str,
    classification: str,
    language: str,
    input_value: str,
    evidence: dict,
) -> dict:
    fallback = _local_explanation(classification, language, input_value=input_value, evidence=evidence)
    result = validate_gemini_payload(parsed, fallback=fallback)
    result["provider"] = f"{provider} ({model_name})"
    return result


def _get_api_key() -> str:
    if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY == "":
        return ""
    return settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")


def _get_client():
    global client, _client_api_key
    current_key = _get_api_key()
    if not current_key:
        return None
    if client is None or _client_api_key != current_key:
        _client_api_key = current_key
        client = genai.Client(api_key=current_key)
    return client

# Models ordered by priority for current Google AI Studio API keys
PRIMARY_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]

SYSTEM_INSTRUCTION = """
You are a top-tier cybersecurity AI research analyst for Nabeh SafeLink (نابه).
Your task is to analyze URLs, perform domain reputation research, identify official vs spoofed brand domains, evaluate phishing/malware risks, and explain your technical findings in valid JSON.
"""


async def generate_explanation(
    input_value: str,
    classification: str,
    language: str = "ar",
    evidence: dict | None = None,
) -> dict:
    """
    Generates structured AI explanation asynchronously with real-time web intelligence.
    Falls back gracefully if API errors occur.
    """
    lang_name = "Arabic" if language == "ar" else "English"
    evidence = evidence or {}
    operation_id = resource_id(input_value)
    log_event(logger, logging.INFO, "gemini_explanation_started", operation_id=operation_id, classification=classification, language=language)
    ml_evidence = evidence.get("ml", {})
    vt_evidence = evidence.get("virustotal", {})
    safe_evidence = {
        "classification": classification,
        "ml": {
            "classification": ml_evidence.get("classification"),
            "phishing_prob": ml_evidence.get("phishing_prob"),
            "threshold": ml_evidence.get("threshold"),
            "source": ml_evidence.get("source"),
        },
        "virustotal": {
            "status": vt_evidence.get("status"),
            "malicious": vt_evidence.get("malicious", 0),
            "suspicious": vt_evidence.get("suspicious", 0),
            "harmless": vt_evidence.get("harmless", 0),
            "total_engines": vt_evidence.get("total_engines", 0),
        },
    }

    prompt = f"""
Input Value: {input_value[:300]}
Primary Security Classification: {classification}
Requested Explanation Language: {lang_name}
Evidence Data:
{json.dumps(safe_evidence, ensure_ascii=False)}

Cybersecurity Research Instructions:
1. Search and identify the true official registered domain for any organization or brand mentioned or impersonated in the input URL.
2. Compare the input URL's domain against the official domain and highlight any discrepancies, typosquatting, or spoofing.
3. Analyze deceptive keywords, TLD risk, ML model probabilities, and VirusTotal engine findings.
4. Do not alter the Primary Security Classification.

Respond ONLY in valid JSON matching this exact structure:
{{
  "summary": "Clear 1-2 sentence summary explaining the security research findings in {lang_name}",
  "reasons": ["Key technical reason 1 comparing official domain vs URL in {lang_name}", "Key technical reason 2 in {lang_name}", "Key technical reason 3 in {lang_name}"],
  "recommendation": "Practical actionable security advice in {lang_name}",
  "limitations": []
}}
"""

    current_key = _get_api_key()
    if not current_key:
        log_event(logger, logging.WARNING, "gemini_provider_not_configured", operation_id=operation_id)
        return _local_explanation(classification, language, input_value=input_value, evidence=evidence)

    gemini_client = _get_client()
    if gemini_client is None:
        log_event(logger, logging.WARNING, "gemini_client_unavailable", operation_id=operation_id)
        return _local_explanation(classification, language, input_value=input_value, evidence=evidence)

    # Try models in priority order
    for model_name in PRIMARY_MODELS:
        log_event(logger, logging.INFO, "gemini_model_attempt_started", operation_id=operation_id, model=model_name, mode="search")
        # Attempt 1: Search Grounded Generation
        try:
            response = await gemini_client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2,
                )
            )
            text = response.text.strip() if response.text else ""
            text_clean = re.sub(r'^```json\s*', '', text)
            text_clean = re.sub(r'\s*```$', '', text_clean)

            parsed = json.loads(text_clean)
            result = _validated_model_result(
                parsed,
                model_name=model_name,
                provider="GEMINI_SEARCH",
                classification=classification,
                language=language,
                input_value=input_value,
                evidence=evidence,
            )
            log_event(logger, logging.INFO, "gemini_model_succeeded", operation_id=operation_id, model=model_name, mode="search")
            return result
        except Exception as error:
            log_event(logger, logging.WARNING, "gemini_model_attempt_failed", operation_id=operation_id, model=model_name, mode="search", error_type=safe_error(error))

        # Attempt 2: Standard Gemini Generation
        try:
            response = await gemini_client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )

            text = response.text.strip() if response.text else ""
            text_clean = re.sub(r'^```json\s*', '', text)
            text_clean = re.sub(r'\s*```$', '', text_clean)

            try:
                parsed = json.loads(text_clean)
                result = _validated_model_result(
                    parsed,
                    model_name=model_name,
                    provider="GEMINI",
                    classification=classification,
                    language=language,
                    input_value=input_value,
                    evidence=evidence,
                )
                log_event(logger, logging.INFO, "gemini_model_succeeded", operation_id=operation_id, model=model_name, mode="json")
                return result
            except json.JSONDecodeError:
                if text:
                    result = _validated_model_result(
                        {"summary": text[:300], "recommendation": _default_rec(classification, language)},
                        model_name=model_name,
                        provider="GEMINI",
                        classification=classification,
                        language=language,
                        input_value=input_value,
                        evidence=evidence,
                    )
                    log_event(logger, logging.INFO, "gemini_model_succeeded", operation_id=operation_id, model=model_name, mode="text_fallback")
                    return result

        except Exception as e:
            log_event(logger, logging.WARNING, "gemini_provider_request_failed", operation_id=operation_id, model=model_name, error_type=safe_error(e))
            continue

    log_event(logger, logging.WARNING, "gemini_provider_fallback_used", operation_id=operation_id)
    return _local_explanation(classification, language, input_value=input_value, evidence=evidence)


def _default_rec(classification: str, language: str = "ar") -> str:
    recs = {
        "SAFE": {"ar": "يمكنك المتابعة والتصفح بأمان", "en": "You can proceed safely"},
        "SUSPICIOUS": {"ar": "تحقق من المصدر قبل إدخال أي بيانات", "en": "Verify the source before entering data"},
        "DANGEROUS": {"ar": "تجنب النقر أو مشاركة هذا الرابط", "en": "Avoid clicking or sharing this link"},
        "UNKNOWN": {"ar": "توخَّ الحذر وتجنب مشاركة بياناتك", "en": "Exercise caution and avoid sharing info"},
    }
    return recs.get(classification, recs["UNKNOWN"]).get(language, "Be cautious")


KNOWN_BRANDS = {
    "alrajhi": ("مصرف الراجحي", "Al Rajhi Bank", "alrajhibank.com.sa"),
    "alrajhibank": ("مصرف الراجحي", "Al Rajhi Bank", "alrajhibank.com.sa"),
    "alahli": ("البنك الأهلي SNB", "SNB AlAhli", "snb.com.sa"),
    "snb": ("البنك الأهلي SNB", "SNB AlAhli", "snb.com.sa"),
    "alinma": ("مصرف الإنماء", "Alinma Bank", "alinma.com"),
    "paypal": ("PayPal", "PayPal", "paypal.com"),
    "paypa1": ("PayPal (انتحال اسم)", "PayPal (Impersonated)", "paypal.com"),
    "google": ("Google", "Google", "google.com"),
    "googl3": ("Google (انتحال اسم)", "Google (Impersonated)", "google.com"),
    "microsoft": ("Microsoft", "Microsoft", "microsoft.com"),
    "apple": ("Apple", "Apple", "apple.com"),
    "amazon": ("Amazon", "Amazon", "amazon.com"),
    "facebook": ("Facebook", "Facebook", "facebook.com"),
    "instagram": ("Instagram", "Instagram", "instagram.com"),
    "whatsapp": ("WhatsApp", "WhatsApp", "whatsapp.com"),
    "telegram": ("Telegram", "Telegram", "telegram.org"),
    "stc": ("STC السعودية", "STC Saudi", "stc.com.sa"),
    "stcpay": ("STC Pay", "STC Pay", "stcpay.com.sa"),
    "absher": ("منصة أبشر", "Absher Platform", "absher.sa"),
    "nafath": ("منصة نفاذ", "Nafath National Platform", "iam.gov.sa"),
    "tawakkalna": ("تطبيق توكلنا", "Tawakkalna App", "tawakkalna.sdaia.gov.sa"),
}

SUSPICIOUS_KEYWORDS_AR = {
    "verify": "تأكيد أو تحديث البيانات",
    "verification": "التحقق من الحساب",
    "login": "تسجيل الدخول",
    "secure": "ادعاء التوثيق الأمني",
    "account": "الحساب البنكي",
    "update": "طلب تحديث معلومات",
    "card": "بطاقة الصراف/الائتمان",
    "bank": "البيانات البنكية",
    "wallet": "المحفظة الرقمية",
    "password": "كلمة المرور",
    "reset": "إعادة تعيين البيانات",
    "reward": "ادعاء جوائز أو مكافآت",
    "prize": "مكافأة أو جائزة مالية",
    "gift": "هدية ترويجية",
}


def _local_explanation(
    classification: str,
    language: str = "ar",
    input_value: str = "",
    evidence: dict | None = None,
) -> dict:
    from urllib.parse import urlsplit
    import tldextract

    is_ar = language == "ar"
    evidence = evidence or {}
    ml_evidence = evidence.get("ml", {})
    vt_evidence = evidence.get("virustotal", {})

    url_str = (input_value or "").strip()
    candidate = url_str if "://" in url_str else "http://" + url_str
    try:
        parsed = urlsplit(candidate)
        host = parsed.hostname or url_str
    except Exception:
        host = url_str

    extractor = tldextract.TLDExtract(suffix_list_urls=())
    ext = extractor(host)
    registered_domain = f"{ext.domain}.{ext.suffix}".lower() if ext.domain and ext.suffix else host.lower()
    suffix = f".{ext.suffix}".lower() if ext.suffix else ""
    full_url_lower = url_str.lower()

    reasons = []
    matched_brand_ar = None
    matched_brand_en = None
    official_domain = None

    # 1. Brand Impersonation Check
    for key, (name_ar, name_en, off_dom) in KNOWN_BRANDS.items():
        if key in full_url_lower:
            matched_brand_ar = name_ar
            matched_brand_en = name_en
            official_domain = off_dom
            if registered_domain != off_dom and not host.endswith("." + off_dom):
                if is_ar:
                    reasons.append(f"انتحال صفة جهة رسمية: الرابط يحاكي اسم ({name_ar}) بينما النطاق الرسمي المعتمد هو ({off_dom}).")
                else:
                    reasons.append(f"Brand Impersonation Risk: Link mimics ({name_en}) while official domain is ({off_dom}).")
            break

    # 2. Typosquatting Check
    if any(spoof in host for spoof in ["paypa1", "googl3", "micros0ft", "app1e", "amaz0n"]):
        if is_ar:
            reasons.append("تزوير النطاق (Typosquatting): تم استبدال بعض الحروف بأرقام لخداع المستخدم وإظهار الرابط كأنه موقع رسمي.")
        else:
            reasons.append("Typosquatting Detected: Character substitution (numbers for letters) used to deceive users.")

    # 3. Suspicious Phishing Keywords Check
    found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS_AR.keys() if kw in full_url_lower]
    if found_keywords and classification in {"DANGEROUS", "SUSPICIOUS"}:
        kw_str = ", ".join(f"'{kw}'" for kw in found_keywords[:3])
        if is_ar:
            reasons.append(f"استخدام كلمات احتيالية استدراجية: يحتوي الرابط على مصطلحات مثل ({kw_str}) لاستدراج المستخدم لإدخال معلومات بنكية أو شخصية.")
        else:
            reasons.append(f"Deceptive Keywords: URL contains keywords ({kw_str}) designed to solicit sensitive data.")

    # 4. High-Risk TLD Suffix Check
    if suffix in {".xyz", ".top", ".info", ".site", ".online", ".work", ".vip", ".cc", ".icu", ".club", ".tk", ".ml", ".ga", ".cf", ".gq"} and classification in {"DANGEROUS", "SUSPICIOUS"}:
        if is_ar:
            reasons.append(f"امتداد نطاق عالي المخاطر ({suffix}): يُستخدم هذا الامتداد بكثرة في الحملات الاحتيالية والمواقع المزيفة.")
        else:
            reasons.append(f"High-Risk TLD Extension ({suffix}): Commonly associated with phishing and untrusted domains.")

    # 5. ML Model Feature Probability Signal
    ml_prob = ml_evidence.get("phishing_prob")
    if ml_prob is not None and float(ml_prob) >= 0.40:
        prob_pct = round(float(ml_prob) * 100, 1)
        if is_ar:
            reasons.append(f"تحليل نموذج التعلم الآلي (ML): أكد المحرك وجود أنماط خطورة عالية بنسبة احتمالية احتيال ({prob_pct}%).")
        else:
            reasons.append(f"Machine Learning Analysis: Detected high-risk structural features with phishing probability ({prob_pct}%).")

    # 6. VirusTotal Multi-Engine Evidence
    vt_malicious = int(vt_evidence.get("malicious", 0) or 0)
    vt_suspicious = int(vt_evidence.get("suspicious", 0) or 0)
    if vt_malicious > 0 or vt_suspicious > 0:
        total_flags = vt_malicious + vt_suspicious
        if is_ar:
            reasons.append(f"فحص المحركات العالمية (VirusTotal): رصدت {total_flags} محركات حماية أمنية مؤشرات خطر ومشتبه بها.")
        else:
            reasons.append(f"Global VirusTotal Engines: Flagged by {total_flags} security engines as malicious or suspicious.")

    # Fallback default reason if reasons array is still empty
    if not reasons:
        if classification in {"DANGEROUS", "SUSPICIOUS"}:
            if is_ar:
                reasons.append("تم رصد مؤشرات خطورة أمنية غير اعتيادية في هيكلية النطاق والبيانات الوصفية للرابط.")
            else:
                reasons.append("Detected unusual security risk indicators in domain structure and metadata.")
        else:
            if is_ar:
                reasons.append("نطاق معتمد وموثوق خالٍ من مؤشرات التهديد السيبراني.")
            else:
                reasons.append("Verified trusted domain with no security threat indicators.")

    display_target = host if host else "الرابط"
    if classification == "DANGEROUS":
        if is_ar:
            summary = f"تحذير خطير: الرابط '{display_target}' ينطوي على مؤشرات احتيال وتهديد إلكتروني عالية. يُنصح بعدم التفاعل معه إطلاقاً."
            recommendation = "تجنب النقر على الرابط أو إدخال أي كلمات مرور أو معلومات بنكية أو رموز تحقق (OTP)."
        else:
            summary = f"High Threat Warning: URL '{display_target}' exhibits strong malicious or phishing indicators."
            recommendation = "Avoid clicking or entering any credentials, banking details, or OTP codes."
    elif classification == "SUSPICIOUS":
        if is_ar:
            summary = f"رابط مشبوه: الرابط '{display_target}' يحتوي على مؤشرات تستدعي الحذر؛ يرجى التأكد من المصدر قبل التفاعل."
            recommendation = "تحقق من المصدر الرسمي للرسالة وتجنب إدخال أي بيانات حساسة."
        else:
            summary = f"Suspicious Link: URL '{display_target}' contains potential risk factors requiring caution."
            recommendation = "Verify the official source and avoid entering sensitive information."
    elif classification == "SAFE":
        if is_ar:
            summary = f"الرابط آمن وموثوق: ينتمي '{display_target}' إلى نطاق موثوق معتمد وتأكدت سلامته عبر محركات الفحص."
            recommendation = "يمكنك التصفح والمتابعة بأمان."
        else:
            summary = f"Safe Link: URL '{display_target}' belongs to a trusted domain verified by security engines."
            recommendation = "You can proceed safely."
    else:
        if is_ar:
            summary = f"تعذر التحقق بدقة من الرابط '{display_target}'. يرجى توخي الحذر."
            recommendation = "أعد المحاولة لاحقاً أو تحقق من المصدر مباشرة."
        else:
            summary = f"Inconclusive result for URL '{display_target}'. Proceed with caution."
            recommendation = "Verify through an official channel."

    claimed_sender = matched_brand_ar if (matched_brand_ar and is_ar) else (matched_brand_en if matched_brand_en else ("جهة غير معروفة" if is_ar else "Unverified Entity"))
    official_dom_str = official_domain if official_domain else ("غير متاح" if is_ar else "N/A")

    lure_str = "ادعاء إيقاف حساب/طلب تحديث بطاقات" if is_ar else "Bank account/card update lure"
    if "prize" in full_url_lower or "reward" in full_url_lower or "مبروك" in full_url_lower:
        lure_str = "ادعاء فوز بجائزة أو مكافأة مالية" if is_ar else "Fake prize/reward claim"

    auth_status = "احتيالية (Fake SMS)" if classification == "DANGEROUS" else "مشبوهة (Unverified)" if classification == "SUSPICIOUS" else "رسمية (Official SMS)"

    return {
        "summary": summary,
        "claimed_sender": claimed_sender,
        "official_domain": official_dom_str,
        "lure_type": lure_str,
        "authenticity_status": auth_status,
        "reasons": reasons,
        "recommendation": recommendation,
        "provider": "TEMPLATE",
    }
