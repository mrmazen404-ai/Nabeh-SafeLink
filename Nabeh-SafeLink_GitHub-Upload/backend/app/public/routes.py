"""Privacy-preserving public metrics used by the Welcome page."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.db.supabase_client import supabase

router = APIRouter(prefix="/public", tags=["Public metrics"])


class VisitEvent(BaseModel):
    visitor_id: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    page: str = Field(default="welcome", min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_/-]+$")


def _visitor_hash(visitor_id: str) -> str:
    salt = settings.VISITOR_HASH_SALT or settings.AUTH_JWT_SECRET
    if not salt:
        raise HTTPException(status_code=503, detail="Visitor metrics are not configured")
    return hashlib.sha256(f"{salt}:{visitor_id}".encode()).hexdigest()


def _count(table: str, filters: list[tuple[str, str]] | None = None) -> int:
    query = supabase.table(table).select("id", count="exact", head=True)
    for column, value in filters or []:
        query = query.eq(column, value)
    result = query.execute()
    return int(result.count or 0)


@router.post("/visit", status_code=202)
def record_visit(event: VisitEvent):
    now = datetime.now(timezone.utc).isoformat()
    visitor_hash = _visitor_hash(event.visitor_id)
    # No raw identifier, IP, user-agent or cookie is stored. Upsert keeps one
    # privacy-preserving record per browser installation.
    supabase.table("site_visitors").upsert(
        {"visitor_hash": visitor_hash, "last_seen_at": now, "last_page": event.page},
        on_conflict="visitor_hash",
    ).execute()
    return {"success": True}


@router.get("/overview")
def public_overview():
    try:
        recent = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        total_visitors = _count("site_visitors")
        active_visitors = int(supabase.table("site_visitors").select("id", count="exact", head=True).gte("last_seen_at", recent).execute().count or 0)
        users = _count("custom_users", [("status", "ACTIVE")])
        scans = _count("scans")
        safe = _count("scans", [("classification", "SAFE")])
        suspicious = _count("scans", [("classification", "SUSPICIOUS")])
        dangerous = _count("scans", [("classification", "DANGEROUS")])
        return {"success": True, "data": {"visitors": total_visitors, "active_visitors_30d": active_visitors, "registered_users": users, "scans": scans, "safe_scans": safe, "suspicious_scans": suspicious, "dangerous_scans": dangerous, "generated_at": datetime.now(timezone.utc).isoformat()}}
    except Exception:
        raise HTTPException(status_code=503, detail="تعذر تحميل إحصائيات المنصة") from None
