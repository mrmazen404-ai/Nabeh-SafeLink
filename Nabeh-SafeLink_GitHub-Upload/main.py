"""ASGI entrypoint for the Nabeh SafeLink deployment."""
from pathlib import Path
import sys
import zipfile

from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parent
LOCAL_BACKEND = ROOT / "backend"
BACKEND_ARCHIVE = ROOT / "backend_bundle.zip"
BACKEND_RUNTIME = Path("/tmp/nabeh_backend_bundle")

# Prefer local backend source if present for live development, otherwise extract bundle
if LOCAL_BACKEND.exists() and (LOCAL_BACKEND / "app").exists():
    if str(LOCAL_BACKEND) not in sys.path:
        sys.path.insert(0, str(LOCAL_BACKEND))
else:
    if not BACKEND_RUNTIME.exists():
        BACKEND_RUNTIME.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(BACKEND_ARCHIVE) as archive:
            archive.extractall(BACKEND_RUNTIME)

    if str(BACKEND_RUNTIME) not in sys.path:
        sys.path.insert(0, str(BACKEND_RUNTIME))

from app.main import app  # noqa: E402

# Keep API routes ahead of this SPA fallback.  FastAPI has no ``app.frontend``
# helper; serving the built files explicitly also makes local and Vercel
# behavior consistent.
FRONTEND_DIST = ROOT / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"


@app.get("/{full_path:path}", include_in_schema=False)
async def frontend_fallback(full_path: str):
    if not FRONTEND_INDEX.is_file():
        return JSONResponse({"detail": "Frontend build is unavailable"}, status_code=404)

    requested = (FRONTEND_DIST / full_path).resolve()
    try:
        requested.relative_to(FRONTEND_DIST.resolve())
    except ValueError:
        return JSONResponse({"detail": "Not found"}, status_code=404)

    if requested.is_file():
        return FileResponse(requested)
    return FileResponse(FRONTEND_INDEX)
