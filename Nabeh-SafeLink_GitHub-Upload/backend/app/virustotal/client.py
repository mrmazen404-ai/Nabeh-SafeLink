"""
Async VirusTotal API Client for Nabeh SafeLink
Uses httpx.AsyncClient to prevent blocking the FastAPI event loop.
"""

import os
import base64
import asyncio
import httpx
from typing import Dict, Any


VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
VIRUSTOTAL_BASE_URL = "https://www.virustotal.com/api/v3"


def _get_headers() -> Dict[str, str]:
    return {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "Accept": "application/json",
    }


def _url_id(url: str) -> str:
    url_bytes = url.encode("utf-8")
    url_base64 = base64.urlsafe_b64encode(url_bytes).decode("utf-8")
    return url_base64.rstrip("=")


async def check_url_virustotal(url: str) -> Dict[str, Any]:
    """Check a URL against VirusTotal asynchronously using httpx."""
    if not VIRUSTOTAL_API_KEY:
        return {
            "status": "UNKNOWN",
            "confidence": 0.0,
            "error": "VIRUSTOTAL_API_KEY not set",
        }

    url_id = _url_id(url)
    endpoint = f"{VIRUSTOTAL_BASE_URL}/urls/{url_id}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(endpoint, headers=_get_headers())

            if response.status_code == 404:
                return await _submit_url(url, client)

            if response.status_code == 401:
                return {
                    "status": "UNKNOWN",
                    "confidence": 0.0,
                    "error": "Invalid API key (401)",
                }

            if response.status_code == 429:
                return {
                    "status": "UNKNOWN",
                    "confidence": 0.0,
                    "error": "Rate limit exceeded (429)",
                }

            if response.status_code != 200:
                return {
                    "status": "UNKNOWN",
                    "confidence": 0.0,
                    "error": f"HTTP {response.status_code}",
                }

            data = response.json()
            return _parse_response(data)

        except httpx.TimeoutException:
            return {"status": "UNKNOWN", "confidence": 0.0, "error": "Timeout"}
        except httpx.RequestError as e:
            return {"status": "UNKNOWN", "confidence": 0.0, "error": str(e)}
        except Exception as e:
            return {"status": "UNKNOWN", "confidence": 0.0, "error": f"Unexpected: {e}"}


async def _submit_url(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    """Submit a new URL to VirusTotal asynchronously."""
    endpoint = f"{VIRUSTOTAL_BASE_URL}/urls"

    try:
        response = await client.post(
            endpoint,
            headers=_get_headers(),
            data={"url": url},
        )

        if response.status_code not in (200, 201):
            return {
                "status": "UNKNOWN",
                "confidence": 0.0,
                "error": f"Submit failed: HTTP {response.status_code}",
            }

        await asyncio.sleep(10)

        url_id = _url_id(url)
        get_endpoint = f"{VIRUSTOTAL_BASE_URL}/urls/{url_id}"
        get_response = await client.get(get_endpoint, headers=_get_headers())
        if get_response.status_code == 200:
            return _parse_response(get_response.json())
        return {
            "status": "UNKNOWN",
            "confidence": 0.0,
            "error": "Pending analysis after submit",
        }

    except Exception as e:
        return {"status": "UNKNOWN", "confidence": 0.0, "error": str(e)}


def _parse_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse VirusTotal response with sanitized output."""
    try:
        attributes = data.get("data", {}).get("attributes", {})
        stats = attributes.get("last_analysis_stats", {})

        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)
        undetected = stats.get("undetected", 0)
        total = malicious + suspicious + harmless + undetected

        reputation = attributes.get("reputation", 0)
        categories = attributes.get("categories", {})

        if malicious >= 3:
            status = "DANGEROUS"
            confidence = min(1.0, malicious / 10.0)
        elif malicious >= 1 or suspicious >= 2:
            status = "SUSPICIOUS"
            confidence = 0.6
        elif harmless > 0 and malicious == 0:
            status = "SAFE"
            confidence = min(1.0, harmless / max(1, total))
        else:
            status = "UNKNOWN"
            confidence = 0.3

        return {
            "status": status,
            "confidence": round(confidence, 4),
            "malicious": malicious,
            "suspicious": suspicious,
            "harmless": harmless,
            "undetected": undetected,
            "total_engines": total,
            "reputation": reputation,
            "categories": categories,
        }

    except Exception as e:
        return {
            "status": "UNKNOWN",
            "confidence": 0.0,
            "error": f"Parse error: {e}",
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")

    test_urls = [
        "https://www.google.com",
        "https://www.youtube.com",
        "http://paypa1-login-verify.com/secure",
    ]

    async def main():
        print("=" * 70)
        print("Testing Async VirusTotal API")
        print("=" * 70)
        for u in test_urls:
            res = await check_url_virustotal(u)
            print(f"{u:<45} → {res.get('status')} (malicious={res.get('malicious', 0)})")

    asyncio.run(main())
