# -*- coding: utf-8 -*-
"""Service musique de fond IA (mood detection + mix FFmpeg)."""

from __future__ import annotations

import os
import tempfile
from typing import Any

import requests

from utils.helpers import ffmpeg_binary, run_subprocess


MOOD_KEYWORDS = {
    "energetic": {"energie", "power", "motivation", "go", "sport", "challenge"},
    "calm": {"calme", "focus", "deep", "slow", "mind", "reflect"},
    "funny": {"drole", "funny", "meme", "blague", "lol"},
    "inspirational": {"histoire", "inspire", "growth", "succes", "mindset"},
}


def detect_mood(transcript_text: str, fallback: str = "inspirational") -> str:
    text = (transcript_text or "").lower()
    best_mood = fallback
    best_score = -1
    for mood, keywords in MOOD_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_mood = mood
            best_score = score
    return best_mood


def search_pixabay_music(mood: str, api_key: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Retourne une liste de pistes libres de droits depuis Pixabay Music."""
    endpoint = "https://pixabay.com/api/"
    params = {
        "key": api_key,
        "q": mood,
        "category": "music",
        "per_page": max(3, min(limit, 20)),
    }
    response = requests.get(endpoint, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("hits", []) or []


def _download_file(url: str, output_path: str) -> str:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    with open(output_path, "wb") as file:
        file.write(response.content)
    return output_path


def _pick_preview_url(track: dict[str, Any]) -> str:
    preview = track.get("previewURL")
    if preview:
        return str(preview)
    tags = track.get("tags", "")
    audio_files = track.get("audio_files") or {}
    for key in ("high", "medium", "low"):
        candidate = audio_files.get(key, {}).get("url")
        if candidate:
            return str(candidate)
    raise RuntimeError(f"No downloadable URL found for track (tags={tags})")


def mix_background_music(
    clip_path: str,
    music_path: str,
    *,
    output_path: str | None = None,
    music_volume: float = 0.15,
) -> str:
    """Mixe musique + voix originale en preservant l'audio principal."""
    if output_path is None:
        base_dir = os.path.dirname(clip_path)
        stem = os.path.splitext(os.path.basename(clip_path))[0]
        output_path = os.path.join(base_dir, f"{stem}_music.mp4")

    command = [
        ffmpeg_binary(),
        "-y",
        "-i",
        clip_path,
        "-i",
        music_path,
        "-filter_complex",
        f"[1:a]volume={music_volume:.3f}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map",
        "0:v:0",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        output_path,
    ]
    run_subprocess(command, timeout=1200)
    return output_path


def add_background_music(
    clip_path: str,
    *,
    transcript_text: str = "",
    mood: str | None = None,
    genre: str = "cinematic",
    music_volume: float = 0.15,
) -> dict[str, Any]:
    """Pipeline complet: mood -> recherche -> telechargement -> mixage."""
    mood_value = (mood or detect_mood(transcript_text)).strip().lower()
    query = f"{mood_value} {genre}".strip()

    api_key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not api_key:
        return {
            "status": "skipped",
            "reason": "missing_pixabay_api_key",
            "clip_path": clip_path,
        }

    tracks = search_pixabay_music(query, api_key)
    if not tracks:
        return {
            "status": "skipped",
            "reason": "no_track_found",
            "clip_path": clip_path,
            "query": query,
        }

    track = tracks[0]
    preview_url = _pick_preview_url(track)

    fd, tmp_music_path = tempfile.mkstemp(prefix="clipai_music_", suffix=".mp3")
    os.close(fd)

    try:
        _download_file(preview_url, tmp_music_path)
        mixed_path = mix_background_music(
            clip_path,
            tmp_music_path,
            music_volume=max(0.0, min(0.3, float(music_volume))),
        )
        return {
            "status": "ok",
            "clip_path": mixed_path,
            "mood": mood_value,
            "query": query,
            "track": {
                "id": track.get("id"),
                "tags": track.get("tags"),
                "user": track.get("user"),
            },
        }
    finally:
        if os.path.isfile(tmp_music_path):
            os.remove(tmp_music_path)
