from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.auth.routes import router as auth_router
from app.scans.routes import router as scans_router
from app.statistics.routes import router as stats_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Nabeh SafeLink API — Intelligent Fraud Detection System",
)

if not settings.CORS_ALLOWED_ORIGINS or any(origin == "*" for origin in settings.CORS_ALLOWED_ORIGINS):
    raise RuntimeError("NABEH_CORS_ALLOWED_ORIGINS must contain explicit origins; wildcard is forbidden.")
for origin in settings.CORS_ALLOWED_ORIGINS:
    parsed_origin = urlsplit(origin)
    local_http = parsed_origin.scheme == "http" and parsed_origin.hostname in {"localhost", "127.0.0.1"}
    if not parsed_origin.netloc or (parsed_origin.scheme != "https" and not local_http) or parsed_origin.path:
        raise RuntimeError("Every CORS origin must be an HTTPS origin (localhost HTTP is development-only).")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(scans_router, prefix="/api/v1/scans", tags=["Scans"])
app.include_router(stats_router, prefix="/api/v1/statistics", tags=["Statistics"])


@app.get("/health")
def health():
    return {"status": "healthy"}
