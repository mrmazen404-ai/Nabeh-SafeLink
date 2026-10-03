import hmac
import re
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, EmailStr, Field

from app.config import settings
from app.auth.emailjs import send_otp_via_emailjs
from app.db.supabase_client import supabase

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
    token: str = Field(min_length=6, max_length=8)
    type: Literal["signup", "recovery"] = "signup"


def _bearer_token(authorization: Optional[str]) -> str:
    parts = (authorization or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="جلسة غير صالحة")
    return parts[1]


@router.post("/send-email-hook")
async def send_email_webhook(request: Request, response: Response):
    """Protected Supabase hook; fail closed until a matching secret is configured."""
    expected_secret = settings.EMAILJS_HOOK_SECRET
    if not expected_secret:
        raise HTTPException(status_code=503, detail="خدمة البريد غير مهيأة")
    supplied = request.headers.get("authorization", "")
    expected = f"Bearer {expected_secret}"
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="غير مصرح")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="حمولة غير صالحة") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="حمولة غير صالحة")

    user_data = body.get("user") if isinstance(body.get("user"), dict) else {}
    email_data = body.get("email_data") if isinstance(body.get("email_data"), dict) else {}
    to_email = user_data.get("email") or email_data.get("email") or body.get("email")
    otp_code = email_data.get("token") or body.get("otp")
    action_type = email_data.get("email_action_type") or body.get("email_action_type")

    if not isinstance(to_email, str) or len(to_email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", to_email):
        raise HTTPException(status_code=400, detail="حمولة البريد غير صالحة")
    if not isinstance(otp_code, str) or not re.fullmatch(r"\d{6,8}", otp_code):
        raise HTTPException(status_code=400, detail="رمز التحقق غير صالح")
    if action_type not in {"signup", "recovery"}:
        raise HTTPException(status_code=400, detail="نوع الرسالة غير مدعوم")

    result = await run_in_threadpool(send_otp_via_emailjs, to_email, otp_code, action_type)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail="تعذر إرسال رسالة التحقق")
    response.headers["Cache-Control"] = "no-store, private"
    return {"success": True}


@router.post("/register")
async def register(request: RegisterRequest):
    message = "إذا كان البريد صالحاً، فستصلك تعليمات إكمال التسجيل"
    try:
        display_name = request.display_name.strip()
        result = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {"data": {"display_name": display_name, "preferred_language": "ar"}},
        })
        if result.user:
            try:
                supabase.table("user_profiles").upsert({
                    "user_id": result.user.id,
                    "display_name": display_name,
                    "preferred_language": "ar",
                }, on_conflict="user_id").execute()
            except Exception:
                # Avoid logging user identifiers or database/provider error text.
                pass
    except Exception:
        # Same response for existing and non-existing addresses to reduce enumeration.
        pass
    return {"success": True, "message": message}


@router.post("/login")
async def login(request: LoginRequest, response: Response):
    try:
        result = supabase.auth.sign_in_with_password({"email": request.email, "password": request.password})
    except Exception:
        raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة") from None
    if not result.session or not result.user:
        raise HTTPException(status_code=401, detail="البريد أو كلمة المرور غير صحيحة")
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return {
        "success": True,
        "data": {
            "access_token": result.session.access_token,
            "user_id": result.user.id,
            "email": result.user.email,
        },
    }


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        # Use the Supabase dashboard Site URL / Redirect URL allow-list; do not
        # hard-code localhost or accept a redirect target from the caller.
        supabase.auth.reset_password_for_email(request.email)
    except Exception:
        pass
    return {"success": True, "message": "إذا كان البريد مسجلاً، فستصلك تعليمات إعادة ضبط كلمة المرور"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    response: Response,
    authorization: Optional[str] = Header(None),
):
    token = _bearer_token(authorization)
    try:
        verified = supabase.auth.get_user(token)
        if not verified or not verified.user:
            raise HTTPException(status_code=401, detail="جلسة الاستعادة غير صالحة")
        # The target user ID comes only from the verified Supabase JWT, never the body.
        supabase.auth.admin.update_user_by_id(verified.user.id, {"password": request.new_password})
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="تعذر تحديث كلمة المرور؛ قد تكون جلسة الاستعادة منتهية") from None
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return {"success": True, "message": "تم تحديث كلمة المرور بنجاح"}


@router.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest, response: Response):
    if not re.fullmatch(r"\d{6,8}", request.token):
        raise HTTPException(status_code=400, detail="رمز التحقق غير صالح أو منتهي الصلاحية")
    try:
        result = supabase.auth.verify_otp({"email": request.email, "token": request.token, "type": request.type})
    except Exception:
        raise HTTPException(status_code=400, detail="رمز التحقق غير صالح أو منتهي الصلاحية") from None
    if not result.session or not result.user:
        raise HTTPException(status_code=400, detail="رمز التحقق غير صالح أو منتهي الصلاحية")
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    return {"success": True, "data": {"access_token": result.session.access_token}}


@router.get("/me")
async def get_current_user_profile(response: Response, authorization: Optional[str] = Header(None)):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    token = _bearer_token(authorization)
    try:
        user_result = supabase.auth.get_user(token)
        if not user_result or not user_result.user:
            raise HTTPException(status_code=401, detail="جلسة غير صالحة")
        user_id = user_result.user.id
        profile_result = supabase.table("user_profiles").select("display_name,preferred_language").eq("user_id", user_id).limit(1).execute()
        profile = profile_result.data[0] if profile_result.data else {}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="جلسة غير صالحة") from None
    email = user_result.user.email or ""
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "email": email,
            "display_name": profile.get("display_name", email.split("@", 1)[0]),
            "preferred_language": profile.get("preferred_language", "ar"),
        },
    }
