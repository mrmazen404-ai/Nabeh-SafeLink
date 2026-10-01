"""Server-side EmailJS transport. Credentials are read only from server environment."""

import os
from typing import Any, Dict

import requests

EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY", "")
EMAILJS_PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY", "")
EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def send_otp_via_emailjs(to_email: str, otp_code: str, action_type: str = "signup") -> Dict[str, Any]:
    """Send a validated auth OTP without exposing provider responses or secrets in logs."""
    if not all((EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, EMAILJS_PUBLIC_KEY, EMAILJS_PRIVATE_KEY)):
        return {"success": False, "error": "email_delivery_not_configured"}
    if not to_email or len(to_email) > 254 or not otp_code or len(otp_code) > 8:
        return {"success": False, "error": "invalid_email_payload"}
    if action_type not in {"signup", "recovery"}:
        return {"success": False, "error": "unsupported_email_action"}

    action_label = "استعادة كلمة المرور" if action_type == "recovery" else "تأكيد الحساب"
    subject = "رمز استعادة كلمة المرور — نبيه SafeLink" if action_type == "recovery" else "رمز تأكيد حسابك — نبيه SafeLink"
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_email": to_email,
            "to_name": to_email.split("@", 1)[0],
            "otp": otp_code,
            "subject": subject,
            "app_name": "Nabeh SafeLink",
            "action_type": action_label,
        },
    }
    try:
        response = requests.post(
            EMAILJS_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            return {"success": True}
        return {"success": False, "error": "email_provider_rejected_request"}
    except requests.RequestException:
        return {"success": False, "error": "email_provider_unavailable"}
