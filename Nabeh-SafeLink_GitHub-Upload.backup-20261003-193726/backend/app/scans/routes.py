from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field

from app.auth.security import AuthSecurityError, get_authenticated_user
from app.scans.service import ScanPersistenceError, ScanService

router = APIRouter()


class ScanRequest(BaseModel):
    input_type: Literal["URL", "TEXT"] = "URL"
    input_value: str = Field(min_length=1, max_length=4096)
    language: Literal["ar", "en"] = "ar"


def _parse_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if authorization is None:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="جلسة غير صالحة")
    return parts[1]


async def get_optional_user_id(authorization: Optional[str] = None) -> Optional[str]:
    """Return a verified custom-auth user ID; malformed credentials fail closed."""
    token = _parse_bearer_token(authorization)
    if token is None:
        return None
    try:
        return str(get_authenticated_user(token)["id"])
    except AuthSecurityError:
        raise HTTPException(status_code=401, detail="جلسة غير صالحة") from None


async def get_required_user_id(authorization: Optional[str]) -> str:
    user_id = await get_optional_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="تسجيل الدخول مطلوب")
    return user_id


def _validate_input(request: ScanRequest) -> str:
    value = request.input_value.strip()
    if not value:
        raise HTTPException(status_code=400, detail="المدخل مطلوب")
    return value


@router.post("/guest")
async def create_guest_scan(request: ScanRequest, response: Response):
    """Run ML, VirusTotal, and Gemini for the guest without persistence."""
    raw_input = _validate_input(request)
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    result = await ScanService.process_guest_scan(
        input_type=request.input_type,
        raw_input=raw_input,
        language=request.language,
    )
    return {"success": True, "data": result}


@router.post("/")
async def create_authenticated_scan(
    request: ScanRequest,
    response: Response,
    authorization: Optional[str] = Header(None),
):
    """Persist a scan only for the account verified from the bearer token."""
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    raw_input = _validate_input(request)
    user_id = await get_required_user_id(authorization)
    try:
        result = await ScanService.process_authenticated_scan(
            input_type=request.input_type,
            raw_input=raw_input,
            user_id=user_id,
            language=request.language,
        )
    except ScanPersistenceError:
        raise HTTPException(status_code=503, detail="تعذر حفظ نتيجة الفحص") from None
    return {"success": True, "data": result}


@router.get("/")
async def get_scans(
    response: Response,
    authorization: Optional[str] = Header(None),
):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Pragma"] = "no-cache"
    user_id = await get_required_user_id(authorization)
    try:
        scans = await ScanService.get_recent_scans(limit=50, user_id=user_id)
    except Exception:
        raise HTTPException(status_code=503, detail="تعذر تحميل سجل الفحوصات") from None
    return {"success": True, "data": scans}
