# -*- coding: utf-8 -*-
"""Fonctions d'aide communes pour le backend."""

from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import datetime, timezone
from uuid import uuid4


def utc_now_iso() -> str:
    """Date/heure UTC en format ISO, utile pour tracer les statuts."""
    return datetime.now(tz=timezone.utc).isoformat()


def new_id() -> str:
    """Genere un identifiant unique lisible."""
    return str(uuid4())


def resolve_temp_dir() -> str:
    """Renvoie le dossier temporaire ClipAI (cross-platform via os.path.join)."""
    env_temp = os.getenv("TEMP_DIR", "").strip()
    if env_temp:
        return env_temp
    return os.path.join(tempfile.gettempdir(), "clipai")


def ensure_dir(path: str) -> str:
    """Cree le dossier si besoin et renvoie le chemin."""
    os.makedirs(path, exist_ok=True)
    return path


def video_work_dir(video_id: str) -> str:
    """Dossier de travail dedie a une video."""
    return ensure_dir(os.path.join(resolve_temp_dir(), video_id))


def ffmpeg_binary() -> str:
    """Renvoie le binaire ffmpeg configurable via variable d'environnement."""
    return os.getenv("FFMPEG_BIN", "ffmpeg")


def ffprobe_binary() -> str:
    """Renvoie le binaire ffprobe configurable via variable d'environnement."""
    return os.getenv("FFPROBE_BIN", "ffprobe")


def run_subprocess(
    command: list[str],
    *,
    timeout: int = 900,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute une commande externe et remonte une erreur exploitable en cas d'echec."""
    process = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )
    if process.returncode != 0:
        details = process.stderr.strip() or process.stdout.strip()
        raise RuntimeError(f"Command failed ({process.returncode}): {' '.join(command)} | {details}")
    return process


def probe_duration_seconds(media_path: str) -> float:
    """Lit la duree d'un media (video ou audio) avec ffprobe."""
    try:
        command = [
            ffprobe_binary(),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            media_path,
        ]
        result = run_subprocess(command, timeout=60)
        raw_value = (result.stdout or "").strip()
        return max(0.0, float(raw_value))
    except Exception:
        return 0.0
