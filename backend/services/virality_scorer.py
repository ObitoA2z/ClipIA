# -*- coding: utf-8 -*-
"""Scoring de viralite des clips avec IA + fallback heuristique."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential


CRITERIA = [
    "hook_strength",
    "emotional_impact",
    "clarity",
    "novelty",
    "pacing",
    "shareability",
    "retention_potential",
    "cta_strength",
]

PLATFORMS = {"tiktok", "reels", "shorts", "all"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _duration_score(duration_seconds: float) -> float:
    if 35 <= duration_seconds <= 55:
        return 85.0
    if 25 <= duration_seconds <= 70:
        return 72.0
    if 15 <= duration_seconds <= 90:
        return 58.0
    return 40.0


def _hook_score(text: str) -> float:
    lowered = (text or "").lower()
    score = 45.0
    if re.search(r"\b(comment|pourquoi|erreur|secret|astuce|hack|attention)\b", lowered):
        score += 18.0
    if re.search(r"\b\d+\b", lowered):
        score += 10.0
    if "?" in lowered:
        score += 8.0
    if len(lowered.strip()) > 120:
        score -= 6.0
    return _clamp(score, 20.0, 95.0)


def _position_score(start: float, total_duration: float) -> float:
    if total_duration <= 0:
        return 60.0
    ratio = _clamp(start / total_duration, 0.0, 1.0)
    # Souvent les meilleurs hooks sont entre 10% et 65% de la video.
    if 0.1 <= ratio <= 0.65:
        return 75.0
    if ratio < 0.1:
        return 62.0
    return 55.0


def _fallback_best_platform(duration_seconds: float, target_platform: str) -> str:
    target = (target_platform or "all").strip().lower()
    if target in {"tiktok", "reels", "shorts"}:
        return target
    if duration_seconds <= 45:
        return "tiktok"
    if duration_seconds <= 60:
        return "reels"
    return "shorts"


def _fallback_improvement_tip(score: float, duration_seconds: float) -> str:
    if score >= 80:
        return "Excellent clip: garde ce format et teste 2 variantes de miniature."
    if duration_seconds > 60:
        return "Raccourcis le clip a 35-55s et mets le hook dans les 3 premieres secondes."
    return "Renforce l'accroche et ajoute une conclusion claire orientee action."


def _fallback_score(
    *,
    title: str,
    hook_text: str,
    reason: str,
    start: float,
    end: float,
    total_duration: float,
    target_platform: str,
) -> dict[str, Any]:
    duration = max(1.0, end - start)
    duration_component = _duration_score(duration)
    hook_component = _hook_score(hook_text or title)
    position_component = _position_score(start, total_duration)
    clarity_component = _hook_score(reason) * 0.75

    base_score = (
        (duration_component * 0.24)
        + (hook_component * 0.28)
        + (position_component * 0.18)
        + (clarity_component * 0.14)
        + 14.0
    )
    score = round(_clamp(base_score, 0.0, 100.0), 2)

    sub_scores = {
        "hook_strength": round(_clamp(hook_component, 0.0, 100.0), 2),
        "emotional_impact": round(_clamp((hook_component * 0.8) + 10, 0.0, 100.0), 2),
        "clarity": round(_clamp(clarity_component, 0.0, 100.0), 2),
        "novelty": round(_clamp((hook_component * 0.65) + 12, 0.0, 100.0), 2),
        "pacing": round(_clamp(duration_component, 0.0, 100.0), 2),
        "shareability": round(_clamp((hook_component * 0.9) + 5, 0.0, 100.0), 2),
        "retention_potential": round(_clamp((position_component * 0.8) + 12, 0.0, 100.0), 2),
        "cta_strength": round(_clamp((clarity_component * 0.6) + 18, 0.0, 100.0), 2),
    }

    hook_output = (hook_text or title or "Moment fort").strip()[:160]
    return {
        "virality_score": score,
        "sub_scores": sub_scores,
        "hook_text": hook_output,
        "improvement_tip": _fallback_improvement_tip(score, duration),
        "best_platform": _fallback_best_platform(duration, target_platform),
    }


def _extract_json_object(raw: str) -> dict[str, Any]:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        parsed = json.loads(raw[start : end + 1])
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_prompt(
    *,
    title: str,
    hook_text: str,
    reason: str,
    start: float,
    end: float,
    total_duration: float,
    target_platform: str,
) -> str:
    return (
        "Tu es un scoreur viral short-form. "
        "Donne UNIQUEMENT un JSON valide avec: "
        "virality_score (0-100), sub_scores (8 criteres), hook_text, improvement_tip, best_platform. "
        "Les 8 sub_scores: hook_strength, emotional_impact, clarity, novelty, pacing, "
        "shareability, retention_potential, cta_strength.\n"
        "best_platform doit etre tiktok|reels|shorts.\n"
        f"Cible utilisateur: {target_platform}\n"
        f"Titre: {title}\n"
        f"Hook: {hook_text}\n"
        f"Reason: {reason}\n"
        f"Start: {start}\n"
        f"End: {end}\n"
        f"Video total duration: {total_duration}\n"
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _score_with_gemini(prompt: str, model_name: str) -> str:
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt, request_options={"timeout": 300})
    return getattr(response, "text", "") or ""


def score_clip_virality(
    *,
    title: str,
    hook_text: str,
    reason: str,
    start: float,
    end: float,
    total_duration: float,
    target_platform: str = "all",
) -> dict[str, Any]:
    """Score un clip et renvoie score + metadata (hook/improvement/platform)."""
    target = (target_platform or "all").strip().lower()
    if target not in PLATFORMS:
        target = "all"

    fallback = _fallback_score(
        title=title,
        hook_text=hook_text,
        reason=reason,
        start=start,
        end=end,
        total_duration=total_duration,
        target_platform=target,
    )

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback

    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        raw = _score_with_gemini(
            _build_prompt(
                title=title,
                hook_text=hook_text,
                reason=reason,
                start=start,
                end=end,
                total_duration=total_duration,
                target_platform=target,
            ),
            model_name=model_name,
        )
        payload = _extract_json_object(raw)
        if not payload:
            return fallback

        virality_score = round(_clamp(_safe_float(payload.get("virality_score"), fallback["virality_score"]), 0.0, 100.0), 2)
        ai_sub_scores = payload.get("sub_scores") or {}
        sub_scores = {}
        for criterion in CRITERIA:
            sub_scores[criterion] = round(
                _clamp(_safe_float(ai_sub_scores.get(criterion), fallback["sub_scores"][criterion]), 0.0, 100.0),
                2,
            )

        best_platform = str(payload.get("best_platform") or fallback["best_platform"]).strip().lower()
        if best_platform not in {"tiktok", "reels", "shorts"}:
            best_platform = fallback["best_platform"]

        hook_out = str(payload.get("hook_text") or fallback["hook_text"]).strip()[:160]
        tip = str(payload.get("improvement_tip") or fallback["improvement_tip"]).strip()[:240]

        return {
            "virality_score": virality_score,
            "sub_scores": sub_scores,
            "hook_text": hook_out or fallback["hook_text"],
            "improvement_tip": tip or fallback["improvement_tip"],
            "best_platform": best_platform,
        }
    except Exception:
        return fallback


def enrich_highlights_with_virality(
    highlights: list[dict[str, Any]],
    *,
    total_duration: float,
    target_platform: str = "all",
    video_title: str = "",
) -> list[dict[str, Any]]:
    """Ajoute les infos de viralite dans les highlights detectes."""
    enriched: list[dict[str, Any]] = []
    for item in highlights:
        scored = score_clip_virality(
            title=str(item.get("title") or video_title or "Clip"),
            hook_text=str(item.get("hook") or ""),
            reason=str(item.get("reason") or ""),
            start=_safe_float(item.get("start"), 0.0),
            end=_safe_float(item.get("end"), 0.0),
            total_duration=_safe_float(total_duration, 0.0),
            target_platform=target_platform,
        )
        enriched.append(
            {
                **item,
                "virality_score": scored["virality_score"],
                "sub_scores": scored["sub_scores"],
                "hook_text": scored["hook_text"],
                "improvement_tip": scored["improvement_tip"],
                "best_platform": scored["best_platform"],
            }
        )
    return enriched
