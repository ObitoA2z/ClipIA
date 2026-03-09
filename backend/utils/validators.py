# -*- coding: utf-8 -*-
"""Validation des URLs YouTube et extraction d'identifiant."""

import re
from urllib.parse import parse_qs, urlparse

YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,15}$")
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def _normalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if raw.startswith(("http://", "https://")):
        return raw
    return f"https://{raw}"


def _extract_id_from_parsed(parsed) -> str | None:
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").strip("/")

    if host in {"youtu.be", "www.youtu.be"}:
        candidate = path.split("/")[0]
        return candidate if YOUTUBE_ID_PATTERN.match(candidate) else None

    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        return None

    if path == "watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        return video_id if YOUTUBE_ID_PATTERN.match(video_id) else None

    parts = [segment for segment in path.split("/") if segment]
    if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live", "v"}:
        candidate = parts[1]
        return candidate if YOUTUBE_ID_PATTERN.match(candidate) else None

    return None


def is_valid_youtube_url(url: str) -> bool:
    """Verifie qu'une URL ressemble a une URL YouTube valide."""
    normalized = _normalize_url(url)
    if not normalized:
        return False
    try:
        parsed = urlparse(normalized)
    except Exception:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.netloc or "").lower()
    if host not in YOUTUBE_HOSTS:
        return False
    return _extract_id_from_parsed(parsed) is not None


def validate_youtube_url(url: str) -> bool:
    """Alias lisible utilise par les tests."""
    return is_valid_youtube_url(url)


def extract_youtube_id(url: str) -> str:
    """Extrait l'ID video YouTube depuis l'URL."""
    normalized = _normalize_url(url)
    if not normalized:
        raise ValueError("URL YouTube invalide")
    try:
        parsed = urlparse(normalized)
    except Exception as exc:
        raise ValueError("URL YouTube invalide") from exc

    video_id = _extract_id_from_parsed(parsed)
    if not video_id:
        raise ValueError("URL YouTube invalide")
    return video_id
