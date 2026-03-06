# -*- coding: utf-8 -*-
"""Detection des moments forts via Gemini avec fallback local."""

from __future__ import annotations

import json
import os
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential


def _infer_total_duration(transcript: dict) -> float:
    """Determine la duree totale a partir de la transcription."""
    explicit = float(transcript.get("duration_seconds") or 0.0)
    if explicit > 0:
        return explicit

    segments = transcript.get("segments", [])
    if not segments:
        return 60.0

    return max(float(segment.get("end", 0.0)) for segment in segments)


def _min_clip_duration(total_duration: float) -> float:
    """Fixe une duree mini selon la duree de video (plus souple sur videos courtes)."""
    if total_duration < 30:
        return 5.0
    return 20.0


def _sanitize_highlight(item: dict[str, Any], rank: int, total_duration: float) -> dict:
    """Valide et normalise un highlight issu d'une IA ou d'un fallback."""
    min_duration = _min_clip_duration(total_duration)
    max_duration = 120.0

    start = max(0.0, float(item.get("start", 0.0)))
    end = max(start + min_duration, float(item.get("end", start + min_duration)))

    if total_duration > 0:
        end = min(end, total_duration)
    if end <= start:
        end = start + min_duration

    duration = end - start
    if duration > max_duration:
        end = start + max_duration

    return {
        "rank": rank,
        "title": str(item.get("title") or f"Clip {rank}").strip(),
        "start": round(start, 3),
        "end": round(end, 3),
        "reason": str(item.get("reason") or "Moment pertinent pour une video courte.").strip(),
        "hook": str(item.get("hook") or "Extrait engageant").strip(),
    }


def _extract_json_array(text: str) -> list[dict]:
    """Extrait un tableau JSON depuis un texte libre."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    raw = text[start : end + 1]
    payload = json.loads(raw)
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def validate_clip_timestamps(
    start: float,
    end: float,
    *,
    min_duration: float = 20.0,
    max_duration: float = 120.0,
) -> bool:
    """Valide qu'un clip respecte les bornes de duree attendues."""
    start_value = float(start)
    end_value = float(end)
    if end_value <= start_value:
        return False
    duration = end_value - start_value
    return min_duration <= duration <= max_duration


def parse_gemini_response(raw_response: str) -> list[dict]:
    """Parse une reponse Gemini et renvoie la liste JSON nettoyee."""
    return _extract_json_array(raw_response)


def _fallback_highlights(transcript: dict) -> list[dict]:
    """Construit des highlights simples a partir des segments de transcription."""
    total_duration = _infer_total_duration(transcript)
    segments = transcript.get("segments", [])

    if not segments:
        return [
            _sanitize_highlight(
                {
                    "title": "Clip principal",
                    "start": 0.0,
                    "end": min(45.0, total_duration),
                    "reason": "Fallback sans transcription detaillee.",
                    "hook": "Extrait automatique",
                },
                rank=1,
                total_duration=total_duration,
            )
        ]

    highlights: list[dict] = []
    for index, segment in enumerate(segments[:8], start=1):
        start = max(0.0, float(segment.get("start", 0.0)) - 1.0)
        end = float(segment.get("end", start + _min_clip_duration(total_duration))) + 1.0

        highlights.append(
            _sanitize_highlight(
                {
                    "title": f"Clip {index} - Moment cle",
                    "start": start,
                    "end": end,
                    "reason": "Selection automatique basee sur la transcription.",
                    "hook": segment.get("text", "Extrait court"),
                },
                rank=index,
                total_duration=total_duration,
            )
        )

    return highlights


def _build_prompt(transcript: dict) -> str:
    """Construit le prompt strict pour forcer une sortie JSON exploitable."""
    return (
        "Voici la transcription d'une video YouTube avec timestamps. "
        "Identifie jusqu'a 8 extraits de 30 a 90 secondes ideaux pour TikTok/Reels/Shorts. "
        "Critere: moments surprenants, utiles, emotionnels, drles, ou tres engageants. "
        "Reponds UNIQUEMENT en JSON valide, sans markdown, format exact:\n"
        "[\n"
        "  {\n"
        "    \"rank\": 1,\n"
        "    \"title\": \"Titre\",\n"
        "    \"start\": 12.3,\n"
        "    \"end\": 58.4,\n"
        "    \"reason\": \"Pourquoi ce clip marche\",\n"
        "    \"hook\": \"Phrase d'accroche\"\n"
        "  }\n"
        "]\n\n"
        f"Transcription:\n{json.dumps(transcript, ensure_ascii=False)}"
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _detect_with_gemini(prompt: str, model_name: str) -> str:
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt, request_options={"timeout": 300})
    return getattr(response, "text", "") or ""


def detect_highlights(transcript: dict) -> list[dict]:
    """Detecte les meilleurs extraits via Gemini, sinon fallback local."""
    try:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        total_duration = _infer_total_duration(transcript)

        if not api_key:
            return _fallback_highlights(transcript)

        genai.configure(api_key=api_key)
        raw_text = _detect_with_gemini(_build_prompt(transcript), model_name=model_name)
        ai_items = parse_gemini_response(raw_text)
        if not ai_items:
            return _fallback_highlights(transcript)

        highlights: list[dict] = []
        for index, item in enumerate(ai_items[:8], start=1):
            highlights.append(_sanitize_highlight(item, rank=index, total_duration=total_duration))

        return highlights or _fallback_highlights(transcript)
    except Exception:
        return _fallback_highlights(transcript)
