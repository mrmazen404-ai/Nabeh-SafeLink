"""Scan processing with strict guest isolation and explicit UNKNOWN outcomes."""

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app.db.supabase_client import supabase
from app.gemini.client import generate_explanation
from app.ml.predictor import predict_url
from app.virustotal.client import check_url_virustotal

logger = logging.getLogger(__name__)

ARABIC_PHISHING_KEYWORDS = (
    "حسابك", "البنك", "تجميد", "تحديث", "كلمة المرور", "بطاقة", "جائزة",
    "مبروك", "الفوز", "رمز", "إيقاف", "الراجحي", "الأهلي", "الإنماء",
    "سداد", "غرامة", "ربح", "تأكيد", "انقر", "اضغط",
)


class ScanPersistenceError(Exception):
    """Raised when a registered user's scan cannot be persisted completely."""


class ScanService:
    @staticmethod
    def extract_url_from_text(text: str) -> str:
        match = re.search(r"https?://[^\s]+|www\.[^\s]+", text)
        return match.group(0) if match else ""

    @staticmethod
    def analyze_text_phishing(text: str, has_embedded_url: bool = False) -> dict:
        text_lower = text.lower()
        matches = [word for word in ARABIC_PHISHING_KEYWORDS if word in text_lower or word in text]
        if len(matches) >= 3:
            classification, confidence = ("DANGEROUS", 0.85) if has_embedded_url else ("SUSPICIOUS", 0.70)
        elif matches:
            classification, confidence = "SUSPICIOUS", 0.65
        else:
            # Absence of these keywords is not evidence that a message is safe.
            classification, confidence = "UNKNOWN", None
        return {
            "classification": classification,
            "confidence": confidence,
            "keyword_matches": matches,
            "match_count": len(matches),
            "source": "SMS_TEXT_ANALYZER",
        }

    @staticmethod
    def _merge_text_signal(combined: dict, text_result: dict) -> dict:
        text_class = text_result.get("classification")
        if text_class in {"DANGEROUS", "SUSPICIOUS"} and combined.get("classification") in {"SAFE", "UNKNOWN"}:
            return {
                "classification": text_class,
                "confidence": text_result.get("confidence"),
                "weighted_score": combined.get("weighted_score"),
                "source": "LOCAL_TEXT_RULES + URL_ANALYSIS",
            }
        return combined

    @staticmethod
    def combine_scan_results(vt_result: dict, ml_result: dict) -> dict:
        """Combine only validated evidence; missing/unknown scanners never produce SAFE."""
        vt_result = vt_result or {}
        ml_result = ml_result or {}
        vt_status = str(vt_result.get("status", "UNKNOWN")).upper()
        try:
            vt_malicious = max(0, int(vt_result.get("malicious", 0) or 0))
            vt_suspicious = max(0, int(vt_result.get("suspicious", 0) or 0))
            vt_harmless = max(0, int(vt_result.get("harmless", 0) or 0))
            vt_total = max(0, int(vt_result.get("total_engines", 0) or 0))
        except (TypeError, ValueError):
            vt_malicious = vt_suspicious = vt_harmless = vt_total = 0
            vt_status = "UNKNOWN"
        has_vt = vt_total > 0 and vt_status in {"SAFE", "SUSPICIOUS", "DANGEROUS"}

        ml_class = str(ml_result.get("classification", "UNKNOWN")).upper()
        ml_prob = ml_result.get("phishing_prob")
        try:
            ml_prob = float(ml_prob)
            has_ml = ml_class in {"SAFE", "SUSPICIOUS", "DANGEROUS"} and 0.0 <= ml_prob <= 1.0
        except (TypeError, ValueError):
            ml_prob, has_ml = None, False
        if ml_result.get("source") == "WHITELIST":
            has_ml = False

        # Confirmed high-signal detections take precedence over safe/unknown output.
        if vt_malicious >= 3 or (has_ml and ml_class == "DANGEROUS" and ml_prob >= 0.60):
            return {"classification": "DANGEROUS", "confidence": max(0.85, float(ml_prob or 0)), "weighted_score": float(ml_prob or 1), "source": "RISK_SIGNAL"}
        if vt_malicious >= 1 or vt_suspicious >= 2:
            return {"classification": "SUSPICIOUS", "confidence": 0.65, "weighted_score": None, "source": "VIRUSTOTAL_SIGNAL"}

        if not has_vt and not has_ml:
            return {"classification": "UNKNOWN", "confidence": None, "weighted_score": None, "source": "INSUFFICIENT_EVIDENCE"}

        if has_vt and has_ml:
            vt_score = min(1.0, (vt_malicious + (vt_suspicious * 0.5)) / max(1.0, vt_total * 0.10))
            score = (0.55 * vt_score) + (0.45 * ml_prob)
            if score >= 0.60:
                classification = "DANGEROUS"
            elif score >= 0.35 or vt_status == "SUSPICIOUS" or ml_class == "SUSPICIOUS":
                classification = "SUSPICIOUS"
            else:
                classification = "SAFE"
            confidence = round(max(score, 0.65) if classification != "SAFE" else 1.0 - score, 4)
            return {"classification": classification, "confidence": confidence, "weighted_score": round(score, 4), "source": "HYBRID_DECISION_MATRIX (VT + ML)"}

        if has_vt:
            if vt_status == "SAFE" and vt_harmless > 0 and vt_malicious == 0 and vt_suspicious == 0:
                classification = "SAFE"
            else:
                classification = "SUSPICIOUS" if vt_status == "SAFE" else vt_status
            return {"classification": classification, "confidence": float(vt_result.get("confidence") or 0.65), "weighted_score": None, "source": "VIRUSTOTAL"}

        return {
            "classification": ml_class,
            "confidence": float(ml_result.get("confidence") or 0.65),
            "weighted_score": ml_prob,
            "source": f"ML_MODEL ({ml_result.get('source', 'LOCAL')})",
        }

    @staticmethod
    def _local_explanation(classification: str, language: str) -> dict:
        english = language == "en"
        text = {
            "SAFE": ("لم تظهر مؤشرات خطر في التحليل المحلي." if not english else "No risk indicators were found by local analysis."),
            "SUSPICIOUS": ("ظهرت مؤشرات تستدعي الحذر والتحقق من المصدر." if not english else "Indicators require caution and source verification."),
            "DANGEROUS": ("ظهرت مؤشرات خطر قوية؛ لا تفتح الرابط ولا تشارك بياناتك." if not english else "Strong risk indicators were found; do not open or share data."),
            "UNKNOWN": ("تعذر التحقق محلياً؛ لا تعتبر النتيجة آمنة." if not english else "Local verification was inconclusive; do not treat this as safe."),
        }.get(classification, "تعذر التحقق محلياً.")
        recommendation = {
            "SAFE": "تابع بحذر." if not english else "Continue cautiously.",
            "SUSPICIOUS": "تحقق من المصدر قبل التفاعل." if not english else "Verify the source before interacting.",
            "DANGEROUS": "تجنب فتح الرابط أو إدخال بياناتك." if not english else "Avoid opening the link or entering data.",
            "UNKNOWN": "أعد المحاولة لاحقاً أو تحقق عبر مصدر موثوق." if not english else "Try again later or verify with a trusted source.",
        }.get(classification, "توخ الحذر." if not english else "Exercise caution.")
        return {"summary": text, "reasons": [], "recommendation": recommendation, "provider": "LOCAL_RULES"}

    @classmethod
    async def process_guest_scan(cls, input_type: str, raw_input: str, language: str = "ar") -> dict:
        """Guest scans use local analysis only: no database and no outbound provider calls."""
        extracted_url = cls.extract_url_from_text(raw_input)
        target_url = extracted_url if extracted_url else raw_input
        vt_result = {"status": "NOT_REQUESTED", "malicious": 0, "suspicious": 0, "harmless": 0, "total_engines": 0}
        if input_type == "URL" or extracted_url:
            try:
                ml_result = predict_url(target_url)
            except Exception:
                logger.warning("guest_local_analysis_failed")
                ml_result = {"classification": "UNKNOWN", "source": "LOCAL_ERROR"}
            combined = cls.combine_scan_results(vt_result, ml_result)
            if input_type == "TEXT" and extracted_url:
                combined = cls._merge_text_signal(combined, cls.analyze_text_phishing(raw_input, has_embedded_url=True))
        else:
            ml_result = cls.analyze_text_phishing(raw_input)
            combined = {"classification": ml_result["classification"], "confidence": ml_result["confidence"], "weighted_score": None, "source": "TEXT_SMS_ANALYZER"}

        return {
            "is_guest": True,
            "scan_id": None,
            "input_value": raw_input,
            "extracted_url": extracted_url or None,
            "classification": combined["classification"],
            "confidence": combined["confidence"],
            "source": combined["source"],
            "explanation": cls._local_explanation(combined["classification"], language),
            "virustotal": vt_result,
            "ml_model": {
                "classification": ml_result.get("classification", "UNKNOWN"),
                "confidence": ml_result.get("confidence"),
                "phishing_prob": ml_result.get("phishing_prob"),
                "source": ml_result.get("source", "N/A"),
            },
        }

    @staticmethod
    def _mask_input(input_type: str, raw_input: str) -> str:
        if input_type == "TEXT":
            return "[TEXT REDACTED]"
        candidate = raw_input if "://" in raw_input else "https://" + raw_input
        try:
            parsed = urlsplit(candidate)
            host = parsed.hostname or "[HOST REDACTED]"
            return f"{parsed.scheme}://{host}/[REDACTED]"
        except Exception:
            return "[URL REDACTED]"

    @classmethod
    async def process_authenticated_scan(cls, input_type: str, raw_input: str, user_id: str, language: str = "ar") -> dict:
        if not user_id:
            raise ScanPersistenceError("verified user ID required")
        extracted_url = cls.extract_url_from_text(raw_input)
        target_url = extracted_url if extracted_url else raw_input
        vt_result, ml_result = {}, {}

        if input_type == "URL" or extracted_url:
            try:
                vt_result = await check_url_virustotal(target_url)
            except Exception:
                logger.warning("authenticated_virustotal_failed")
                vt_result = {"status": "UNKNOWN"}
            try:
                ml_result = predict_url(target_url)
            except Exception:
                logger.warning("authenticated_ml_analysis_failed")
                ml_result = {"classification": "UNKNOWN"}
            combined = cls.combine_scan_results(vt_result, ml_result)
            if input_type == "TEXT" and extracted_url:
                combined = cls._merge_text_signal(combined, cls.analyze_text_phishing(raw_input, has_embedded_url=True))
        else:
            ml_result = cls.analyze_text_phishing(raw_input)
            combined = {"classification": ml_result["classification"], "confidence": ml_result["confidence"], "source": "TEXT_SMS_ANALYZER"}

        try:
            explanation = await generate_explanation(input_value=raw_input, classification=combined["classification"], language=language)
        except Exception:
            logger.warning("authenticated_explanation_failed")
            explanation = cls._local_explanation(combined["classification"], language)

        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            scan_data = {
                "user_id": user_id,
                "input_type": input_type,
                "input_value_masked": cls._mask_input(input_type, raw_input),
                "status": "COMPLETED",
                "classification": combined["classification"],
                "confidence_score": float(combined.get("confidence") or 0.0),
                "confidence_level": "HIGH" if (combined.get("confidence") or 0) >= 0.8 else "MEDIUM",
                "recommendation": explanation.get("recommendation", ""),
                "completed_at": now_iso,
            }
            saved = supabase.table("scans").insert(scan_data).execute()
            if not saved.data:
                raise RuntimeError("scan row not returned")
            scan_id = saved.data[0].get("id")
            if not scan_id:
                raise RuntimeError("scan ID not returned")

            explanation_data = {
                "scan_id": scan_id,
                "language": language,
                "summary": explanation.get("summary", ""),
                "reasons": explanation.get("reasons", []),
                "recommendation": explanation.get("recommendation", ""),
                "provider": explanation.get("provider", "TEMPLATE"),
            }
            supabase.table("scan_explanations").insert(explanation_data).execute()

            signals = []
            if vt_result.get("malicious", 0) > 0:
                signals.append({"scan_id": scan_id, "signal_code": "VT_MALICIOUS_DETECTION", "signal_label_en": "VirusTotal malicious detections", "signal_label_ar": "رصدت خدمة الفحص مؤشرات ضارة", "severity": 5, "source": "VIRUSTOTAL"})
            if ml_result.get("phishing_prob", 0) and ml_result.get("phishing_prob", 0) > 0.5:
                signals.append({"scan_id": scan_id, "signal_code": "ML_PHISHING_PROBABILITY", "signal_label_en": "Elevated model phishing score", "signal_label_ar": "مؤشر مرتفع لاحتمال التصيد", "severity": 4, "source": "LIGHTGBM_ML"})
            if signals:
                supabase.table("scan_signals").insert(signals).execute()
        except Exception:
            logger.error("authenticated_scan_persistence_failed")
            raise ScanPersistenceError("scan persistence failed") from None

        return {
            "is_guest": False,
            "scan_id": scan_id,
            "input_value": raw_input,
            "extracted_url": extracted_url or None,
            "classification": combined["classification"],
            "confidence": combined.get("confidence"),
            "source": combined["source"],
            "explanation": explanation,
            "virustotal": {
                "status": vt_result.get("status", "UNKNOWN"),
                "malicious": vt_result.get("malicious", 0),
                "suspicious": vt_result.get("suspicious", 0),
                "harmless": vt_result.get("harmless", 0),
                "total_engines": vt_result.get("total_engines", 0),
            },
            "ml_model": {
                "classification": ml_result.get("classification", "UNKNOWN"),
                "confidence": ml_result.get("confidence"),
                "phishing_prob": ml_result.get("phishing_prob"),
                "source": ml_result.get("source", "N/A"),
            },
        }

    @staticmethod
    async def get_recent_scans(limit: int = 50, user_id: str = None) -> list:
        if not user_id:
            raise ValueError("user_id is required")
        safe_limit = max(1, min(int(limit), 50))
        try:
            result = (
                supabase.table("scans")
                .select("id,input_type,input_value_masked,status,classification,confidence_score,confidence_level,created_at,completed_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(safe_limit)
                .execute()
            )
            return result.data or []
        except Exception:
            logger.error("scan_history_query_failed")
            raise
