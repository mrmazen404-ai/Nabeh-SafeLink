"""ASGI entrypoint for the Nabeh SafeLink Vercel deployment."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
BACKEND_ARCHIVE = ROOT / "backend_bundle.zip"
if str(BACKEND_ARCHIVE) not in sys.path:
    sys.path.insert(0, str(BACKEND_ARCHIVE))

from app.main import app  # noqa: E402

# Vercel promotes the built frontend directory to its CDN and keeps FastAPI
# routes (including /api/* and /health) ahead of the SPA navigation fallback.
app.frontend(
    "/",
    directory=str(ROOT / "frontend" / "dist"),
    fallback="index.html",
)
