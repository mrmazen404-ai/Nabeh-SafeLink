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
    result = _sanitize_official_portal_url(result, input_value, input_value)
    result["provider"] = f"{provider} ({model_name})"
    return result


def _sanitized_local_explanation(classification: str, language: str, input_value: str, evidence: dict) -> dict:
    local = _local_explanation(classification, language, input_value=input_value, evidence=evidence)
    return _sanitize_official_portal_url(local, input_value, input_value)


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

# Resilient multi-tier model cascade ordered from latest high-speed models to bedrock versions
PRIMARY_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-flash-latest",
]

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
    Employs a resilient multi-tier model fallback ladder with zero-downtime local fallback.
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
        return _sanitized_local_explanation(classification, language, input_value, evidence)

    gemini_client = _get_client()
    if gemini_client is None:
        log_event(logger, logging.WARNING, "gemini_client_unavailable", operation_id=operation_id)
        return _sanitized_local_explanation(classification, language, input_value, evidence)

    # Multi-tier model fallback cascade: iterates through every model until a successful response
    for model_name in PRIMARY_MODELS:
        log_event(logger, logging.INFO, "gemini_model_attempt_started", operation_id=operation_id, model=model_name, mode="search")

        # Mode 1: Search Grounded Generation
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

        # Mode 2: Standard Gemini JSON Generation
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
    return _sanitized_local_explanation(classification, language, input_value, evidence)


SMS_SYSTEM_INSTRUCTION = """
You are a senior cybersecurity AI research analyst specializing in SMS Smishing, Social Engineering, and Fraud Detection for Nabeh SafeLink (نابه).
Your mission is to read and comprehend the given SMS text message, perform real-world research (including Google search grounding if available) to verify claimed organizations, active scam alerts, and official domains versus fraudulent spoofing, AND PROVIDE A STEP-BY-STEP ACTION & GUIDANCE PLAN FOR THE USER.

Cybersecurity Analysis & Guidance Rules:
1. Normal, friendly, everyday greetings, family messages, or benign queries (e.g. "السلام عليكم", "كيف حالك", "صباح الخير", "شكرا لك", "متى نلتقي") MUST be evaluated as SAFE (100% safe, 0.0 fraud probability, classification SAFE).
2. Fraudulent lures (bank account suspensions, OTP theft, fake prize claims, urgent traffic fines, impersonating official Saudi portals like Al Rajhi, SNB, Absher, Nafath, Tawakkalna, SPL/Post, DHL, Aramex) MUST be classified as DANGEROUS or SUSPICIOUS based on threat severity.
3. Perform research and guidance to identify:
   - "claimed_sender": The official entity or brand mentioned/impersonated in the message in requested language.
   - "official_domain": The verified true official registered domain for that organization (e.g., "alrajhibank.com.sa", "absher.sa", "iam.gov.sa").
   - "official_portal_url": The exact official HTTPS website/portal URL where the user can safely log in or check their status directly (e.g. "https://www.alrajhibank.com.sa", "https://www.absher.sa", "https://iam.gov.sa").
   - "claim_verdict_explanation": A clear statement explaining if the claim/lure is a complete hoax or fabrication with no basis in truth (e.g., "ادعاء كاذب لا أساس له من الصحة؛ الجهات الرسمية لا تصدر طلبات تحديث بيانات نصية إطلاقاً").
   - "lure_type": The social engineering psychological tactic used (e.g., "ادعاء إيقاف حساب بنكي", "ادعاء طرد بريدي معلق", "تأكيد بطاقة صراف").
   - "authenticity_status": Official verdict status in requested language (e.g. "احتيالية مزيفة (Fake Smishing SMS)", "مشبوهة غير موثوقة", "رسمية وحقيقية").
   - "action_plan_steps": A numbered, actionable step-by-step guidance plan in requested language telling the user exactly what to do safely (e.g., ["1. تجنب النقر على أي رابط أو التواصل مع الرقم المرسل.", "2. الدخول المباشر إلى المنصة الرسمية المعتمدة بشكل مستقل.", "3. الإبلاغ عن الرسالة الاحتيالية فوراً للرقم الموحد (330330)."]).
4. If an embedded URL is present in the SMS text, synthesize the link's threat evidence (ML probability & VirusTotal engine flags) together with the SMS context lure and real-world web research findings.

Respond ONLY in valid JSON matching this exact structure:
{
  "classification": "SAFE" | "SUSPICIOUS" | "DANGEROUS",
  "confidence": float between 0.5 and 1.0,
  "fraud_probability": float between 0.0 and 1.0,
  "urgency_pressure_score": integer between 0 and 100 assessing artificial time pressure/urgency,
  "credential_theft_score": integer between 0 and 100 assessing requests for OTP/passwords/IDs/sensitive data,
  "identity_spoofing_score": integer between 0 and 100 assessing impersonation of official brands/entities,
  "claimed_sender": "string describing claimed organization/sender in requested language",
  "official_domain": "string stating official domain name (e.g. alrajhibank.com.sa)",
  "official_portal_url": "string stating exact official portal HTTPS URL (e.g. https://www.absher.sa)",
  "claim_verdict_explanation": "string explaining why claim is false or true in requested language",
  "lure_type": "string describing lure tactic in requested language",
  "authenticity_status": "string describing authenticity verdict in requested language",
  "summary": "Clear 1-2 sentence summary explaining the AI research analysis in requested language for non-technical users",
  "reasons": ["Key research reason 1 in requested language", "Key research reason 2 in requested language", "Key research reason 3 in requested language"],
  "recommendation": "Practical actionable security advice in requested language",
  "action_plan_steps": ["Step 1 in requested language", "Step 2 in requested language", "Step 3 in requested language"]
}
"""


async def analyze_sms_message(
    text_content: str,
    extracted_url: str = "",
    evidence: dict | None = None,
    language: str = "ar",
) -> dict:
    """
    Performs AI-driven SMS text message smishing analysis using Google Gemini API.
    Employs Google Search Grounding to research real-world entities, active scams, and official domains.
    Provides actionable guidance and step-by-step safe action plan for the user.
    """
    lang_name = "Arabic" if language == "ar" else "English"
    evidence = evidence or {}
    operation_id = resource_id(text_content)
    log_event(logger, logging.INFO, "gemini_sms_analysis_started", operation_id=operation_id, language=language)

    prompt = f"""
SMS Message Text: "{text_content[:600]}"
Embedded URL (if any): "{extracted_url or 'None'}"
Requested Explanation Language: {lang_name}
Link Analysis Evidence:
{json.dumps(evidence, ensure_ascii=False)}

Cybersecurity Research Instructions:
1. Research and verify the true official entity, official domain, and official portal URL for any organization mentioned in the SMS message.
2. Evaluate if the message uses deceptive lures, account suspension threats, fake package delivery claims, or OTP theft attempts. Explain if the claim is a complete hoax/fabrication.
3. Create a step-by-step actionable safety guidance plan telling the user exactly how to proceed safely.
4. Synthesize the embedded link's threat indicators (if any) together with the message text intent.

Respond ONLY in valid JSON matching the requested structure.
"""

    current_key = _get_api_key()
    gemini_client = _get_client() if current_key else None

    if gemini_client:
        for model_name in PRIMARY_MODELS:
            log_event(logger, logging.INFO, "gemini_sms_model_attempt_started", operation_id=operation_id, model=model_name)

            # Mode 1: Search Grounded Generation for SMS Research
            try:
                response = await gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SMS_SYSTEM_INSTRUCTION,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.1,
                    )
                )
                text = response.text.strip() if response.text else ""
                text_clean = re.sub(r'^```json\s*', '', text)
                text_clean = re.sub(r'\s*```$', '', text_clean)

                parsed = json.loads(text_clean)
                parsed["provider"] = f"GEMINI_SEARCH ({model_name})"
                parsed = _sanitize_official_portal_url(parsed, text_content, extracted_url)
                log_event(logger, logging.INFO, "gemini_sms_analysis_succeeded", operation_id=operation_id, model=model_name, mode="search")
                return parsed
            except Exception as error:
                log_event(logger, logging.WARNING, "gemini_sms_search_attempt_failed", operation_id=operation_id, model=model_name, error_type=safe_error(error))

            # Mode 2: Standard JSON Schema Generation
            try:
                response = await gemini_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SMS_SYSTEM_INSTRUCTION,
                        response_mime_type="application/json",
                        temperature=0.1,
                    )
                )
                text = response.text.strip() if response.text else ""
                text_clean = re.sub(r'^```json\s*', '', text)
                text_clean = re.sub(r'\s*```$', '', text_clean)

                parsed = json.loads(text_clean)
                parsed["provider"] = f"GEMINI_AI ({model_name})"
                parsed = _sanitize_official_portal_url(parsed, text_content, extracted_url)
                log_event(logger, logging.INFO, "gemini_sms_analysis_succeeded", operation_id=operation_id, model=model_name, mode="json")
                return parsed
            except Exception as error:
                log_event(logger, logging.WARNING, "gemini_sms_json_attempt_failed", operation_id=operation_id, model=model_name, error_type=safe_error(error))
                continue

    return _sanitize_official_portal_url(_local_sms_analysis(text_content, extracted_url, language, evidence), text_content, extracted_url)


def _matched_known_brand_domain(text_content: str, extracted_url: str) -> str | None:
    haystack = f"{text_content} {extracted_url}".lower()
    for key, (name_ar, name_en, off_dom) in KNOWN_BRANDS.items():
        aliases = (key, name_en.lower())
        has_english_alias = any(
            re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", haystack)
            for alias in aliases if alias
        )
        has_domain = bool(re.search(rf"(?<![a-z0-9.-]){re.escape(off_dom.lower())}(?![a-z0-9.-])", haystack))
        if has_english_alias or name_ar in haystack or has_domain:
            return off_dom.lower()
    return None


def _sanitize_official_portal_url(parsed: dict, text_content: str, extracted_url: str) -> dict:
    if not isinstance(parsed, dict):
        return parsed

    matched_official_domain = _matched_known_brand_domain(text_content, extracted_url)
    no_www_domains = {"iam.gov.sa", "tawakkalna.sdaia.gov.sa"}
    matched_official_portal = (
        f"https://{matched_official_domain}" if matched_official_domain in no_www_domains
        else f"https://www.{matched_official_domain}" if matched_official_domain
        else None
    )

    if matched_official_portal:
        parsed["official_portal_url"] = matched_official_portal
        parsed["official_domain"] = matched_official_domain
    else:
        # Never pass through an unverified model-suggested portal or domain.
        parsed["official_portal_url"] = "غير متاح"
        parsed["official_domain"] = "غير متاح"

    return parsed


def _local_sms_analysis(text_content: str, extracted_url: str = "", language: str = "ar", evidence: dict | None = None) -> dict:
    is_ar = language == "ar"
    evidence = evidence or {}

    safe_greetings = (
        "السلام عليكم", "سلام عليكم", "صباح الخير", "مساء الخير",
        "مرحبا", "أهلا", "اهلاً", "شكرا", "شكراً", "كيف حالك",
        "متى الموعد", "الله يعطيك العافية", "جزاك الله خير",
        "عيد مبارك", "كل عام وأنتم بخير", "الحمد لله", "هلا"
    )
    phishing_keywords = (
        "حسابك", "البنك", "تجميد", "تحديث", "كلمة المرور", "بطاقة", "جائزة",
        "مبروك", "الفوز", "رمز", "إيقاف", "الراجحي", "الأهلي", "الإنماء",
        "سداد", "غرامة", "ربح", "تأكيد", "انقر", "اضغط"
    )
    has_greeting = any(g in text_content for g in safe_greetings)
    has_phishing_keywords = any(word in text_content.lower() or word in text_content for word in phishing_keywords)
    has_url = bool(extracted_url)

    if not has_url and (has_greeting or not has_phishing_keywords or len(text_content.strip()) <= 120):
        classification = "SAFE"
        confidence = 0.99 if (has_greeting or not has_phishing_keywords) else 0.95
        fraud_prob = 0.01
        lure_type = "رسالة عادية آمنة" if is_ar else "Safe Normal Message"
        summary = "الرسالة عبارة عن تواصل شخصي أو نص عادي خالي من أي مؤشرات احتيال أو روابط مشبوهة." if is_ar else "Innocent message containing no fraudulent lures or suspicious links."
        reasons = [
            "خلو الرسالة من روابط استدراجية أو طلبات إدخال بيانات بنكية." if is_ar else "Message contains no phishing links or requests for credentials.",
            "نص الرسالة خالي من الأنماط والكلمات الاحتيالية المشبوهة." if is_ar else "Message contains no suspicious phishing patterns."
        ]
        recommendation = "رسالة آمنة لا تتطلب أي إجراء." if is_ar else "Safe message requiring no action."
        official_portal = "غير متاح"
        claim_verdict = "رسالة طبيعية لا تنطوي على ادعاءات مالية أو أمنية." if is_ar else "Normal message with no financial or security claims."
        action_steps = [
            "يمكنك التفاعل مع الرسالة والتواصل كالمعتاد." if is_ar else "You can interact and communicate normally."
        ]
    else:
        url_verdict = evidence.get("url_combined_verdict", {})
        classification = url_verdict.get("classification", "SUSPICIOUS") if has_url else "SUSPICIOUS"
        confidence = 0.85
        fraud_prob = 0.85 if classification == "DANGEROUS" else (0.50 if classification == "SUSPICIOUS" else 0.05)
        lure_type = "ادعاء تحديث بيانات/رابط مضمن" if is_ar else "Data update/embedded link lure"
        summary = "تحتوي الرسالة على رابط أو مصطلحات تستدعي الحذر والتحقق قبل التفاعل." if is_ar else "Message contains a link or terms requiring caution before interacting."
        reasons = [
            "وجود رابط مضمن يتطلب الفحص الأمني عبر المحركات." if is_ar else "Embedded URL detected requiring security audit.",
        ]
        recommendation = "تحقق من المصدر الرسمي للرسالة ولا تدخل بياناتك الحسّاسة." if is_ar else "Verify the official source and do not enter sensitive info."
        
        # Match against known verified brands; strictly return "غير متاح" if no known brand is found
        matched_portal = None
        matched_domain = _matched_known_brand_domain(text_content, extracted_url)
        if matched_domain:
            no_www_domains = {"iam.gov.sa", "tawakkalna.sdaia.gov.sa"}
            matched_portal = f"https://{matched_domain}" if matched_domain in no_www_domains else f"https://www.{matched_domain}"

        official_portal = matched_portal or "غير متاح"
        claim_verdict = "ادعاء مريب يحاكي أسلوب الاستدراج لحث المستخدم على التفاعل الفوري." if is_ar else "Suspicious lure attempt seeking immediate interaction."
        action_steps = [
            "تجنب النقر على أي رابط مرفق أو الاتصال بالرقم المرسل." if is_ar else "Avoid clicking links or calling the sender.",
            "قم بالدخول المباشر للمنصة أو التطبيق الرسمي من خلال متصفحك أو متجر التطبيقات." if is_ar else "Access the official portal or app directly.",
            "إعادة إرسال الرسالة إلى الرقم الموحد للإبلاغ عن الاحتيال (330330) في السعودية." if is_ar else "Report the scam message to official anti-fraud numbers."
        ]

    # Calculate social engineering risk scores dynamically (0-100)
    urgency_words = ("ساعة", "ساعات", "فوري", "عاجل", "الآن", "تجميد", "إيقاف", "مهلة", "خلال", "فورا", "فوراً", "انتهى")
    urgency_count = sum(1 for w in urgency_words if w in text_content)
    if urgency_count >= 2:
        urgency_score = min(98, 80 + urgency_count * 8)
    elif urgency_count == 1:
        urgency_score = 65
    elif has_phishing_keywords:
        urgency_score = 45
    else:
        urgency_score = 5

    credential_words = ("otp", "رمز", "كلمة المرور", "بطاقة", "هوية", "الهويه", "حسابك", "تسجيل", "بيانات", "السرية", "تحويل")
    credential_count = sum(1 for w in credential_words if w in text_content.lower())
    if credential_count >= 2:
        credential_score = min(98, 75 + credential_count * 8)
    elif credential_count == 1:
        credential_score = 60
    elif has_url and has_phishing_keywords:
        credential_score = 50
    else:
        credential_score = 2

    matched_brand = bool(_matched_known_brand_domain(text_content, extracted_url))

    if matched_brand:
        spoofing_score = 98 if (has_phishing_keywords or has_url) else 80
    elif has_phishing_keywords:
        spoofing_score = 60
    else:
        spoofing_score = 1

    return {
        "classification": classification,
        "confidence": confidence,
        "fraud_probability": fraud_prob,
        "urgency_pressure_score": urgency_score,
        "credential_theft_score": credential_score,
        "identity_spoofing_score": spoofing_score,
        "lure_type": lure_type,
        "summary": summary,
        "reasons": reasons,
        "recommendation": recommendation,
        "official_portal_url": official_portal,
        "claim_verdict_explanation": claim_verdict,
        "action_plan_steps": action_steps,
        "provider": "LOCAL_AI_RULES"
    }


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
    "kuraimi": ("بنك الكريمي", "Kuraimi Bank", "kuraimibank.com"),
    "kuraimibank": ("بنك الكريمي", "Kuraimi Bank", "kuraimibank.com"),
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
    matched_domain = _matched_known_brand_domain("", url_str)
    for _, (name_ar, name_en, off_dom) in KNOWN_BRANDS.items():
        if matched_domain and off_dom.lower() == matched_domain:
            matched_brand_ar = name_ar
            matched_brand_en = name_en
            official_domain = off_dom
            if registered_domain != off_dom.lower() and not host.endswith("." + off_dom.lower()):
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
