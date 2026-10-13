from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import supabase

router = APIRouter()

PolicyType = Literal["TERMS", "PRIVACY", "DISCLAIMER"]


def _get_policy(policy_type: str, language: str) -> dict:
    result = (
        supabase.table("policy_documents")
        .select("id,policy_type,language,version,title,content_markdown,content_hash,published_at")
        .eq("policy_type", policy_type)
        .eq("language", language)
        .eq("is_active", True)
        .order("published_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="الوثيقة القانونية غير متاحة")
    return result.data[0]


@router.get("/{policy_type}")
async def get_policy(
    policy_type: PolicyType,
    language: str = Query("ar", pattern="^(ar|en)$"),
):
    return {"success": True, "data": _get_policy(policy_type, language)}


@router.get("")
async def get_active_policies(language: str = Query("ar", pattern="^(ar|en)$")):
    result = (
        supabase.table("policy_documents")
        .select("id,policy_type,language,version,title,content_markdown,content_hash,published_at")
        .eq("language", language)
        .eq("is_active", True)
        .order("policy_type")
        .execute()
    )
    return {"success": True, "data": result.data or []}
