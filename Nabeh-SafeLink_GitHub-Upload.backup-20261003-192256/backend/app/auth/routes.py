"""Custom authentication: backend-generated OTP, EmailJS delivery, and JWT sessions."""

import hmac
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Response
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

logger = logging.getLogger(__name__)
router = APIRouter()


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


def _bearer_token(authorization: Optional[str]) -> str:
    parts = (authorization or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="جلسة غير صالحة")
    return parts[1]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _issue_email_otp(user_id: str, email: str, action: str) -> None:
    code = generate_otp()
    expires_at = (_now() + timedelta(minutes=settings.AUTH_OTP_MINUTES)).isoformat()
    # Invalidate previous codes before inserting the new one.
    supabase.table("custom_auth_otps").update({"consumed_at": _now().isoformat()}).eq(
        "user_id", user_id
    ).eq("purpose", action).is_("consumed_at", "null").execute()
    supabase.table("custom_auth_otps").insert({
        "id": str(uuid4()),
        "user_id": user_id,
        "email": normalize_email(email),
        "purpose": action,
        "code_hash": hash_otp(code),
        "expires_at": expires_at,
        "attempts": 0,
    }).execute()
    result = send_otp_via_emailjs(email, code, "recovery" if action == "recovery" else "signup")
    if not result.get("success"):
        raise RuntimeError("email provider rejected OTP")


def _generic_auth_message() -> str:
    return "إذا كان البريد صالحاً، فستصلك رسالة التحقق عبر البريد الإلكتروني"


@router.post("/register")
async def register(request: RegisterRequest):
    email = normalize_email(str(request.email))
    display_name = request.display_name.strip()
    if not display_name:
        raise HTTPException(status_code=422, detail="اسم العرض مطلوب")
    if not settings.AUTH_JWT_SECRET or not settings.AUTH_OTP_PEPPER:
        raise HTTPException(status_code=503, detail="خدمة المصادقة غير مهيأة")

    try:
        existing = get_user_by_email(email)
        if existing and existing.get("email_verified"):
            # Do not reveal whether an address is registered.
            return {"success": True, "message": _generic_auth_message()}
        if existing:
            user = existing
            supabase.table("custom_users").update({
                "password_hash": hash_password(request.password),
                "display_name": display_name,
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
            supabase.table("user_profiles").upsert({
                "user_id": user_id,
                "display_name": display_name,
                "preferred_language": "ar",
            }, on_conflict="user_id").execute()
        await run_in_threadpool(_issue_email_otp, user["id"], email, "signup")
    except HTTPException:
        raise
    except Exception:
        logger.exception("custom_register_failed")
        # Do not expose provider/database details or permit account enumeration.
    return {"success": True, "message": _generic_auth_message()}


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    try:
        user = get_user_by_email(normalize_email(str(request.email)))
        if not user or not user.get("email_verified") or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة")
        token = issue_access_token(user)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة") from None
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return {"success": True, "data": {"access_token": token, "user_id": user["id"], "email": user["email"]}}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        user = get_user_by_email(normalize_email(str(request.email)))
        if user and user.get("email_verified"):
            await run_in_threadpool(_issue_email_otp, user["id"], user["email"], "recovery")
    except Exception:
        logger.exception("custom_recovery_request_failed")
    return {"success": True, "message": "إذا كان البريد مسجلاً، فستصلك رسالة رمز الاستعادة"}


@router.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest, response: Response):
    email = normalize_email(str(request.email))
    purpose = "recovery" if request.type == "recovery" else "signup"
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
    return {"success": True, "data": {"access_token": token, "purpose": purpose}}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, response: Response, authorization: Optional[str] = Header(None)):
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
    }}
