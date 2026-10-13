from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, EmailStr, Field

from app.admin.dependencies import ROLE_PERMISSIONS, bearer_token, client_ip, current_admin, require_permissions, require_roles
from app.admin.security import (
    AdminSecurityError, decrypt_totp_secret, encrypt_totp_secret, hash_password,
    hash_value, issue_access_token, issue_challenge_token, issue_setup_token,
    new_refresh_token, now, recovery_hash, refresh_hash, totp_uri, verify_password,
    verify_totp,
)
from app.config import settings
from app.db.supabase_client import supabase

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class BootstrapRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)


class CodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class InviteRequest(BaseModel):
    email: EmailStr
    role: Literal["SUPERVISOR", "ADMIN", "SUPER_ADMIN"] = "SUPERVISOR"


class UserStatusRequest(BaseModel):
    status: Literal["ACTIVE", "SUSPENDED"]
    reason: str = Field(min_length=3, max_length=500)


def _admin_by_email(email: str) -> dict | None:
    result = supabase.table("admin_users").select("*").eq("email", str(email).strip().lower()).limit(1).execute()
    return result.data[0] if result.data else None


def _audit(admin_id: str | None, action: str, resource_type: str, resource_id: str | None, request: Request, before=None, after=None, target_user_id: str | None = None, target_scan_id: str | None = None):
    request_id = request.headers.get("x-request-id")
    try:
        UUID(request_id) if request_id else None
    except ValueError:
        request_id = None
    supabase.table("admin_audit_logs").insert({
        "admin_user_id": admin_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "target_user_id": target_user_id,
        "target_scan_id": target_scan_id,
        "before_data": before or {},
        "after_data": after or {},
        "metadata_masked": {},
        "ip_hash": hash_value(client_ip(request)),
        "user_agent_hash": hash_value(request.headers.get("user-agent", "")),
        "request_id": request_id,
    }).execute()


def _tokens(admin: dict, request: Request, token_family: str | None = None) -> dict:
    refresh = new_refresh_token()
    row = {
        "admin_user_id": str(admin["id"]),
        "refresh_token_hash": refresh_hash(refresh),
        "token_family": token_family or str(uuid4()),
        "ip_hash": hash_value(client_ip(request)),
        "user_agent_hash": hash_value(request.headers.get("user-agent", "")),
        "expires_at": (now() + timedelta(days=settings.ADMIN_REFRESH_TOKEN_DAYS)).isoformat(),
    }
    result = supabase.table("admin_sessions").insert(row).execute()
    session_id = result.data[0]["id"] if result.data else None
    if not session_id:
        raise HTTPException(status_code=503, detail="Unable to create administrator session")
    access = issue_access_token(admin, {"sid": session_id})
    return {"access_token": access, "refresh_token": refresh, "session_id": session_id}


@router.post("/auth/bootstrap", status_code=201)
def bootstrap(request: BootstrapRequest, http_request: Request, bootstrap_token: str | None = Header(None, alias="X-Admin-Bootstrap-Token")):
    """Create the first SUPER_ADMIN only when the one-time server bootstrap secret matches."""
    if not settings.ADMIN_BOOTSTRAP_TOKEN or not bootstrap_token or bootstrap_token != settings.ADMIN_BOOTSTRAP_TOKEN:
        raise HTTPException(status_code=404, detail="Not found")
    existing = supabase.table("admin_users").select("id").limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Admin bootstrap is already completed")
    row = {
        "email": str(request.email).strip().lower(),
        "display_name": request.display_name.strip(),
        "password_hash": hash_password(request.password),
        "role": "SUPER_ADMIN",
        "status": "ACTIVE",
        "email_verified": True,
        "two_factor_required": True,
    }
    result = supabase.table("admin_users").insert(row).execute()
    admin = result.data[0]
    _audit(str(admin["id"]), "ADMIN_BOOTSTRAPPED", "admin_user", str(admin["id"]), http_request, after={"role": "SUPER_ADMIN", "status": "ACTIVE"})
    return {"success": True, "data": {"id": admin["id"], "email": admin["email"], "requires_2fa_setup": True}}


@router.post("/auth/login")
def login(request: LoginRequest, http_request: Request):
    email = str(request.email).strip().lower()
    ip_hash = hash_value(client_ip(http_request))
    recent = supabase.table("admin_login_attempts").select("id", count="exact", head=True).eq("ip_hash", ip_hash).gte("created_at", (now() - timedelta(minutes=15)).isoformat()).in_("outcome", ["INVALID_CREDENTIALS", "INVALID_2FA", "RATE_LIMITED"]).execute()
    if (recent.count or 0) >= settings.ADMIN_LOGIN_RATE_LIMIT:
        supabase.table("admin_login_attempts").insert({"email_hash": hash_value(email), "ip_hash": ip_hash, "outcome": "RATE_LIMITED", "failure_reason": "IP_WINDOW_EXCEEDED"}).execute()
        raise HTTPException(status_code=429, detail="Too many login attempts")
    admin = _admin_by_email(email)
    if not admin or admin.get("status") != "ACTIVE" or not verify_password(request.password, admin.get("password_hash", "")):
        supabase.table("admin_login_attempts").insert({"email_hash": hash_value(email), "ip_hash": ip_hash, "admin_user_id": admin.get("id") if admin else None, "outcome": "INVALID_CREDENTIALS"}).execute()
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    method = supabase.table("admin_2fa_methods").select("id,is_enabled").eq("admin_user_id", admin["id"]).limit(1).execute()
    if admin.get("two_factor_required") and not (method.data and method.data[0].get("is_enabled")):
        return {"success": True, "status": "2FA_SETUP_REQUIRED", "setup_token": issue_setup_token(admin)}
    if admin.get("two_factor_required"):
        return {"success": True, "status": "2FA_REQUIRED", "challenge_token": issue_challenge_token(admin)}
    tokens = _tokens(admin, http_request)
    supabase.table("admin_users").update({"last_login_at": now().isoformat()}).eq("id", admin["id"]).execute()
    supabase.table("admin_login_attempts").insert({"email_hash": hash_value(email), "ip_hash": ip_hash, "admin_user_id": admin["id"], "outcome": "SUCCESS"}).execute()
    _audit(str(admin["id"]), "ADMIN_LOGIN", "admin_session", tokens["session_id"], http_request)
    return {"success": True, "status": "AUTHENTICATED", "data": tokens}


@router.post("/auth/2fa/setup")
def setup_2fa(http_request: Request, authorization: str | None = Header(None)):
    try:
        claims = __import__("app.admin.security", fromlist=["decode_token"]).decode_token(bearer_token(authorization), ("access", "2fa_setup"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid setup authorization") from None
    admin = _admin_by_id(claims["sub"])
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    secret = __import__("pyotp").random_base32()
    ciphertext, nonce = encrypt_totp_secret(secret)
    supabase.table("admin_2fa_methods").upsert({"admin_user_id": admin["id"], "method": "TOTP", "secret_ciphertext": ciphertext, "secret_nonce": nonce, "is_enabled": False}, on_conflict="admin_user_id").execute()
    return {"success": True, "data": {"otpauth_uri": totp_uri(secret, admin["email"]), "secret": secret}}


def _admin_by_id(admin_id: str) -> dict | None:
    result = supabase.table("admin_users").select("*").eq("id", admin_id).limit(1).execute()
    return result.data[0] if result.data else None


@router.post("/auth/2fa/confirm")
def confirm_2fa(request: CodeRequest, http_request: Request, authorization: str | None = Header(None)):
    try:
        claims = __import__("app.admin.security", fromlist=["decode_token"]).decode_token(bearer_token(authorization), ("access", "2fa_setup"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid setup authorization") from None
    method_result = supabase.table("admin_2fa_methods").select("*").eq("admin_user_id", claims["sub"]).limit(1).execute()
    method = method_result.data[0] if method_result.data else None
    if not method or not verify_totp(decrypt_totp_secret(method["secret_ciphertext"]), request.code):
        raise HTTPException(status_code=400, detail="Invalid authenticator code")
    codes = [secrets.token_urlsafe(8) for _ in range(10)]
    supabase.table("admin_2fa_methods").update({"is_enabled": True, "verified_at": now().isoformat()}).eq("id", method["id"]).execute()
    supabase.table("admin_2fa_recovery_codes").delete().eq("admin_user_id", claims["sub"]).execute()
    supabase.table("admin_2fa_recovery_codes").insert([{"admin_user_id": claims["sub"], "code_hash": recovery_hash(code)} for code in codes]).execute()
    _audit(claims["sub"], "ADMIN_2FA_ENABLED", "admin_2fa", method["id"], http_request)
    return {"success": True, "data": {"recovery_codes": codes}}


@router.post("/auth/2fa/verify")
def verify_2fa(request: CodeRequest, http_request: Request, authorization: str | None = Header(None)):
    try:
        claims = __import__("app.admin.security", fromlist=["decode_token"]).decode_token(bearer_token(authorization), "2fa_challenge")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid 2FA challenge") from None
    ip_hash = hash_value(client_ip(http_request))
    recent = supabase.table("admin_login_attempts").select("id", count="exact", head=True).eq(
        "ip_hash", ip_hash
    ).gte("created_at", (now() - timedelta(minutes=15)).isoformat()).eq("outcome", "INVALID_2FA").execute()
    if (recent.count or 0) >= settings.ADMIN_LOGIN_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many 2FA attempts")
    method_result = supabase.table("admin_2fa_methods").select("*").eq("admin_user_id", claims["sub"]).limit(1).execute()
    method = method_result.data[0] if method_result.data else None
    valid = bool(method and verify_totp(decrypt_totp_secret(method["secret_ciphertext"]), request.code))
    recovery_row = None
    if not valid:
        recovery_result = supabase.table("admin_2fa_recovery_codes").select("id").eq(
            "admin_user_id", claims["sub"]
        ).eq("code_hash", recovery_hash(request.code.strip())).is_("used_at", "null").limit(1).execute()
        recovery_row = recovery_result.data[0] if recovery_result.data else None
        valid = recovery_row is not None
    outcome = "SUCCESS" if valid else "INVALID_2FA"
    supabase.table("admin_login_attempts").insert({"admin_user_id": claims["sub"], "ip_hash": ip_hash, "outcome": outcome}).execute()
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid authenticator code")
    if recovery_row:
        supabase.table("admin_2fa_recovery_codes").update({"used_at": now().isoformat()}).eq("id", recovery_row["id"]).is_("used_at", "null").execute()
    admin = _admin_by_id(claims["sub"])
    tokens = _tokens(admin, http_request)
    supabase.table("admin_users").update({"last_login_at": now().isoformat()}).eq("id", admin["id"]).execute()
    _audit(str(admin["id"]), "ADMIN_LOGIN_2FA", "admin_session", tokens["session_id"], http_request)
    return {"success": True, "status": "AUTHENTICATED", "data": tokens}


@router.post("/auth/refresh")
def refresh(request: RefreshRequest, http_request: Request):
    old_hash = refresh_hash(request.refresh_token)
    result = supabase.table("admin_sessions").select("*").eq("refresh_token_hash", old_hash).limit(1).execute()
    session = result.data[0] if result.data else None
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if session.get("revoked_at"):
        supabase.table("admin_sessions").update({
            "revoked_at": now().isoformat(),
            "revoke_reason": "REUSE_DETECTED",
        }).eq("admin_user_id", session["admin_user_id"]).eq(
            "token_family", session["token_family"]
        ).is_("revoked_at", "null").execute()
        raise HTTPException(status_code=401, detail="Refresh token has already been used")
    try:
        expires_at = datetime.fromisoformat(session.get("expires_at", "").replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from None
    if expires_at <= now():
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    admin = _admin_by_id(session["admin_user_id"])
    if not admin or admin.get("status") != "ACTIVE":
        raise HTTPException(status_code=401, detail="Admin is inactive")
    rotated = supabase.table("admin_sessions").update({
        "revoked_at": now().isoformat(),
        "last_used_at": now().isoformat(),
        "revoke_reason": "ROTATED",
    }).eq("id", session["id"]).is_("revoked_at", "null").execute()
    if not rotated.data:
        raise HTTPException(status_code=401, detail="Refresh token has already been used")
    tokens = _tokens(admin, http_request, str(session["token_family"]))
    _audit(str(admin["id"]), "ADMIN_SESSION_ROTATED", "admin_session", str(session["id"]), http_request)
    return {"success": True, "data": tokens}


@router.post("/auth/logout")
def logout(http_request: Request, authorization: str | None = Header(None), admin: dict = Depends(current_admin)):
    try:
        claims = __import__("app.admin.security", fromlist=["decode_token"]).decode_token(bearer_token(authorization), "access")
        sid = claims.get("sid")
        if sid:
            supabase.table("admin_sessions").update({"revoked_at": now().isoformat(), "revoke_reason": "LOGOUT"}).eq("id", sid).eq("admin_user_id", admin["id"]).execute()
    except Exception:
        pass
    _audit(str(admin["id"]), "ADMIN_LOGOUT", "admin_session", None, http_request)
    return {"success": True}


@router.post("/auth/logout-all")
def logout_all(http_request: Request, admin: dict = Depends(current_admin)):
    supabase.table("admin_sessions").update({"revoked_at": now().isoformat(), "revoke_reason": "LOGOUT_ALL"}).eq("admin_user_id", admin["id"]).is_("revoked_at", "null").execute()
    _audit(str(admin["id"]), "ADMIN_LOGOUT_ALL", "admin_session", None, http_request)
    return {"success": True}


@router.get("/auth/me")
def me(admin: dict = Depends(current_admin)):
    profile = {**admin, "permissions": sorted(ROLE_PERMISSIONS.get(admin.get("role"), frozenset()))}
    return {"success": True, "data": profile}


def _count(table_name: str, filters: list[tuple[str, str, object]] | None = None) -> int:
    query = supabase.table(table_name).select("id", count="exact", head=True)
    for operator, column, value in filters or []:
        query = getattr(query, operator)(column, value)
    result = query.execute()
    return int(result.count or 0)


@router.get("/dashboard/overview")
def dashboard_overview(
    range_days: int = Query(30, ge=1, le=90),
    admin: dict = Depends(require_permissions("dashboard.read")),
):
    """Return operational metrics from Supabase without fabricated fallbacks."""
    del admin
    period_start = now() - timedelta(days=range_days)
    period_iso = period_start.isoformat()
    try:
        users_period = [("gte", "created_at", period_iso)]
        scans_period = [("gte", "created_at", period_iso)]
        feedback_period = [("gte", "created_at", period_iso)]
        support_period = [("gte", "created_at", period_iso)]
        audit_period = [("gte", "created_at", period_iso)]

        scan_counts = {
            "total": _count("scans", scans_period),
            "completed": _count("scans", scans_period + [("eq", "status", "COMPLETED")]),
            "failed": _count("scans", scans_period + [("eq", "status", "FAILED")]),
            "processing": _count("scans", scans_period + [("eq", "status", "PROCESSING")]),
            "safe": _count("scans", scans_period + [("eq", "classification", "SAFE")]),
            "suspicious": _count("scans", scans_period + [("eq", "classification", "SUSPICIOUS")]),
            "dangerous": _count("scans", scans_period + [("eq", "classification", "DANGEROUS")]),
            "unknown": _count("scans", scans_period + [("eq", "classification", "UNKNOWN")]),
            "needs_review": _count("scans", scans_period + [("eq", "classification", "NEEDS_REVIEW")]),
        }
        recent_audit = supabase.table("admin_audit_logs").select(
            "id,action,resource_type,resource_id,created_at,admin_user_id"
        ).gte("created_at", period_iso).order("created_at", desc=True).limit(8).execute()
        data = {
            "range_days": range_days,
            "period_start": period_iso,
            "generated_at": now().isoformat(),
            "users": {
                "total": _count("custom_users"),
                "active": _count("custom_users", [("eq", "status", "ACTIVE")]),
                "suspended": _count("custom_users", [("eq", "status", "SUSPENDED")]),
                "new": _count("custom_users", users_period),
            },
            "scans": scan_counts,
            "feedback": {
                "total": _count("feedback", feedback_period),
                "new": _count("feedback", feedback_period + [("eq", "status", "NEW")]),
                "reviewed": _count("feedback", feedback_period + [("eq", "status", "REVIEWED")]),
            },
            "support": {
                "open": _count("support_requests", [("eq", "status", "OPEN")]),
                "in_progress": _count("support_requests", [("eq", "status", "IN_PROGRESS")]),
                "urgent_open": _count("support_requests", [("eq", "status", "OPEN"), ("eq", "priority", "URGENT")]),
                "new": _count("support_requests", support_period),
            },
            "audit": {
                "period_events": _count("admin_audit_logs", audit_period),
                "recent": recent_audit.data or [],
            },
        }
        return {"success": True, "data": data}
    except Exception:
        raise HTTPException(status_code=503, detail="تعذر تحميل مؤشرات Dashboard من قاعدة البيانات") from None


@router.get("/users")
def users(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, max_length=120),
    status: Literal["ACTIVE", "SUSPENDED", "DELETED"] | None = Query(None),
    admin: dict = Depends(require_permissions("users.read")),
):
    del admin
    query = supabase.table("custom_users").select(
        "id,email,display_name,role,status,email_verified,preferred_language,last_login_at,created_at,updated_at",
        count="exact",
    )
    if search:
        safe_search = search.strip().replace("%", "").replace("_", "").replace(",", "")
        if safe_search:
            query = query.or_(f"email.ilike.%{safe_search}%,display_name.ilike.%{safe_search}%")
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"success": True, "data": result.data or [], "meta": {"limit": limit, "offset": offset, "total": int(result.count or 0)}}


@router.get("/users/{user_id}")
def user_details(user_id: UUID, admin: dict = Depends(require_permissions("users.read"))):
    del admin
    result = supabase.table("custom_users").select(
        "id,email,display_name,role,status,email_verified,preferred_language,last_login_at,created_at,updated_at"
    ).eq("id", str(user_id)).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    user = result.data[0]
    try:
        user["scan_count"] = _count("scans", [("eq", "user_id", str(user_id))])
        user["feedback_count"] = _count("feedback", [("eq", "user_id", str(user_id))])
    except Exception:
        raise HTTPException(status_code=503, detail="تعذر تحميل إحصاءات المستخدم") from None
    return {"success": True, "data": user}


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: UUID,
    request: UserStatusRequest,
    http_request: Request,
    admin: dict = Depends(require_permissions("users.manage")),
):
    result = supabase.table("custom_users").select("id,status,email,display_name").eq("id", str(user_id)).limit(1).execute()
    user = result.data[0] if result.data else None
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    if user["status"] == "DELETED":
        raise HTTPException(status_code=409, detail="لا يمكن تغيير حالة مستخدم محذوف")
    if user["status"] == request.status:
        return {"success": True, "data": user, "changed": False}
    updated = supabase.table("custom_users").update({"status": request.status}).eq("id", str(user_id)).execute()
    data = (updated.data or [None])[0] or {**user, "status": request.status}
    _audit(
        str(admin["id"]),
        "ADMIN_USER_STATUS_CHANGED",
        "custom_user",
        str(user_id),
        http_request,
        before={"status": user["status"]},
        after={"status": request.status, "reason": request.reason},
        target_user_id=str(user_id),
    )
    return {"success": True, "data": data, "changed": True}


@router.get("/sessions")
def sessions(admin: dict = Depends(require_permissions("sessions.read"))):
    result = supabase.table("admin_sessions").select("id,created_at,last_used_at,expires_at,revoked_at,revoke_reason,ip_hash,user_agent_hash").eq("admin_user_id", admin["id"]).order("created_at", desc=True).limit(100).execute()
    return {"success": True, "data": result.data or []}


@router.delete("/sessions/{session_id}")
def revoke_session(session_id: UUID, http_request: Request, admin: dict = Depends(require_permissions("sessions.manage"))):
    result = supabase.table("admin_sessions").update({"revoked_at": now().isoformat(), "revoke_reason": "ADMIN_REVOKED"}).eq("id", str(session_id)).eq("admin_user_id", admin["id"]).is_("revoked_at", "null").execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")
    _audit(str(admin["id"]), "ADMIN_SESSION_REVOKED", "admin_session", str(session_id), http_request)
    return {"success": True}


@router.get("/audit-logs")
def audit_logs(limit: int = 50, offset: int = 0, admin: dict = Depends(require_permissions("audit.read"))):
    limit = max(1, min(limit, 100))
    result = supabase.table("admin_audit_logs").select("id,admin_user_id,action,resource_type,resource_id,target_user_id,target_scan_id,before_data,after_data,metadata_masked,created_at").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return {"success": True, "data": result.data or []}


@router.post("/invitations")
def invite(request: InviteRequest, http_request: Request, admin: dict = Depends(require_roles("SUPER_ADMIN"))):
    if request.role == "SUPER_ADMIN" and admin["role"] != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can invite SUPER_ADMIN")
    raw = new_refresh_token()
    result = supabase.table("admin_invitations").insert({"email": str(request.email).lower(), "role": request.role, "invited_by": admin["id"], "token_hash": refresh_hash(raw), "expires_at": (now() + timedelta(days=2)).isoformat()}).execute()
    invitation = result.data[0]
    _audit(str(admin["id"]), "ADMIN_INVITATION_CREATED", "admin_invitation", invitation["id"], http_request, after={"email": str(request.email).lower(), "role": request.role})
    return {"success": True, "data": {"id": invitation["id"], "token": raw, "expires_at": invitation["expires_at"]}}
