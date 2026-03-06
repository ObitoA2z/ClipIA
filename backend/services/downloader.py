# -*- coding: utf-8 -*-
"""Service de telechargement video avec yt-dlp."""

from __future__ import annotations

import os

from yt_dlp import YoutubeDL

from utils.helpers import ffmpeg_binary, run_subprocess, video_work_dir


def get_video_metadata(youtube_url: str) -> dict:
    """Recupere les metadonnees d'une video YouTube sans la telecharger."""
    try:
        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        return {
            "title": info.get("title") or "Untitled video",
            "duration_seconds": int(info.get("duration") or 0),
            "thumbnail_url": info.get("thumbnail") or "",
            "uploader": info.get("uploader") or "",
        }
    except Exception as exc:
        raise RuntimeError(f"get_video_metadata failed: {exc}") from exc


def _find_downloaded_video(work_dir: str) -> str:
    """Trouve le fichier video principal telecharge par yt-dlp."""
    for extension in ("mp4", "mkv", "webm", "mov"):
        candidate = os.path.join(work_dir, f"original.{extension}")
        if os.path.exists(candidate):
            return candidate

    for filename in os.listdir(work_dir):
        if filename.lower().startswith("original."):
            return os.path.join(work_dir, filename)

    raise RuntimeError("Downloaded video file not found")


def _build_synthetic_video(work_dir: str, duration_seconds: int = 60) -> str:
    """Genere une video locale de secours si YouTube est inaccessible."""
    output_path = os.path.join(work_dir, "original.mp4")
    command = [
        ffmpeg_binary(),
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=1280x720:rate=30",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:sample_rate=44100",
        "-t",
        str(duration_seconds),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]
    run_subprocess(command, timeout=300)
    return output_path


def download_video(youtube_url: str, video_id: str) -> dict:
    """Telecharge la video YouTube dans un dossier local dedie au traitement."""
    try:
        try:
            metadata = get_video_metadata(youtube_url)
        except Exception:
            metadata = {
                "title": "Video importee",
                "duration_seconds": 60,
                "thumbnail_url": "",
                "uploader": "",
            }

        work_dir = video_work_dir(video_id)
        output_template = os.path.join(work_dir, "original.%(ext)s")

        options = {
            "format": "bv*[height<=720]+ba/b[height<=720]/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "fragment_retries": 3,
            "geo_bypass": True,
            "nocheckcertificate": True,
        }

        fallback_enabled = os.getenv("ALLOW_SYNTHETIC_FALLBACK", "true").strip().lower() == "true"

        try:
            with YoutubeDL(options) as ydl:
                ydl.extract_info(youtube_url, download=True)
            video_path = _find_downloaded_video(work_dir)
            source_mode = "youtube"
        except Exception as download_error:
            if not fallback_enabled:
                raise RuntimeError(download_error) from download_error
            video_path = _build_synthetic_video(
                work_dir=work_dir,
                duration_seconds=max(20, int(metadata.get("duration_seconds") or 60)),
            )
            source_mode = "synthetic_fallback"
            metadata["title"] = f"{metadata.get('title', 'Video')} (fallback local)"

        return {
            "video_path": video_path,
            "work_dir": work_dir,
            "title": metadata["title"],
            "duration_seconds": int(metadata.get("duration_seconds") or 60),
            "thumbnail_url": metadata["thumbnail_url"],
            "uploader": metadata["uploader"],
            "source_mode": source_mode,
        }
    except Exception as exc:
        raise RuntimeError(f"download_video failed: {exc}") from exc
