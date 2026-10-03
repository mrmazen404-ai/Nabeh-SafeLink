"""
Gemini AI Client for Nabeh SafeLink
Provides non-blocking async security explanations using Google GenAI SDK (client.aio)
with structured JSON output and multi-model fallback resilience.
"""

import json
import re
import logging
from google import genai
from google.genai import types
from app.config import settings

client = None
logger = logging.getLogger(__name__)


def _get_client():
    global client
    if client is None and settings.GEMINI_API_KEY:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return client

# Models ordered by priority
PRIMARY_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]

SYSTEM_INSTRUCTION = """
You are a top-tier cybersecurity expert assistant for Nabeh SafeLink (نابه) fraud detection system.
Your job is to analyze URLs or text messages and provide clear, evidence-based threat explanations in valid JSON.
"""


async def generate_explanation(
    input_value: str,
    classification: str,
    language: str = "ar",
) -> dict:
    """
    Generates structured AI explanation asynchronously.
    Falls back gracefully to local template if API is unavailable or errors occur.
    """
    lang_name = "Arabic" if language == "ar" else "English"

    prompt = f"""
Input Value: {input_value[:300]}
Primary Security Classification: {classification}
Requested Explanation Language: {lang_name}

Respond ONLY in valid JSON matching this exact structure:
{{
  "summary": "Clear 1-2 sentence summary explaining the security classification in {lang_name}",
  "reasons": ["Key technical reason 1 in {lang_name}", "Key technical reason 2 in {lang_name}"],
  "recommendation": "Practical actionable security advice in {lang_name}"
}}
"""

    if not settings.GEMINI_API_KEY:
        logger.warning("gemini_provider_not_configured")
        return _local_explanation(classification, language)

    gemini_client = _get_client()
    if gemini_client is None:
        return _local_explanation(classification, language)

    # Try models in priority order
    for model_name in PRIMARY_MODELS:
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
                return {
                    "summary": parsed.get("summary", text[:300]),
                    "reasons": parsed.get("reasons", []),
                    "recommendation": parsed.get("recommendation", _default_rec(classification, language)),
                    "provider": f"GEMINI ({model_name})",
                }
            except json.JSONDecodeError:
                if text:
                    return {
                        "summary": text[:300],
                        "reasons": [],
                        "recommendation": _default_rec(classification, language),
                        "provider": f"GEMINI ({model_name})",
                    }

        except Exception:
            logger.warning("gemini_provider_request_failed")
            continue

    logger.warning("gemini_provider_fallback_used")
    return _local_explanation(classification, language)


def _default_rec(classification: str, language: str = "ar") -> str:
    recs = {
        "SAFE": {"ar": "يمكنك المتابعة والتصفح بأمان", "en": "You can proceed safely"},
        "SUSPICIOUS": {"ar": "تحقق من المصدر قبل إدخال أي بيانات", "en": "Verify the source before entering data"},
        "DANGEROUS": {"ar": "تجنب النقر أو مشاركة هذا الرابط", "en": "Avoid clicking or sharing this link"},
        "UNKNOWN": {"ar": "توخَّ الحذر وتجنب مشاركة بياناتك", "en": "Exercise caution and avoid sharing info"},
    }
    return recs.get(classification, recs["UNKNOWN"]).get(language, "Be cautious")


def _local_explanation(classification: str, language: str = "ar") -> dict:
    templates = {
        "SAFE": {
            "ar": "الرابط آمن. لم يتم اكتشاف أي تهديدات أو مؤشرات احتيال من قبل محركات الفحص.",
            "en": "URL is safe. No threats detected by security engines.",
        },
        "SUSPICIOUS": {
            "ar": "الرابط مشبوه! تم اكتشاف مؤشرات قد تشير إلى محاولة انتحال أو تصيد.",
            "en": "URL is suspicious! Potential risk indicators detected.",
        },
        "DANGEROUS": {
            "ar": "تحذير خطير! تم تصنيف الرابط كتهديد إلكتروني أو موقع تصيد احتيالي.",
            "en": "Warning! URL classified as malicious or phishing site.",
        },
        "UNKNOWN": {
            "ar": "تعذر تحديد التصنيف بدقة. توخَّ الحذر دائماً عند التعامل مع الرابط.",
            "en": "Classification unknown. Be cautious when interacting with this link.",
        },
    }

    return {
        "summary": templates.get(classification, templates["UNKNOWN"]).get(language, "Unknown"),
        "reasons": [],
        "recommendation": _default_rec(classification, language),
        "provider": "TEMPLATE",
    }
