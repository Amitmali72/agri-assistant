"""
Main FastAPI Application Entrypoint for KrishiMitra.
Serves API endpoints, static audio files, and the built React web application (when available).
"""

import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

from backend.config import settings
from backend.database.db import init_db, cleanup_expired_audio_files
from backend.api.routes import router as api_router
from backend.api.whatsapp import whatsapp_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agri_assistant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing KrishiMitra database and runtime directories...")
    init_db()

    base_dir = settings.BASE_DIR
    for d in [
        base_dir / "data" / "raw_pdfs",
        base_dir / "data" / "processed",
        base_dir / "vector_store",
        base_dir / "audio" / "uploads",
        base_dir / "audio" / "responses",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    try:
        purged = cleanup_expired_audio_files()
        if purged:
            logger.info(f"Privacy retention cleanup removed {purged} expired audio file(s).")
    except Exception as e:
        logger.warning(f"Audio retention cleanup check skipped: {e}")

    logger.info("Startup complete. KrishiMitra backend ready.")
    yield
    logger.info("Shutting down KrishiMitra backend.")


app = FastAPI(
    title="KrishiMitra: Voice-First Multilingual Agricultural Assistant",
    description=(
        "Production-grade AI agricultural assistant for Indian farmers. "
        "Supports Marathi & Hindi voice/text queries, hybrid RRF RAG over verified ICAR/KVK documents, "
        "live weather & mandi data, safety/confidence gating, WhatsApp webhook, and Admin Review Console."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response


# Mount audio static directory
audio_dir = settings.BASE_DIR / "audio"
audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Include API & WhatsApp routes
app.include_router(api_router)
app.include_router(whatsapp_router)

# Serve built React frontend if dist exists (single-command full-stack serving)
frontend_dist = Path(settings.FRONTEND_DIST_DIR)
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_spa_root():
        return FileResponse(str(frontend_dist / "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )
