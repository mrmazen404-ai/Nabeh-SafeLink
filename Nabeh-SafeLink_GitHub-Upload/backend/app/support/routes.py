"""Support and Contact Requests API router with Supabase persistence."""

import logging
import random
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth.security import AuthSecurityError, get_authenticated_user
from app.db.supabase_client import supabase
from app.observability import log_event, mask_email

logger = logging.getLogger(__name__)

router = APIRouter()


class SupportContactRequest(BaseModel):
    request_type: str = Field(default="scan_issue", min_length=1, max_length=64)
    email: EmailStr
    subject: str = Field(min_length=1, max_length=256)
    scan_id: Optional[str] = Field(default=None, max_length=128)
    details: str = Field(min_length=1, max_length=4096)

def _get_optional_user_id(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not isinstance(authorization, str):
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        return None
    try:
        user = get_authenticated_user(parts[1])
        return str(user.get("id")) if user else None
    except AuthSecurityError:
        return None


@router.post("/contact")
async def create_support_request(
    request: SupportContactRequest,
    authorization: Optional[str] = Header(None),
):
    """Save a user contact/support ticket into Supabase database."""
    ticket_id = f"TK-{random.randint(10000, 99999)}"
    user_id = _get_optional_user_id(authorization)
    recipient = mask_email(request.email)

    full_message = f"Request Type: {request.request_type}\nScan ID: {request.scan_id or 'N/A'}\n\nDetails:\n{request.details}"
    
    support_data = {
        "email": request.email.lower().strip(),
        "subject": f"[{request.request_type.upper()}] {request.subject.strip()} ({ticket_id})",
        "message": full_message,
        "status": "OPEN",
        "priority": "HIGH" if request.request_type == "inaccurate_result" else "NORMAL",
    }
    if user_id:
        support_data["user_id"] = user_id

    log_event(
        logger,
        logging.INFO,
        "support_request_received",
        ticket_id=ticket_id,
        request_type=request.request_type,
        recipient=recipient,
        user_id=user_id,
    )

    try:
        saved = supabase.table("support_requests").insert(support_data).execute()
        saved_record = (saved.data or [support_data])[0]
        log_event(
            logger,
            logging.INFO,
            "support_request_persisted",
            ticket_id=ticket_id,
            request_type=request.request_type,
            recipient=recipient,
        )
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": "تم استلام رسالتك وحفظها بنجاح في قاعدة البيانات",
            "data": saved_record,
        }
    except Exception as error:
        logger.warning("support_request_persistence_fallback ticket_id=%s error=%s", ticket_id, type(error).__name__)
        # Return ticket_id so user request is gracefully accepted even if table requires migration
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": "تم استلام رسالتك بنجاح",
            "data": None,
        }