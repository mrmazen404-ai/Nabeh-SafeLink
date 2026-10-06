"""Authenticated dashboard APIs for the verified custom-auth user."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.auth.security import AuthSecurityError, get_authenticated_user, hash_password, verify_password
from app.db.supabase_client import supabase
from app.observability import log_event, mask_email
from app.dashboard.realtime import manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    preferred_language: Optional[Literal["ar", "en"]] = None
    timezone: Optional[str] = Field(default=None, max_length=50)


class PreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    dangerous_scan_enabled: Optional[bool] = None
    weekly_summary_enabled: Optional[bool] = None


class ConsentUpdate(BaseModel):
    consent_type: Literal["PRIVACY_POLICY", "DATA_RETENTION", "MODEL_IMPROVEMENT"]
    version: str = Field(min_length=1, max_length=30)
    granted: bool


class FeedbackCreate(BaseModel):
    scan_id: str
    reported_classification: Literal["SAFE", "SUSPICIOUS", "DANGEROUS", "UNKNOWN", "NEEDS_REVIEW"]
    comment: Optional[str] = Field(default=None, max_length=2000)


class SupportCreate(BaseModel):
    subject: str = Field(min_length=2, max_length=160)
    message: str = Field(min_length=2, max_length=5000)
    priority: Literal["LOW", "NORMAL", "HIGH", "URGENT"] = "NORMAL"


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)
    confirm_password: str = Field(min_length=12, max_length=128)


@router.websocket("/ws")
async def dashboard_websocket(websocket: WebSocket):
    """Authenticate via first message, then stream only events belonging to this user."""
    await websocket.accept()
    user_id = None
    try:
        try:
            raw_msg = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            data = json.loads(raw_msg)
            if not isinstance(data, dict) or data.get("type") != "auth":
                await websocket.close(code=1008, reason="authentication required")
                return
            token = data.get("token")
            if not token or not isinstance(token, str):
                await websocket.close(code=1008, reason="invalid authentication token")
                return

            user = get_authenticated_user(token)
            if user.get("status", "ACTIVE") != "ACTIVE":
                await websocket.close(code=1008, reason="inactive user")
                return
            user_id = str(user["id"])
        except asyncio.TimeoutError:
            await websocket.close(code=1008, reason="authentication timeout")
            return
        except Exception:
            await websocket.close(code=1008, reason="invalid authentication payload")
            return

        await manager.connect(user_id, websocket)
        await websocket.send_json({"type": "connected", "user_id": user_id, "server_time": _now()})

        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_json({"type": "pong", "server_time": _now()})
            else:
                try:
                    data = json.loads(message)
                    if isinstance(data, dict) and data.get("type") == "ping":
                        await websocket.send_json({"type": "pong", "server_time": _now()})
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("dashboard_websocket_failed")
    finally:
        if user_id:
            await manager.disconnect(user_id, websocket)


def _require_user(authorization: Optional[str]) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="تسجيل الدخول مطلوب")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="جلسة غير صالحة")
    try:
        user = get_authenticated_user(parts[1])
    except AuthSecurityError:
        raise HTTPException(status_code=401, detail="جلسة غير صالحة") from None
    if user.get("status", "ACTIVE") != "ACTIVE":
        log_event(logger, logging.WARNING, "dashboard_suspended_user_blocked")
        raise HTTPException(status_code=403, detail="الحساب موقوف")
    return user


def _user_public(user: dict, profile: Optional[dict] = None) -> dict:
    return {
        "user_id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name") or user["email"].split("@", 1)[0],
        "role": user.get("role", "USER"),
        "status": user.get("status", "ACTIVE"),
        "email_verified": bool(user.get("email_verified")),
        "preferred_language": user.get("preferred_language", "ar"),
        "timezone": (profile or {}).get("timezone"),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_profile(user_id: str) -> dict:
    result = supabase.table("user_profiles").select(
        "user_id,display_name,preferred_language,timezone,avatar_path,created_at,updated_at"
    ).eq("user_id", user_id).limit(1).execute()
    return result.data[0] if result.data else {}


@router.get("/overview")
async def dashboard_overview(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    response.headers["Cache-Control"] = "no-store, private"
    try:
        user_id = str(user["id"])
        scans_result = supabase.table("scans").select(
            "id,input_type,input_value_masked,classification,confidence_score,created_at,completed_at"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(50).execute()
        scans = scans_result.data or []
        notification_result = supabase.table("notifications").select("id", count="exact").eq(
            "user_id", user_id
        ).eq("is_read", False).execute()
        profile = _load_profile(user_id)
        counts = {"SAFE": 0, "SUSPICIOUS": 0, "DANGEROUS": 0, "UNKNOWN": 0}
        for scan in scans:
            classification = scan.get("classification") or "UNKNOWN"
            counts[classification] = counts.get(classification, 0) + 1
        data = {
            "user": _user_public(user, profile),
            "permissions": {
                "can_scan": True,
                "can_view_history": True,
                "can_view_statistics": True,
                "can_manage_profile": True,
                "can_manage_notifications": True,
                "can_manage_privacy": True,
                "can_manage_users": user.get("role") in {"ADMIN", "SUPERVISOR"},
                "role": user.get("role", "USER"),
            },
            "statistics": {"total": len(scans), "safe": counts["SAFE"], "suspicious": counts["SUSPICIOUS"], "dangerous": counts["DANGEROUS"], "unknown": counts["UNKNOWN"]},
            "unread_notifications": notification_result.count or len(notification_result.data or []),
            "recent_scans": scans[:5],
        }
        log_event(logger, logging.INFO, "dashboard_overview_loaded", total_scans=len(scans))
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as error:
        log_event(logger, logging.ERROR, "dashboard_overview_failed", error_type=type(error).__name__)
        raise HTTPException(status_code=503, detail="تعذر تحميل لوحة التحكم") from None


@router.get("/live-stats")
async def live_stats(response: Response, authorization: Optional[str] = Header(None)):
    """Return current counters without exposing another user's data."""
    user = _require_user(authorization)
    user_id = str(user["id"])
    day_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        total_result = supabase.table("scans").select("id", count="exact", head=True).eq("user_id", user_id).execute()
        day_result = supabase.table("scans").select("id", count="exact", head=True).eq("user_id", user_id).gte("created_at", day_ago).execute()
        counts = {}
        for classification in ("SAFE", "SUSPICIOUS", "DANGEROUS", "UNKNOWN"):
            result = supabase.table("scans").select("id", count="exact", head=True).eq("user_id", user_id).eq("classification", classification).execute()
            counts[classification.lower()] = result.count or 0
        unread = supabase.table("notifications").select("id", count="exact", head=True).eq("user_id", user_id).eq("is_read", False).execute()
        data = {"total": total_result.count or 0, "last_24_hours": day_result.count or 0, "unread_notifications": unread.count or 0, **counts, "generated_at": _now()}
        log_event(logger, logging.INFO, "live_stats_loaded", total=data["total"])
        return {"success": True, "data": data}
    except Exception:
        log_event(logger, logging.ERROR, "live_stats_failed")
        raise HTTPException(status_code=503, detail="تعذر تحميل الإحصائيات الحية") from None


@router.get("/activity")
async def activity_feed(response: Response, authorization: Optional[str] = Header(None), limit: int = Query(30, ge=1, le=100)):
    """Build a chronological, user-scoped activity feed from audit, scans and notifications."""
    user = _require_user(authorization)
    user_id = str(user["id"])
    try:
        audit = supabase.table("audit_logs").select("id,action,resource_type,created_at").eq(
            "actor_user_id", user_id
        ).order("created_at", desc=True).limit(limit).execute()
        scans = supabase.table("scans").select("id,classification,input_type,created_at").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(limit).execute()
        notifications = supabase.table("notifications").select("id,type,title,created_at").eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(limit).execute()
        items = []
        for item in audit.data or []:
            items.append({"id": f"audit:{item['id']}", "kind": "security", "action": item.get("action", "OTHER"), "title": "نشاط أمني", "created_at": item.get("created_at")})
        for item in scans.data or []:
            items.append({"id": f"scan:{item['id']}", "kind": "scan", "action": item.get("classification") or "UNKNOWN", "title": "اكتمل فحص جديد", "created_at": item.get("created_at")})
        for item in notifications.data or []:
            items.append({"id": f"notification:{item['id']}", "kind": "notification", "action": item.get("type", "SYSTEM"), "title": item.get("title") or "تنبيه النظام", "created_at": item.get("created_at")})
        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return {"success": True, "data": items[:limit]}
    except Exception:
        log_event(logger, logging.ERROR, "activity_feed_failed")
        raise HTTPException(status_code=503, detail="تعذر تحميل سجل النشاطات") from None


@router.get("/profile")
async def get_profile(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    response.headers["Cache-Control"] = "no-store, private"
    profile = _load_profile(str(user["id"]))
    log_event(logger, logging.INFO, "profile_loaded", recipient=mask_email(user["email"]))
    return {"success": True, "data": _user_public(user, profile)}


@router.patch("/profile")
async def update_profile(payload: ProfileUpdate, response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    user_id = str(user["id"])
    user_update = {}
    if payload.display_name is not None:
        user_update["display_name"] = payload.display_name.strip()
    if payload.preferred_language is not None:
        user_update["preferred_language"] = payload.preferred_language
    if user_update:
        user_update["updated_at"] = _now()
        supabase.table("custom_users").update(user_update).eq("id", user_id).execute()
    profile = _load_profile(user_id)
    profile_payload = {
        "user_id": user_id,
        "display_name": payload.display_name or profile.get("display_name") or user.get("display_name") or user["email"].split("@", 1)[0],
        "preferred_language": payload.preferred_language or profile.get("preferred_language") or user.get("preferred_language", "ar"),
        "timezone": payload.timezone if payload.timezone is not None else profile.get("timezone"),
        "updated_at": _now(),
    }
    supabase.table("user_profiles").upsert(profile_payload, on_conflict="user_id").execute()
    refreshed = {**user, **user_update}
    log_event(logger, logging.INFO, "profile_updated", recipient=mask_email(user["email"]))
    return {"success": True, "data": _user_public(refreshed, profile_payload)}


@router.get("/notifications")
async def get_notifications(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    result = supabase.table("notifications").select(
        "id,scan_id,type,title,body,is_read,created_at,read_at"
    ).eq("user_id", str(user["id"])).order("created_at", desc=True).limit(50).execute()
    return {"success": True, "data": result.data or []}


@router.post("/notifications/read-all")
async def mark_notifications_read(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    supabase.table("notifications").update({"is_read": True, "read_at": _now()}).eq(
        "user_id", str(user["id"])
    ).eq("is_read", False).execute()
    log_event(logger, logging.INFO, "notifications_marked_read")
    return {"success": True}


@router.post("/security/change-password")
async def change_password(payload: PasswordChange, response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=422, detail="كلمتا المرور غير متطابقتين")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=422, detail="كلمة المرور الجديدة يجب أن تختلف عن الحالية")
    if not verify_password(payload.current_password, user["password_hash"]):
        log_event(logger, logging.WARNING, "password_change_rejected")
        raise HTTPException(status_code=400, detail="كلمة المرور الحالية غير صحيحة")
    supabase.table("custom_users").update({"password_hash": hash_password(payload.new_password), "updated_at": _now()}).eq("id", str(user["id"])).execute()
    log_event(logger, logging.INFO, "password_changed")
    return {"success": True, "message": "تم تغيير كلمة المرور بنجاح"}


@router.get("/security/activity")
async def get_security_activity(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    result = supabase.table("audit_logs").select(
        "id,action,resource_type,metadata_masked,created_at"
    ).eq("actor_user_id", str(user["id"])).order("created_at", desc=True).limit(20).execute()
    return {"success": True, "data": result.data or []}


@router.get("/notification-preferences")
async def get_notification_preferences(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    result = supabase.table("notification_preferences").select(
        "user_id,in_app_enabled,email_enabled,dangerous_scan_enabled,weekly_summary_enabled,updated_at"
    ).eq("user_id", str(user["id"])).limit(1).execute()
    if result.data:
        data = result.data[0]
    else:
        data = {"user_id": str(user["id"]), "in_app_enabled": True, "email_enabled": False, "dangerous_scan_enabled": True, "weekly_summary_enabled": False}
    return {"success": True, "data": data}


@router.patch("/notification-preferences")
async def update_notification_preferences(payload: PreferenceUpdate, response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return await get_notification_preferences(response, authorization)
    updates.update({"user_id": str(user["id"]), "updated_at": _now()})
    result = supabase.table("notification_preferences").upsert(updates, on_conflict="user_id").execute()
    log_event(logger, logging.INFO, "notification_preferences_updated")
    return {"success": True, "data": (result.data or [updates])[0]}


@router.get("/privacy/consents")
async def get_privacy_consents(response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    result = supabase.table("privacy_consents").select(
        "id,consent_type,version,granted,granted_at,revoked_at"
    ).eq("user_id", str(user["id"])).order("granted_at", desc=True).limit(50).execute()
    return {"success": True, "data": result.data or []}


@router.post("/privacy/consents")
async def update_privacy_consent(payload: ConsentUpdate, response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    user_id = str(user["id"])
    row = {"user_id": user_id, "consent_type": payload.consent_type, "version": payload.version, "granted": payload.granted, "granted_at": _now(), "revoked_at": None if payload.granted else _now()}
    result = supabase.table("privacy_consents").upsert(row, on_conflict="user_id,consent_type,version").execute()
    log_event(logger, logging.INFO, "privacy_consent_updated", consent_type=payload.consent_type, granted=payload.granted)
    return {"success": True, "data": (result.data or [row])[0]}


@router.post("/feedback")
async def create_feedback(payload: FeedbackCreate, response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    row = {"scan_id": payload.scan_id, "user_id": str(user["id"]), "reported_classification": payload.reported_classification, "comment": payload.comment}
    result = supabase.table("feedback").insert(row).execute()
    log_event(logger, logging.INFO, "feedback_created")
    return {"success": True, "data": (result.data or [row])[0]}


@router.post("/support")
async def create_support_request(payload: SupportCreate, response: Response, authorization: Optional[str] = Header(None)):
    user = _require_user(authorization)
    row = {"user_id": str(user["id"]), "email": user["email"], "subject": payload.subject.strip(), "message": payload.message.strip(), "priority": payload.priority}
    result = supabase.table("support_requests").insert(row).execute()
    log_event(logger, logging.INFO, "support_request_created")
    return {"success": True, "data": (result.data or [row])[0]}
