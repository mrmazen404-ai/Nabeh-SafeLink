from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Response

from app.db.supabase_client import supabase
from app.scans.routes import get_required_user_id

router = APIRouter()


@router.get("/me")
async def get_my_statistics(
    response: Response,
    authorization: Optional[str] = Header(None),
):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    user_id = await get_required_user_id(authorization)

    try:
        result = (
            supabase.table("scans")
            .select("classification")
            .eq("user_id", user_id)
            .execute()
        )
        scans = result.data or []
    except Exception:
        raise HTTPException(status_code=503, detail="تعذر تحميل الإحصاءات") from None

    return {
        "success": True,
        "data": {
            "total": len(scans),
            "safe": sum(1 for scan in scans if scan.get("classification") == "SAFE"),
            "suspicious": sum(1 for scan in scans if scan.get("classification") == "SUSPICIOUS"),
            "dangerous": sum(1 for scan in scans if scan.get("classification") == "DANGEROUS"),
        },
    }
