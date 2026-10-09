import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.auth.routes import router as auth_router
from app.scans.routes import router as scans_router
from app.statistics.routes import router as stats_router
from app.dashboard.routes import router as dashboard_router
from app.support.routes import router as support_router
from app.observability import configure_logging, elapsed_ms, install_request_id_filter, log_event, reset_request_id, set_request_id

configure_logging()
install_request_id_filter()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def application_lifespan(_app: FastAPI):
    log_event(
        logger,
        logging.INFO,
        "application_started",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        cors_origins=len(settings.CORS_ALLOWED_ORIGINS),
    )
    yield
    log_event(logger, logging.INFO, "application_stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Nabeh SafeLink API — Intelligent Fraud Detection System",
    lifespan=application_lifespan,
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
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(scans_router, prefix="/api/v1/scans", tags=["Scans"])
app.include_router(stats_router, prefix="/api/v1/statistics", tags=["Statistics"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(support_router, prefix="/api/v1/support", tags=["Support"])


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_token = set_request_id(request.headers.get("x-request-id") or str(uuid4()))
    started = time.perf_counter()
    log_event(logger, logging.INFO, "request_started", method=request.method, path=request.url.path)
    response = None
    try:
        response = await call_next(request)
        log_event(
            logger,
            logging.INFO if response.status_code < 400 else logging.WARNING,
            "request_finished",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=elapsed_ms(started),
        )
        response.headers["X-Request-ID"] = request.headers.get("x-request-id") or request_id_for_header()
        return response
    except Exception as error:
        log_event(
            logger,
            logging.ERROR,
            "request_failed",
            method=request.method,
            path=request.url.path,
            error_type=type(error).__name__,
            duration_ms=elapsed_ms(started),
        )
        raise
    finally:
        reset_request_id(request_token)


def request_id_for_header() -> str:
    """Read the current request id without exposing implementation details."""
    from app.observability import request_id

    return request_id()


@app.get("/health")
@app.get("/api/v1/health")
def health():
    return {"status": "healthy"}


# Local production-like mode: one URL serves both the built React app and the API.
# Vercel and Vite deployments can continue to use their own frontend serving path.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

if FRONTEND_INDEX.is_file():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def frontend_root():
        return FileResponse(FRONTEND_INDEX)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def frontend_spa(full_path: str):
        if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json", "health"}:
            raise HTTPException(status_code=404, detail="Not found")
        requested = (FRONTEND_DIST / full_path).resolve()
        if requested.is_file() and FRONTEND_DIST.resolve() in requested.parents:
            media_type = None
            if requested.suffix == ".css":
                media_type = "text/css"
            elif requested.suffix == ".js":
                media_type = "application/javascript"
            elif requested.suffix == ".svg":
                media_type = "image/svg+xml"
            elif requested.suffix == ".json":
                media_type = "application/json"
            return FileResponse(requested, media_type=media_type)
        if FRONTEND_INDEX.is_file():
            return FileResponse(FRONTEND_INDEX)
        raise HTTPException(status_code=404, detail="Not found")
