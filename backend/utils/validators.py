# -*- coding: utf-8 -*-
"""Validation des URLs YouTube et extraction d'identifiant."""

import re

YOUTUBE_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([\w-]{6,})"
)


def is_valid_youtube_url(url: str) -> bool:
    """Vérifie qu'une URL ressemble à une URL YouTube valide."""
    return bool(YOUTUBE_PATTERN.search(url or ""))


def validate_youtube_url(url: str) -> bool:
    """Alias lisible utilisé par les tests."""
    return is_valid_youtube_url(url)


def extract_youtube_id(url: str) -> str:
    """Extrait l'ID vidéo YouTube depuis l'URL."""
    match = YOUTUBE_PATTERN.search(url or "")
    if not match:
        raise ValueError("URL YouTube invalide")
    return match.group(4)
