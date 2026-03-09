# -*- coding: utf-8 -*-
"""AI Coach personnel base sur l'historique de clips."""

from __future__ import annotations

import json
import os
from statistics import mean
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential


def _normalize_clips(clips: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for clip in clips:
        normalized.append(
            {
                "title": str(clip.get("title") or "Clip").strip(),
                "duration_seconds": float(clip.get("duration_seconds") or 0.0),
                "score": int(clip.get("virality_score") or clip.get("score") or 60),
                "hook": str(clip.get("hook") or "").strip(),
            }
        )
    return normalized


def _heuristic_report(clips: list[dict[str, Any]], previous_score: int | None = None) -> dict[str, Any]:
    if not clips:
        return {
            "weekly_score": 0,
            "trend": "0 vs semaine precedente",
            "creator_style": "Style en apprentissage",
            "top_strength": "Pas assez de donnees",
            "top_weakness": "Publie plus de clips pour debloquer les insights",
            "this_week_tip": "Cree 3 clips cette semaine pour lancer le coaching IA.",
            "next_goal": "Generer 3 clips",
            "predicted_best_day": "Mardi",
            "predicted_best_time": "19h-21h",
            "topic_analysis": [],
        }

    avg_score = int(round(mean(item["score"] for item in clips)))
    avg_duration = mean(max(1.0, item["duration_seconds"]) for item in clips)
    previous = int(previous_score or avg_score)
    delta = avg_score - previous
    trend = f"{delta:+d} vs semaine precedente"

    if avg_duration > 60:
        weakness = "Tes clips sont trop longs pour maximiser la retention mobile."
        tip = "Vise 35-50 secondes pour les prochains clips."
    elif avg_duration < 25:
        weakness = "Certains clips sont trop courts pour installer le contexte."
        tip = "Vise 35-45 secondes avec un hook clair des 3 premieres secondes."
    else:
        weakness = "Tu peux mieux segmenter les sujets pour eviter les transitions brusques."
        tip = "Ajoute une phrase de transition forte avant la conclusion du clip."

    return {
        "weekly_score": avg_score,
        "trend": trend,
        "creator_style": "Contenu educatif et actionnable",
        "top_strength": "Hooks solides dans les premieres secondes.",
        "top_weakness": weakness,
        "this_week_tip": tip,
        "next_goal": "Publier 3 clips avec score > 75",
        "predicted_best_day": "Mardi",
        "predicted_best_time": "19h-21h",
        "topic_analysis": [
            {"topic": "Business", "score": max(45, min(95, avg_score + 3)), "note": "Bonne traction"},
            {"topic": "Productivite", "score": max(35, min(90, avg_score - 4)), "note": "A optimiser"},
        ],
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _coach_with_gemini(prompt: str, model_name: str) -> str:
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt, request_options={"timeout": 300})
    return getattr(response, "text", "") or ""


def generate_ai_coach_report(
    clips: list[dict[str, Any]],
    *,
    previous_score: int | None = None,
) -> dict[str, Any]:
    """Genere un rapport coach JSON via Gemini, fallback heuristique local."""
    normalized = _normalize_clips(clips)
    fallback = _heuristic_report(normalized, previous_score=previous_score)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or len(normalized) < 5:
        return fallback

    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        prompt = (
            "Analyse ces clips et genere strictement un JSON de coaching. "
            "Champs attendus: weekly_score, trend, creator_style, top_strength, top_weakness, "
            "this_week_tip, next_goal, predicted_best_day, predicted_best_time, topic_analysis.\n\n"
            f"Clips:\n{json.dumps(normalized, ensure_ascii=False)}"
        )
        raw = _coach_with_gemini(prompt, model_name)
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return fallback
        parsed = json.loads(raw[start : end + 1])
        if not isinstance(parsed, dict):
            return fallback

        report = {**fallback, **parsed}
        report["weekly_score"] = int(max(0, min(100, int(report.get("weekly_score", fallback["weekly_score"])))))
        return report
    except Exception:
        return fallback
