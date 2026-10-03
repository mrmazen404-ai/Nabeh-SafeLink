"""ASGI entrypoint for the Nabeh SafeLink Vercel deployment."""
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
BACKEND_ARCHIVE = ROOT / "backend_bundle.zip"
BACKEND_RUNTIME = Path("/tmp/nabeh_backend_bundle")

# The ML artifact is a real file inside the archive. Importing Python modules
# directly from a ZIP makes os.path.exists fail for that artifact, so extract
# the trusted deployment bundle before importing the FastAPI app.
if not BACKEND_RUNTIME.exists():
    BACKEND_RUNTIME.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BACKEND_ARCHIVE) as archive:
        archive.extractall(BACKEND_RUNTIME)

if str(BACKEND_RUNTIME) not in sys.path:
    sys.path.insert(0, str(BACKEND_RUNTIME))

from app.main import app  # noqa: E402

# Vercel promotes the built frontend directory to its CDN and keeps FastAPI
# routes (including /api/* and /health) ahead of the SPA navigation fallback.
app.frontend(
    "/",
    directory=str(ROOT / "frontend" / "dist"),
    fallback="index.html",
)
