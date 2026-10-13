from __future__ import annotations

from typing import Callable

from fastapi import Header, HTTPException, Request

from app.admin.security import AdminSecurityError, decode_token
from app.db.supabase_client import supabase


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return authorization[7:].strip()


def current_admin(authorization: str | None = Header(None)) -> dict:
    try:
        claims = decode_token(bearer_token(authorization), "access")
        result = supabase.table("admin_users").select(
            "id,email,display_name,role,status,email_verified,two_factor_required,last_login_at,created_at,updated_at"
        ).eq("id", claims["sub"]).limit(1).execute()
        admin = result.data[0] if result.data else None
        if not admin or admin.get("status") != "ACTIVE" or not admin.get("email_verified"):
            raise HTTPException(status_code=401, detail="Admin session is inactive")
        return admin
    except HTTPException:
        raise
    except (AdminSecurityError, Exception):
        raise HTTPException(status_code=401, detail="Invalid admin authentication") from None


def require_roles(*roles: str) -> Callable:
    def dependency(admin: dict = __import__("fastapi").Depends(current_admin)) -> dict:
        if admin.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient administrator permissions")
        return admin
    return dependency


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")
