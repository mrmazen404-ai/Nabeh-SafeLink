"""Scan processing with strict guest isolation and explicit UNKNOWN outcomes."""

import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from app.db.supabase_client import supabase
from app.observability import log_event, resource_id
from app.gemini.client import generate_explanation
from app.ml.predictor import predict_url
from app.virustotal.client import check_url_virustotal
from app.dashboard.realtime import manager

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
        """Combine 3-Stage Scan Results (Stage 1: ML, Stage 2: VirusTotal) into an accurate verdict.

        Core security principle: ML alone is NEVER sufficient for DANGEROUS classification.
        DANGEROUS requires either:
          (a) VirusTotal with 3+ malicious engines, OR
          (b) VirusTotal with 1-2 malicious AND ML corroboration (high confidence)
        """
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
        ml_source = str(ml_result.get("source", ""))
        ml_prob = ml_result.get("phishing_prob")
        try:
            ml_prob = float(ml_prob)
            has_ml = ml_class in {"SAFE", "SUSPICIOUS", "DANGEROUS"} and 0.0 <= ml_prob <= 1.0
        except (TypeError, ValueError):
            ml_prob, has_ml = None, False

        if ml_source == "WHITELIST":
            has_ml = False

        # ═══════════════════════════════════════════════════════════════════
        # TIER 0: Verified Safe Domain Whitelist
        # ═══════════════════════════════════════════════════════════════════
        if ml_source == "VERIFIED_SAFE_DOMAIN" and vt_malicious == 0:
            return {
                "classification": "SAFE",
                "confidence": 0.99,
                "weighted_score": 0.01,
                "source": "VERIFIED_SAFE_DOMAIN",
            }

        # ═══════════════════════════════════════════════════════════════════
        # TIER 1: DANGEROUS — requires STRONG evidence
        # ═══════════════════════════════════════════════════════════════════

        # Rule 1a: VirusTotal strong consensus (3+ engines flag as malicious)
        if vt_malicious >= 3:
            # Confidence scales with # of engines
            confidence = min(0.99, 0.85 + (vt_malicious - 3) * 0.02)
            return {
                "classification": "DANGEROUS",
                "confidence": round(confidence, 4),
                "weighted_score": 1.0,
                "source": f"VIRUSTOTAL_CONSENSUS ({vt_malicious} engines)",
            }

        # Rule 1b: VirusTotal moderate (1-2) + ML corroboration at high confidence
        if vt_malicious >= 1 and has_ml and ml_class == "DANGEROUS" and ml_prob >= 0.85:
            # Two independent signals agree
            confidence = min(0.95, 0.75 + (ml_prob - 0.85) * 1.5)
            return {
                "classification": "DANGEROUS",
                "confidence": round(confidence, 4),
                "weighted_score": round(ml_prob, 4),
                "source": f"DANGEROUS_CORROBORATED (VT:{vt_malicious} + ML:{ml_prob:.2f})",
            }

        # ═══════════════════════════════════════════════════════════════════
        # TIER 2: SUSPICIOUS — moderate evidence
        # ═══════════════════════════════════════════════════════════════════

        # Rule 2a: VirusTotal has malicious OR multiple suspicious signals
        if vt_malicious >= 1 or vt_suspicious >= 2:
            return {
                "classification": "SUSPICIOUS",
                "confidence": 0.65,
                "weighted_score": float(ml_prob or 0.5),
                "source": f"VIRUSTOTAL_SIGNAL (M:{vt_malicious}, S:{vt_suspicious})",
            }

        # Rule 2b: ML strong signal alone → maximum SUSPICIOUS (never DANGEROUS)
        if has_ml and ml_class == "DANGEROUS" and ml_prob >= 0.60:
            return {
                "classification": "SUSPICIOUS",
                "confidence": round(min(0.75, ml_prob * 0.9), 4),
                "weighted_score": round(ml_prob, 4),
                "source": "ML_SIGNAL_ONLY",
            }

        # Rule 2c: ML suspicious signal
        if has_ml and ml_class == "SUSPICIOUS":
            return {
                "classification": "SUSPICIOUS",
                "confidence": round(float(ml_prob or 0.55) * 0.8, 4),
                "weighted_score": round(float(ml_prob or 0.5), 4),
                "source": "ML_SUSPICIOUS_SIGNAL",
            }

        # ═══════════════════════════════════════════════════════════════════
        # TIER 3: SAFE — requires positive evidence from both sources
        # ═══════════════════════════════════════════════════════════════════

        # Rule 3a: Both VT and ML agree on SAFE
        if has_vt and has_ml and vt_status == "SAFE" and ml_class == "SAFE":
            # Confidence = average of both
            vt_conf = float(vt_result.get("confidence") or 0.85)
            ml_conf = 1.0 - ml_prob  # phishing_prob = 0 → confidence = 1
            confidence = min(0.95, (vt_conf + ml_conf) / 2)
            return {
                "classification": "SAFE",
                "confidence": round(confidence, 4),
                "weighted_score": round(ml_prob, 4),
                "source": "HYBRID_CONSENSUS_SAFE",
            }

        # Rule 3b: VT clean + ML unknown → SAFE (VT is authoritative)
        if has_vt and vt_status == "SAFE" and vt_harmless > 0 and vt_malicious == 0 and vt_suspicious == 0:
            confidence = float(vt_result.get("confidence") or 0.85)
            return {
                "classification": "SAFE",
                "confidence": round(confidence, 4),
                "weighted_score": None,
                "source": "VIRUSTOTAL_CLEAN",
            }

        # Rule 3c: ML safe + VT unknown → SAFE (ML alone is OK for SAFE, but with lower confidence)
        if has_ml and ml_class == "SAFE" and not has_vt:
            confidence = min(0.80, 1.0 - ml_prob)  # Cap at 0.80 for ML-only SAFE
            return {
                "classification": "SAFE",
                "confidence": round(confidence, 4),
                "weighted_score": round(ml_prob, 4),
                "source": "ML_SAFE_ONLY",
            }

        # ═══════════════════════════════════════════════════════════════════
        # TIER 4: Hybrid weighted score (fallback for edge cases)
        # ═══════════════════════════════════════════════════════════════════
        if has_vt and has_ml:
            vt_score = min(1.0, (vt_malicious + (vt_suspicious * 0.5)) / max(1.0, vt_total * 0.10))
            score = (0.55 * vt_score) + (0.45 * ml_prob)

            if score >= 0.70:
                classification = "DANGEROUS"
            elif score >= 0.40:
                classification = "SUSPICIOUS"
            else:
                classification = "SAFE"

            # Confidence reflects the score, but never reaches 0.99 from weighted alone
            if classification == "SAFE":
                confidence = max(0.70, 1.0 - score)
            else:
                confidence = round(min(0.88, 0.60 + score * 0.3), 4)

            return {
                "classification": classification,
                "confidence": round(confidence, 4),
                "weighted_score": round(score, 4),
                "source": "HYBRID_WEIGHTED",
            }

        # ═══════════════════════════════════════════════════════════════════
        # TIER 5: Insufficient evidence → UNKNOWN (never fabricate)
        # ═══════════════════════════════════════════════════════════════════
        return {
            "classification": "UNKNOWN",
            "confidence": None,
            "weighted_score": None,
            "source": "INSUFFICIENT_EVIDENCE",
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
    async def process_url_scan(cls, target_url: str, language: str = "ar") -> dict:
        """Standalone 3-Stage URL Link Scanner (ML -> VirusTotal -> Gemini Research)."""
        try:
            ml_result = predict_url(target_url)
        except Exception:
            logger.exception("url_ml_analysis_failed")
            ml_result = {"classification": "UNKNOWN", "confidence": None, "source": "ML_ERROR"}

        try:
            vt_result = await check_url_virustotal(target_url)
        except Exception:
            logger.exception("url_virustotal_failed")
            vt_result = {"status": "UNKNOWN", "error": "VIRUSTOTAL_UNAVAILABLE"}

        combined = cls.combine_scan_results(vt_result, ml_result)
        combined["evidence"] = {"ml": ml_result, "virustotal": vt_result, "input_type": "URL"}

        try:
            explanation = await generate_explanation(
                input_value=target_url,
                classification=combined["classification"],
                evidence=combined.get("evidence", {}),
                language=language,
            )
        except Exception:
            logger.exception("url_gemini_failed")
            explanation = cls._local_explanation(combined["classification"], language)

        return {
            "scan_kind": "URL_LINK",
            "input_type": "URL",
            "input_value": target_url,
            "extracted_url": target_url,
            "classification": combined["classification"],
            "confidence": combined.get("confidence"),
            "source": combined["source"],
            "stages": {
                "stage1_ml": {
                    "name": "Stage 1: LightGBM ML Model Analysis",
                    "classification": ml_result.get("classification", "UNKNOWN"),
                    "confidence": ml_result.get("confidence"),
                    "phishing_prob": ml_result.get("phishing_prob"),
                    "source": ml_result.get("source", "N/A"),
                },
                "stage2_virustotal": {
                    "name": "Stage 2: VirusTotal 92+ Engines Intelligence",
                    "status": vt_result.get("status", "UNKNOWN"),
                    "malicious": vt_result.get("malicious", 0),
                    "suspicious": vt_result.get("suspicious", 0),
                    "harmless": vt_result.get("harmless", 0),
                    "total_engines": vt_result.get("total_engines", 0),
                },
                "stage3_gemini": {
                    "name": "Stage 3: Gemini AI URL Threat Research",
                    "provider": explanation.get("provider", "TEMPLATE"),
                    "summary": explanation.get("summary", ""),
                    "recommendation": explanation.get("recommendation", ""),
                },
            },
            "explanation": explanation,
            "virustotal": vt_result,
            "ml_model": {
                "classification": ml_result.get("classification", "UNKNOWN"),
                "confidence": ml_result.get("confidence"),
                "phishing_prob": ml_result.get("phishing_prob"),
                "source": ml_result.get("source", "N/A"),
            },
        }

    @classmethod
    async def process_text_scan(cls, text_content: str, language: str = "ar") -> dict:
        """Standalone SMS / Text Message Smishing Scanner (Text NLP -> Embedded Link Audit -> Gemini Research)."""
        extracted_url = cls.extract_url_from_text(text_content)
        vt_result, ml_result = {}, {}

        if extracted_url:
            try:
                ml_result = predict_url(extracted_url)
            except Exception:
                logger.exception("sms_ml_analysis_failed")
                ml_result = {"classification": "UNKNOWN", "confidence": None, "source": "ML_ERROR"}

            try:
                vt_result = await check_url_virustotal(extracted_url)
            except Exception:
                logger.exception("sms_virustotal_failed")
                vt_result = {"status": "UNKNOWN", "error": "VIRUSTOTAL_UNAVAILABLE"}

            combined = cls.combine_scan_results(vt_result, ml_result)
            text_signal = cls.analyze_text_phishing(text_content, has_embedded_url=True)
            combined = cls._merge_text_signal(combined, text_signal)
        else:
            text_signal = cls.analyze_text_phishing(text_content)
            combined = {
                "classification": text_signal["classification"],
                "confidence": text_signal["confidence"],
                "weighted_score": None,
                "source": "SMS_TEXT_ANALYZER",
            }
            vt_result = {"status": "NOT_APPLICABLE", "total_engines": 0}

        combined["evidence"] = {
            "ml": ml_result,
            "virustotal": vt_result,
            "input_type": "TEXT",
            "extracted_url": extracted_url,
            "keyword_matches": cls.analyze_text_phishing(text_content).get("keyword_matches", []),
        }

        try:
            explanation = await generate_explanation(
                input_value=text_content,
                classification=combined["classification"],
                evidence=combined.get("evidence", {}),
                language=language,
            )
        except Exception:
            logger.exception("sms_gemini_failed")
            explanation = cls._local_explanation(combined["classification"], language)

        return {
            "scan_kind": "SMS_TEXT",
            "input_type": "TEXT",
            "input_value": text_content,
            "extracted_url": extracted_url or None,
            "classification": combined["classification"],
            "confidence": combined.get("confidence"),
            "source": combined["source"],
            "text_analysis": {
                "has_embedded_url": bool(extracted_url),
                "extracted_url": extracted_url or None,
                "phishing_keywords": cls.analyze_text_phishing(text_content).get("keyword_matches", []),
            },
            "stages": {
                "stage1_text_nlp": {
                    "name": "Stage 1: SMS Phishing & Lure NLP Analysis",
                    "classification": combined["classification"],
                    "confidence": combined.get("confidence"),
                    "source": combined.get("source"),
                },
                "stage2_link_audit": {
                    "name": "Stage 2: Embedded Link Security Audit",
                    "status": vt_result.get("status", "NOT_APPLICABLE"),
                    "malicious": vt_result.get("malicious", 0),
                    "suspicious": vt_result.get("suspicious", 0),
                    "total_engines": vt_result.get("total_engines", 0),
                },
                "stage3_gemini_sms": {
                    "name": "Stage 3: Gemini AI Smishing & Fraud Research",
                    "provider": explanation.get("provider", "TEMPLATE"),
                    "summary": explanation.get("summary", ""),
                    "recommendation": explanation.get("recommendation", ""),
                },
            },
            "explanation": explanation,
            "virustotal": vt_result,
            "ml_model": {
                "classification": ml_result.get("classification", "UNKNOWN"),
                "confidence": ml_result.get("confidence"),
                "phishing_prob": ml_result.get("phishing_prob"),
                "source": ml_result.get("source", "N/A"),
            },
        }

    @classmethod
    async def process_guest_scan(cls, input_type: str, raw_input: str, language: str = "ar") -> dict:
        """Process guest scan routing cleanly between URL and SMS Text pipelines."""
        operation_id = resource_id(raw_input)
        log_event(logger, logging.INFO, "guest_scan_started", operation_id=operation_id, input_type=input_type, language=language)
        if input_type == "TEXT":
            scan_res = await cls.process_text_scan(raw_input, language=language)
        else:
            target = cls.extract_url_from_text(raw_input) or raw_input
            scan_res = await cls.process_url_scan(target, language=language)
            scan_res["input_value"] = raw_input
        scan_res["is_guest"] = True
        scan_res["scan_id"] = None
        log_event(logger, logging.INFO, "guest_scan_finished", operation_id=operation_id, classification=scan_res.get("classification"))
        return scan_res

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

        operation_id = resource_id(raw_input)
        log_event(logger, logging.INFO, "authenticated_scan_started", operation_id=operation_id, input_type=input_type, language=language)
        if input_type == "TEXT":
            scan_res = await cls.process_text_scan(raw_input, language=language)
        else:
            target = cls.extract_url_from_text(raw_input) or raw_input
            scan_res = await cls.process_url_scan(target, language=language)
            scan_res["input_value"] = raw_input

        scan_res["is_guest"] = False

        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            scan_data = {
                "user_id": user_id,
                "input_type": input_type,
                "input_value_masked": cls._mask_input(input_type, raw_input),
                "status": "COMPLETED",
                "classification": scan_res["classification"],
                "confidence_score": float(scan_res.get("confidence") or 0.0),
                "confidence_level": "HIGH" if (scan_res.get("confidence") or 0) >= 0.8 else "MEDIUM",
                "recommendation": scan_res.get("explanation", {}).get("recommendation", ""),
                "completed_at": now_iso,
            }
            saved = supabase.table("scans").insert(scan_data).execute()
            if saved.data:
                scan_id = saved.data[0].get("id")
                scan_res["scan_id"] = scan_id
                try:
                    supabase.table("scans").update({"analysis_snapshot": scan_res.get("stages", {})}).eq("id", scan_id).eq("user_id", user_id).execute()
                except Exception:
                    # Older installations can apply the additive SQL migration later;
                    # the scan itself must not fail merely because the optional snapshot is absent.
                    logger.warning("analysis_snapshot_persistence_skipped")

                explanation = scan_res.get("explanation", {})
                raw_provider = str(explanation.get("provider", "TEMPLATE")).upper()
                if "GEMINI" in raw_provider:
                    provider = "GEMINI"
                elif "LOCAL" in raw_provider or "RULES" in raw_provider:
                    provider = "LOCAL_RULES"
                elif "HUMAN" in raw_provider:
                    provider = "HUMAN_REVIEW"
                elif raw_provider in {"TEMPLATE", "GEMINI", "HUMAN_REVIEW", "LOCAL_RULES"}:
                    provider = raw_provider
                else:
                    provider = "TEMPLATE"

                explanation_data = {
                    "scan_id": scan_id,
                    "language": language,
                    "summary": explanation.get("summary", ""),
                    "reasons": explanation.get("reasons", []),
                    "recommendation": explanation.get("recommendation", ""),
                    "provider": provider,
                }
                try:
                    supabase.table("scan_explanations").insert(explanation_data).execute()
                except Exception:
                    logger.warning("scan_explanation_persistence_failed")
                event = {
                    "type": "scan_completed",
                    "scan_id": scan_id,
                    "classification": scan_res.get("classification", "UNKNOWN"),
                    "confidence": scan_res.get("confidence"),
                    "created_at": now_iso,
                    "title": "اكتمل فحص جديد",
                }
                await manager.broadcast(user_id, event)
                if scan_res.get("classification") == "DANGEROUS":
                    notification = {
                        "user_id": user_id,
                        "scan_id": scan_id,
                        "type": "DANGEROUS_RESULT",
                        "title": "تنبيه أمني عاجل",
                        "body": "تم اكتشاف نتيجة خطيرة في آخر فحص. لا تفتح الرابط ولا تدخل بياناتك.",
                    }
                    try:
                        saved_notification = supabase.table("notifications").insert(notification).execute()
                        notification_data = (saved_notification.data or [notification])[0]
                    except Exception:
                        logger.warning("dangerous_notification_persistence_failed")
                        notification_data = notification
                    await manager.broadcast(user_id, {
                        "type": "security_alert",
                        "severity": "critical",
                        "notification": notification_data,
                        "created_at": now_iso,
                    })
                log_event(logger, logging.INFO, "authenticated_scan_persisted", operation_id=operation_id, scan_id=scan_id)
        except Exception:
            logger.error("authenticated_scan_persistence_failed")
            raise ScanPersistenceError("scan persistence failed") from None

        log_event(logger, logging.INFO, "authenticated_scan_finished", operation_id=operation_id, classification=scan_res.get("classification"))
        return scan_res

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
