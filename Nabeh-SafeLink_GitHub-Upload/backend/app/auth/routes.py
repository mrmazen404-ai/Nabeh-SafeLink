"""Custom authentication: backend-generated OTP, EmailJS delivery, and JWT sessions."""

import hmac
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, EmailStr, Field

from app.auth.emailjs import send_otp_via_emailjs
from app.auth.security import (
    AuthSecurityError,
    generate_otp,
    get_authenticated_user,
    get_reset_user,
    get_user_by_email,
    hash_otp,
    hash_password,
    issue_access_token,
    normalize_email,
    verify_password,
)
from app.config import settings
from app.db.supabase_client import supabase
from app.observability import log_event, mask_email
from app.security.guest_rate_limit import UpstashRateLimiter, client_identity

logger = logging.getLogger(__name__)
router = APIRouter()


class EmailDeliveryError(Exception):
    """Raised when the verification message cannot be delivered."""


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=12, max_length=128)


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=6, max_length=6)
    type: Literal["signup", "recovery"] = "signup"


class ResendOtpRequest(BaseModel):
    email: EmailStr
    type: Literal["signup", "recovery"] = "signup"


def _bearer_token(authorization: Optional[str]) -> str:
    parts = (authorization or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="جلسة غير صالحة")
    return parts[1]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _issue_email_otp(user_id: str, email: str, action: str) -> None:
    log_event(logger, logging.INFO, "otp_generation_started", action=action, recipient=mask_email(email))
    code = generate_otp()
    otp_id = str(uuid4())
    expires_at = (_now() + timedelta(minutes=settings.AUTH_OTP_MINUTES)).isoformat()
    # Invalidate previous codes before inserting the new one.
    supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
        "user_id", user_id
    ).eq("purpose", action).is_("consumed_at", "null").execute()
    supabase.table("custom_auth_otps").insert({
        "id": otp_id,
        "user_id": user_id,
        "email": normalize_email(email),
        "purpose": action,
        "code_hash": hash_otp(code),
        "expires_at": expires_at,
        "attempts": 0,
    }).execute()
    result = send_otp_via_emailjs(email, code, "recovery" if action == "recovery" else "signup")
    if not result.get("success"):
        # Never leave a usable OTP in Supabase when delivery failed.
        supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
            "id", otp_id
        ).execute()
        raise EmailDeliveryError(result.get("error", "email provider rejected OTP"))
    log_event(logger, logging.INFO, "otp_delivery_succeeded", action=action, recipient=mask_email(email))


def _generic_auth_message() -> str:
    return "إذا كان البريد صالحاً، فستصلك رسالة التحقق عبر البريد الإلكتروني"


@router.post("/register")
async def register(request: RegisterRequest):
    email = normalize_email(str(request.email))
    log_event(logger, logging.INFO, "registration_started", recipient=mask_email(email))
    display_name = request.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=422, detail="اسم العرض مطلوب")
    if not settings.AUTH_JWT_SECRET or not settings.AUTH_OTP_PEPPER:
        raise HTTPException(status_code=503, detail="خدمة المصادقة غير مهيأة")

    try:
        existing = get_user_by_email(email)
        if existing and existing.get("email_verified"):
            raise HTTPException(
                status_code=400,
                detail="هذا البريد الإلكتروني مسجل بالفعل. يرجى تسجيل الدخول بدلاً من ذلك."
            )
        if existing:
            user = existing
            supabase.table("custom_users").update({
                "password_hash": hash_password(request.password),
                "display_name": display_name,
                "email_verified": False,
                "updated_at": _now().isoformat(),
            }).eq("id", user["id"]).execute()
        else:
            user_id = str(uuid4())
            user = {
                "id": user_id,
                "email": email,
                "display_name": display_name,
                "password_hash": hash_password(request.password),
                "email_verified": False,
                "preferred_language": "ar",
            }
            supabase.table("custom_users").insert({
                **user,
                "created_at": _now().isoformat(),
                "updated_at": _now().isoformat(),
            }).execute()
        await run_in_threadpool(_issue_email_otp, user["id"], email, "signup")
    except EmailDeliveryError as error:
        logger.warning("email_delivery_failed code=%s", str(error))
        raise HTTPException(status_code=503, detail="تعذر إرسال رمز التحقق حاليًا. حاول لاحقًا.") from None
    except HTTPException:
        raise
    except Exception:
        logger.exception("custom_register_failed")
        raise HTTPException(status_code=503, detail="تعذر إنشاء الحساب حاليًا. حاول لاحقًا.") from None
    log_event(logger, logging.INFO, "registration_succeeded", recipient=mask_email(email))
    return {"success": True, "message": "تم إنشاء الحساب. تحقق من بريدك لإدخال رمز التأكيد."}


_login_limiter = UpstashRateLimiter(
    limit=10,
    window_seconds=900,
    fail_closed=os.getenv("NABEH_LOGIN_RATE_LIMIT_FAIL_CLOSED", "false").lower() in {"1", "true", "yes"},
)


@router.post("/login")
async def login(request: LoginRequest, response: Response, http_request: Request):
    log_event(logger, logging.INFO, "login_started", recipient=mask_email(str(request.email)))
    decision = await _login_limiter.check(client_identity(http_request))
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="تم تجاوز عدد محاولات الدخول. حاول لاحقًا.",
            headers={"Retry-After": str(decision.retry_after or 60), "Cache-Control": "no-store"},
        )
    try:
        user = get_user_by_email(normalize_email(str(request.email)))
        if not user or not user.get("email_verified") or user.get("status", "ACTIVE") != "ACTIVE" or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة")
        token = issue_access_token(user)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة") from None
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    log_event(logger, logging.INFO, "login_succeeded", recipient=mask_email(str(request.email)))
    return {"success": True, "data": {"access_token": token, "user_id": user["id"], "email": user["email"]}}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    log_event(logger, logging.INFO, "password_recovery_started", recipient=mask_email(str(request.email)))
    try:
        user = get_user_by_email(normalize_email(str(request.email)))
        if user and user.get("email_verified"):
            await run_in_threadpool(_issue_email_otp, user["id"], user["email"], "recovery")
    except Exception:
        logger.exception("custom_recovery_request_failed")
    log_event(logger, logging.INFO, "password_recovery_finished", recipient=mask_email(str(request.email)))
    return {"success": True, "message": "إذا كان البريد مسجلاً، فستصلك رسالة رمز الاستعادة"}


_resend_limiter = UpstashRateLimiter(
    limit=5,
    window_seconds=3600,
    fail_closed=os.getenv("NABEH_RATE_LIMIT_FAIL_CLOSED", "false").lower() in {"1", "true", "yes"},
)
_resend_cooldown_limiter = UpstashRateLimiter(
    limit=1,
    window_seconds=60,
    fail_closed=os.getenv("NABEH_RATE_LIMIT_FAIL_CLOSED", "false").lower() in {"1", "true", "yes"},
)


@router.post("/resend-otp")
async def resend_otp(request: ResendOtpRequest, http_request: Request):
    """Resend signup/recovery OTP without revealing account existence."""
    email = normalize_email(str(request.email))
    log_event(logger, logging.INFO, "otp_resend_started", action=request.type, recipient=mask_email(email))
    identity = f"{client_identity(http_request)}:{email}"
    cooldown_decision = await _resend_cooldown_limiter.check(identity)
    hourly_decision = await _resend_limiter.check(identity)
    decision = cooldown_decision if not cooldown_decision.allowed else hourly_decision
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="تم تجاوز عدد طلبات إعادة الإرسال. حاول لاحقًا.",
            headers={"Retry-After": str(decision.retry_after or 60), "Cache-Control": "no-store"},
        )

    try:
        user = get_user_by_email(email)
        if user and ((request.type == "signup" and not user.get("email_verified")) or (request.type == "recovery" and user.get("email_verified"))):
            await run_in_threadpool(_issue_email_otp, user["id"], email, request.type)
    except EmailDeliveryError as error:
        logger.warning("otp_resend_email_delivery_failed code=%s", str(error))
        raise HTTPException(status_code=503, detail="تعذر إرسال رمز التحقق حاليًا. حاول لاحقًا.") from None
    except Exception:
        logger.exception("otp_resend_failed")
        raise HTTPException(status_code=503, detail="تعذر إرسال رمز التحقق حاليًا. حاول لاحقًا.") from None

    log_event(logger, logging.INFO, "otp_resend_finished", action=request.type, recipient=mask_email(email))
    return {"success": True, "message": _generic_auth_message()}


@router.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest, response: Response):
    email = normalize_email(str(request.email))
    purpose = "recovery" if request.type == "recovery" else "signup"
    log_event(logger, logging.INFO, "otp_verification_started", purpose=purpose, recipient=mask_email(email))
    try:
        user = get_user_by_email(email)
        if not user:
            raise ValueError("unknown user")
        result = supabase.table("custom_auth_otps").select(
            "id,user_id,code_hash,expires_at,attempts,consumed_at"
        ).eq("user_id", user["id"]).eq("purpose", purpose).is_("consumed_at", "null").order(
            "created_at", desc=True
        ).limit(1).execute()
        otp = result.data[0] if result.data else None
        if not otp or int(otp.get("attempts", 0)) >= settings.AUTH_OTP_MAX_ATTEMPTS:
            raise ValueError("otp unavailable")
        if datetime.fromisoformat(otp["expires_at"].replace("Z", "+00:00")) <= _now():
            raise ValueError("otp expired")
        if not hmac.compare_digest(hash_otp(request.token), otp["code_hash"]):
            supabase.table("custom_auth_otps").update({"attempts": int(otp.get("attempts", 0)) + 1}).eq("id", otp["id"]).execute()
            raise ValueError("otp mismatch")
        supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq("id", otp["id"]).execute()
        if purpose == "signup":
            supabase.table("custom_users").update({"email_verified": True, "updated_at": _now().isoformat()}).eq("id", user["id"]).execute()
            token = issue_access_token({**user, "email_verified": True})
        else:
            token = issue_access_token(user, purpose="password_reset")
    except Exception:
        raise HTTPException(status_code=400, detail="رمز التحقق غير صالح أو منتهي الصلاحية") from None
    response.headers["Cache-Control"] = "no-store, private"
    log_event(logger, logging.INFO, "otp_verification_succeeded", purpose=purpose, recipient=mask_email(email))
    return {"success": True, "data": {"access_token": token, "purpose": purpose}}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, response: Response, authorization: Optional[str] = Header(None)):
    log_event(logger, logging.INFO, "password_reset_started")
    try:
        user = get_reset_user(_bearer_token(authorization))
        supabase.table("custom_users").update({
            "password_hash": hash_password(request.new_password),
            "updated_at": _now().isoformat(),
        }).eq("id", user["id"]).execute()
    except AuthSecurityError:
        raise HTTPException(status_code=401, detail="جلسة الاستعادة غير صالحة") from None
    except Exception:
        raise HTTPException(status_code=400, detail="تعذر تحديث كلمة المرور") from None
    response.headers["Cache-Control"] = "no-store, private"
    log_event(logger, logging.INFO, "password_reset_succeeded")
    return {"success": True, "message": "تم تحديث كلمة المرور بنجاح"}


@router.get("/me")
async def get_current_user_profile(response: Response, authorization: Optional[str] = Header(None)):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    try:
        user = get_authenticated_user(_bearer_token(authorization))
    except (AuthSecurityError, HTTPException):
        raise HTTPException(status_code=401, detail="جلسة غير صالحة") from None
    return {"success": True, "data": {
        "user_id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name") or user["email"].split("@", 1)[0],
        "preferred_language": user.get("preferred_language", "ar"),
        "role": user.get("role", "USER"),
        "status": user.get("status", "ACTIVE"),
        "email_verified": bool(user.get("email_verified")),
    }}
