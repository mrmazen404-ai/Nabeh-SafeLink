"""Custom authentication: backend-generated OTP, EmailJS delivery, and JWT sessions."""

import base64
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


SYSTEM_PENDING_USER_ID = "00000000-0000-0000-0000-000000000000"


def _ensure_system_pending_user():
    """Ensure constant system pending user ID exists to satisfy custom_auth_otps FK constraint without creating unverified user records."""
    try:
        existing = supabase.table("custom_users").select("id").eq("id", SYSTEM_PENDING_USER_ID).limit(1).execute()
        if not existing.data:
            supabase.table("custom_users").insert({
                "id": SYSTEM_PENDING_USER_ID,
                "email": "system.pending@safelink.internal",
                "display_name": "System Pending Signup",
                "password_hash": "disabled",
                "email_verified": False,
                "preferred_language": "ar",
                "created_at": _now().isoformat(),
                "updated_at": _now().isoformat(),
            }).execute()
    except Exception:
        pass


def _issue_signup_otp(email: str, password_hash: str, display_name: str) -> None:
    """Store pending signup credentials in custom_auth_otps; custom_users remains untouched until OTP is verified."""
    _ensure_system_pending_user()
    log_event(logger, logging.INFO, "signup_otp_generation_started", recipient=mask_email(email))
    code = generate_otp()
    otp_id = str(uuid4())
    expires_at = (_now() + timedelta(minutes=settings.AUTH_OTP_MINUTES)).isoformat()

    otp_hash = hash_otp(code)
    b64_pass = base64.b64encode(password_hash.encode("utf-8")).decode("utf-8")
    b64_name = base64.b64encode(display_name.encode("utf-8")).decode("utf-8")
    composite_hash = f"signup${otp_hash}${b64_pass}${b64_name}"

    # Invalidate previous unconsumed signup OTPs for this email.
    supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
        "email", normalize_email(email)
    ).eq("purpose", "signup").is_("consumed_at", "null").execute()

    supabase.table("custom_auth_otps").insert({
        "id": otp_id,
        "user_id": SYSTEM_PENDING_USER_ID,
        "email": normalize_email(email),
        "purpose": "signup",
        "code_hash": composite_hash,
        "expires_at": expires_at,
        "attempts": 0,
    }).execute()

    result = send_otp_via_emailjs(email, code, "signup")
    if not result.get("success"):
        supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
            "id", otp_id
        ).execute()
        raise EmailDeliveryError(result.get("error", "email provider rejected OTP"))

    log_event(logger, logging.INFO, "signup_otp_delivery_succeeded", recipient=mask_email(email))


def _issue_recovery_otp(user_id: str, email: str) -> None:
    """Generate and store recovery OTP for existing verified users."""
    log_event(logger, logging.INFO, "recovery_otp_generation_started", recipient=mask_email(email))
    code = generate_otp()
    otp_id = str(uuid4())
    expires_at = (_now() + timedelta(minutes=settings.AUTH_OTP_MINUTES)).isoformat()

    otp_hash = hash_otp(code)
    composite_hash = f"recovery${otp_hash}"

    supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
        "user_id", user_id
    ).eq("purpose", "recovery").is_("consumed_at", "null").execute()

    supabase.table("custom_auth_otps").insert({
        "id": otp_id,
        "user_id": user_id,
        "email": normalize_email(email),
        "purpose": "recovery",
        "code_hash": composite_hash,
        "expires_at": expires_at,
        "attempts": 0,
    }).execute()

    result = send_otp_via_emailjs(email, code, "recovery")
    if not result.get("success"):
        supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
            "id", otp_id
        ).execute()
        raise EmailDeliveryError(result.get("error", "email provider rejected OTP"))

    log_event(logger, logging.INFO, "recovery_otp_delivery_succeeded", recipient=mask_email(email))


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

        # STRICT SECURITY POLICY: Do NOT create any record in custom_users before OTP verification!
        password_hash = hash_password(request.password)
        await run_in_threadpool(_issue_signup_otp, email, password_hash, display_name)
    except EmailDeliveryError as error:
        logger.warning("email_delivery_failed code=%s", str(error))
        raise HTTPException(status_code=503, detail="تعذر إرسال رمز التحقق حاليًا. حاول لاحقًا.") from None
    except HTTPException:
        raise
    except Exception:
        logger.exception("custom_register_failed")
        raise HTTPException(status_code=503, detail="تعذر معالجة الطلب حاليًا. حاول لاحقًا.") from None

    log_event(logger, logging.INFO, "registration_otp_issued", recipient=mask_email(email))
    return {"success": True, "message": "تم إرسال رمز التأكيد. تحقق من بريدك الإلكتروني لإكمال التسجيل."}


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
            await run_in_threadpool(_issue_recovery_otp, user["id"], user["email"])
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
    """Resend signup/recovery OTP without revealing account existence or creating unverified accounts."""
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
        if request.type == "signup":
            user = get_user_by_email(email)
            if user and user.get("email_verified"):
                return {"success": True, "message": _generic_auth_message()}

            result = supabase.table("custom_auth_otps").select(
                "id,code_hash"
            ).eq("email", email).eq("purpose", "signup").is_("consumed_at", "null").order(
                "created_at", desc=True
            ).limit(1).execute()

            otp = result.data[0] if result.data else None
            if otp:
                parts = otp["code_hash"].split("$")
                if len(parts) >= 4 and parts[0] == "signup":
                    _, _, b64_pass, b64_name = parts[0], parts[1], parts[2], parts[3]
                    password_hash = base64.b64decode(b64_pass.encode("utf-8")).decode("utf-8")
                    display_name = base64.b64decode(b64_name.encode("utf-8")).decode("utf-8")
                    await run_in_threadpool(_issue_signup_otp, email, password_hash, display_name)

        else:  # request.type == "recovery"
            user = get_user_by_email(email)
            if user and user.get("email_verified"):
                await run_in_threadpool(_issue_recovery_otp, user["id"], email)

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
    """Verify OTP code. Accounts are created in custom_users ONLY when signup OTP is valid!"""
    email = normalize_email(str(request.email))
    purpose = "recovery" if request.type == "recovery" else "signup"
    log_event(logger, logging.INFO, "otp_verification_started", purpose=purpose, recipient=mask_email(email))

    try:
        if purpose == "signup":
            existing_user = get_user_by_email(email)
            if existing_user and existing_user.get("email_verified"):
                token = issue_access_token(existing_user)
                response.headers["Cache-Control"] = "no-store, private"
                return {"success": True, "data": {"access_token": token, "purpose": purpose}}

            result = supabase.table("custom_auth_otps").select(
                "id,user_id,email,code_hash,expires_at,attempts,consumed_at"
            ).eq("email", email).eq("purpose", "signup").is_("consumed_at", "null").order(
                "created_at", desc=True
            ).limit(1).execute()

            otp = result.data[0] if result.data else None
            if not otp or int(otp.get("attempts", 0)) >= settings.AUTH_OTP_MAX_ATTEMPTS:
                raise ValueError("otp unavailable")
            if datetime.fromisoformat(otp["expires_at"].replace("Z", "+00:00")) <= _now():
                raise ValueError("otp expired")

            parts = otp["code_hash"].split("$")
            if len(parts) >= 4 and parts[0] == "signup":
                _, stored_otp_hash, b64_pass, b64_name = parts[0], parts[1], parts[2], parts[3]
                if not hmac.compare_digest(hash_otp(request.token), stored_otp_hash):
                    supabase.table("custom_auth_otps").update({"attempts": int(otp.get("attempts", 0)) + 1}).eq("id", otp["id"]).execute()
                    raise ValueError("otp mismatch")

                password_hash = base64.b64decode(b64_pass.encode("utf-8")).decode("utf-8")
                display_name = base64.b64decode(b64_name.encode("utf-8")).decode("utf-8")

                # NOW CREATE AND INSERT THE VERIFIED USER RECORD IN CUSTOM_USERS!
                user_id = str(uuid4())
                user = {
                    "id": user_id,
                    "email": email,
                    "display_name": display_name,
                    "password_hash": password_hash,
                    "email_verified": True,
                    "preferred_language": "ar",
                    "created_at": _now().isoformat(),
                    "updated_at": _now().isoformat(),
                }
                supabase.table("custom_users").insert(user).execute()
            else:
                # Fallback for legacy OTP format if present
                stored_hash = parts[-1]
                if not hmac.compare_digest(hash_otp(request.token), stored_hash):
                    supabase.table("custom_auth_otps").update({"attempts": int(otp.get("attempts", 0)) + 1}).eq("id", otp["id"]).execute()
                    raise ValueError("otp mismatch")
                user = get_user_by_email(email)
                if not user:
                    raise ValueError("unknown user")
                supabase.table("custom_users").update({"email_verified": True, "updated_at": _now().isoformat()}).eq("id", user["id"]).execute()

            supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq("id", otp["id"]).execute()
            token = issue_access_token(user)

        else:  # purpose == "recovery"
            user = get_user_by_email(email)
            if not user or not user.get("email_verified"):
                raise ValueError("unknown user")

            result = supabase.table("custom_auth_otps").select(
                "id,user_id,code_hash,expires_at,attempts,consumed_at"
            ).eq("user_id", user["id"]).eq("purpose", "recovery").is_("consumed_at", "null").order(
                "created_at", desc=True
            ).limit(1).execute()

            otp = result.data[0] if result.data else None
            if not otp or int(otp.get("attempts", 0)) >= settings.AUTH_OTP_MAX_ATTEMPTS:
                raise ValueError("otp unavailable")
            if datetime.fromisoformat(otp["expires_at"].replace("Z", "+00:00")) <= _now():
                raise ValueError("otp expired")

            stored_hash = otp["code_hash"].split("$")[-1]
            if not hmac.compare_digest(hash_otp(request.token), stored_hash):
                supabase.table("custom_auth_otps").update({"attempts": int(otp.get("attempts", 0)) + 1}).eq("id", otp["id"]).execute()
                raise ValueError("otp mismatch")

            supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq("id", otp["id"]).execute()
            token = issue_access_token(user, purpose="password_reset")

    except ValueError:
        raise HTTPException(status_code=400, detail="رمز التحقق غير صالح أو منتهي الصلاحية") from None
    except Exception:
        logger.exception("otp_verification_failed")
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
