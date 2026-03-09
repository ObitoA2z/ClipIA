# -*- coding: utf-8 -*-
"""Point d'entree FastAPI pour ClipAI."""

from __future__ import annotations

import os
import shutil
import threading
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
import redis as redis_client
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from supabase import create_client

from middleware.security import apply_security_middleware
from routes.admin import router as admin_router
from routes.ai_commands import router as ai_commands_router
from routes.ai_coach import router as ai_coach_router
from routes.auth import router as auth_router
from routes.brand import router as brand_router
from routes.clips import router as clips_router
from routes.content import router as content_router
from routes.feedback import router as feedback_router
from routes.gdpr import router as gdpr_router
from routes.notifications import router as notifications_router
from routes.payment import router as payment_router
from routes.publishing import router as publishing_router
from routes.referral import router as referral_router
from routes.scheduler import router as scheduler_router
from routes.stats import router as stats_router
from routes.teams import router as teams_router
from routes.video import router as video_router
from utils.helpers import ensure_dir, ffmpeg_binary, resolve_temp_dir, run_subprocess
from utils.rate_limit import limiter

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(
    title="ClipAI API",
    description="API locale ClipAI avec pipeline video reel.",
    version="0.2.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _check_ffmpeg() -> dict:
    try:
        result = run_subprocess([ffmpeg_binary(), "-version"], timeout=10)
        first_line = (result.stdout or "").splitlines()[0] if result.stdout else ""
        return {"status": "ok", "detail": first_line or "ffmpeg detecte"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_redis() -> dict:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379").strip()
    try:
        client = redis_client.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        return {"status": "ok", "detail": f"connecte sur {redis_url}"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_supabase() -> dict:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()
    if not supabase_url or not supabase_key:
        return {"status": "not_configured", "detail": "SUPABASE_URL/SUPABASE_KEY absents"}

    try:
        client = create_client(supabase_url, supabase_key)
        client.table("users").select("id").limit(1).execute()
        return {"status": "ok", "detail": "connexion valide"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def cleanup_old_temp_files(max_age_seconds: int = 7200) -> None:
    """Supprime les fichiers et dossiers temporaires vieux de plus de 2 heures."""
    root = ensure_dir(resolve_temp_dir())
    keep_dirs = {"published"}
    now = time.time()

    for name in os.listdir(root):
        if name in keep_dirs:
            continue

        path = os.path.join(root, name)
        try:
            modified_at = os.path.getmtime(path)
            if now - modified_at <= max_age_seconds:
                continue

            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        except Exception:
            continue


def _cleanup_worker() -> None:
    interval_seconds = 60 * 60
    while True:
        cleanup_old_temp_files(max_age_seconds=2 * 60 * 60)
        time.sleep(interval_seconds)


apply_security_middleware(app)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SlowAPIMiddleware)

media_dir = ensure_dir(resolve_temp_dir())
app.mount("/media", StaticFiles(directory=media_dir), name="media")

app.include_router(auth_router)
app.include_router(ai_commands_router)
app.include_router(ai_coach_router)
app.include_router(video_router)
app.include_router(clips_router)
app.include_router(brand_router)
app.include_router(payment_router)
app.include_router(publishing_router)
app.include_router(gdpr_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(referral_router)
app.include_router(scheduler_router)
app.include_router(feedback_router)
app.include_router(teams_router)
app.include_router(stats_router)
app.include_router(content_router)


@app.on_event("startup")
def startup_checks() -> None:
    ffmpeg_check = _check_ffmpeg()
    require_ffmpeg = os.getenv("REQUIRE_FFMPEG", "false").strip().lower() == "true"
    if require_ffmpeg and ffmpeg_check["status"] != "ok":
        raise RuntimeError(f"FFmpeg indisponible: {ffmpeg_check['detail']}")

    thread = threading.Thread(target=_cleanup_worker, daemon=True, name="clipai-temp-cleanup")
    thread.start()


@app.get("/")
def read_root() -> dict:
    """Renvoie un message simple pour verifier que l'API tourne."""
    return {"message": "ClipAI backend is running"}


@app.get("/health")
def healthcheck() -> dict:
    """Endpoint de sante simple pour supervision."""
    return {"status": "ok", "timestamp": _utc_now_iso()}


@app.get("/health/detailed")
def healthcheck_detailed() -> dict:
    checks = {
        "ffmpeg": _check_ffmpeg(),
        "redis": _check_redis(),
        "supabase": _check_supabase(),
    }
    all_ok = all(item["status"] == "ok" for item in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "timestamp": _utc_now_iso(),
        "checks": checks,
    }
