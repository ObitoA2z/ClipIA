# -*- coding: utf-8 -*-
"""Transcription audio via Groq Whisper avec fallback local."""

from __future__ import annotations

import os
from typing import Any

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.helpers import probe_duration_seconds


def _normalize_segments(raw_segments: list[Any]) -> list[dict]:
    """Normalise la liste de segments pour un format stable."""
    normalized: list[dict] = []
    for segment in raw_segments:
        if isinstance(segment, dict):
            start = float(segment.get("start", 0.0))
            end = float(segment.get("end", 0.0))
            text = str(segment.get("text", "")).strip()
        else:
            start = float(getattr(segment, "start", 0.0) or 0.0)
            end = float(getattr(segment, "end", 0.0) or 0.0)
            text = str(getattr(segment, "text", "") or "").strip()

        if end <= start:
            continue

        normalized.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
            }
        )
    return normalized


def _fallback_transcript(audio_path: str, reason: str = "fallback") -> dict:
    """Construit une transcription de secours si Groq n'est pas configure/disponible."""
    duration = probe_duration_seconds(audio_path)
    if duration <= 0:
        duration = 60.0

    chunk = 45.0
    segments: list[dict] = []
    cursor = 0.0
    index = 1
    while cursor < duration:
        end = min(duration, cursor + chunk)
        segments.append(
            {
                "start": round(cursor, 3),
                "end": round(end, 3),
                "text": f"Segment {index} genere en mode local ({reason}).",
            }
        )
        cursor = end
        index += 1

    text = " ".join(segment["text"] for segment in segments)
    return {
        "text": text,
        "segments": segments,
        "duration_seconds": round(duration, 3),
        "source": "fallback",
    }


def _parse_groq_response(response: Any) -> dict:
    """Convertit la reponse Groq en dictionnaire python utilisable."""
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    payload: dict = {
        "text": str(getattr(response, "text", "") or ""),
        "segments": getattr(response, "segments", []) or [],
    }
    return payload


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _transcribe_with_groq(audio_path: str, api_key: str, model_name: str) -> dict:
    client = Groq(api_key=api_key, timeout=300)
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model=model_name,
            response_format="verbose_json",
            temperature=0,
            timeout=300,
        )
    return _parse_groq_response(response)


def transcribe_audio(audio_path: str) -> dict:
    """Transcrit l'audio avec Groq Whisper (ou fallback local)."""
    try:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        model_name = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo").strip()

        if not api_key:
            return _fallback_transcript(audio_path, reason="missing_groq_api_key")
        payload = _transcribe_with_groq(audio_path, api_key, model_name)
        segments = _normalize_segments(payload.get("segments", []))

        if not segments:
            return _fallback_transcript(audio_path, reason="empty_groq_segments")

        transcript_text = str(payload.get("text", "") or "").strip()
        duration = max(segment["end"] for segment in segments)

        return {
            "text": transcript_text or " ".join(segment["text"] for segment in segments),
            "segments": segments,
            "duration_seconds": round(duration, 3),
            "source": "groq",
        }
    except Exception as exc:
        return _fallback_transcript(audio_path, reason=f"groq_error:{exc}")
