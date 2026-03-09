# -*- coding: utf-8 -*-
"""Tracking performance post-publication des clips."""

from __future__ import annotations

from typing import Any

from database.connection import DATABASE, insert_record, list_records, update_record
from utils.helpers import new_id, utc_now_iso


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def ensure_performance_table() -> None:
    DATABASE.setdefault("clip_performance", {})


def compute_engagement_score(stats: dict[str, Any]) -> float:
    views = max(1, _safe_int(stats.get("views")))
    likes = _safe_int(stats.get("likes"))
    comments = _safe_int(stats.get("comments"))
    shares = _safe_int(stats.get("shares"))
    watch = _safe_float(stats.get("avg_watch_time_seconds"))
    return round(((likes * 1.0) + (comments * 2.0) + (shares * 3.0) + (watch * 0.2)) / views * 100.0, 3)


def record_clip_performance(
    *,
    clip_id: str,
    scheduled_post_id: str | None,
    platform: str,
    views: int = 0,
    likes: int = 0,
    comments: int = 0,
    shares: int = 0,
    avg_watch_time_seconds: float = 0.0,
) -> dict[str, Any]:
    ensure_performance_table()
    record_id = new_id()
    payload = {
        "id": record_id,
        "clip_id": clip_id,
        "scheduled_post_id": scheduled_post_id,
        "platform": platform,
        "views": _safe_int(views),
        "likes": _safe_int(likes),
        "comments": _safe_int(comments),
        "shares": _safe_int(shares),
        "avg_watch_time_seconds": _safe_float(avg_watch_time_seconds),
        "engagement_score": compute_engagement_score(
            {
                "views": views,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "avg_watch_time_seconds": avg_watch_time_seconds,
            }
        ),
        "fetched_at": utc_now_iso(),
    }
    insert_record("clip_performance", record_id, payload)
    return payload


def list_clip_performance(clip_id: str) -> list[dict[str, Any]]:
    ensure_performance_table()
    items = [item for item in list_records("clip_performance") if item.get("clip_id") == clip_id]
    items.sort(key=lambda row: row.get("fetched_at", ""), reverse=True)
    return items


def summarize_score_vs_views(limit: int = 30) -> dict[str, Any]:
    ensure_performance_table()
    rows = list_records("clip_performance")
    rows.sort(key=lambda row: row.get("fetched_at", ""), reverse=True)
    sample = rows[: max(1, limit)]
    if not sample:
        return {"count": 0, "avg_views": 0, "avg_engagement_score": 0.0, "insight": "Aucune donnee disponible"}

    total_views = sum(_safe_int(row.get("views")) for row in sample)
    avg_views = int(total_views / len(sample))
    avg_score = round(sum(_safe_float(row.get("engagement_score")) for row in sample) / len(sample), 3)

    insight = "Les clips a haut score convertissent bien."
    if avg_score < 3:
        insight = "Engagement bas: renforcer les hooks et CTA dans les 5 premieres secondes."
    elif avg_score > 8:
        insight = "Excellent engagement: dupliquer ce format sur les prochains clips."

    return {
        "count": len(sample),
        "avg_views": avg_views,
        "avg_engagement_score": avg_score,
        "insight": insight,
    }


def backfill_predicted_vs_actual(predicted_scores: dict[str, float]) -> dict[str, Any]:
    """Associe les scores predits aux performances pour analytics corrélation."""
    ensure_performance_table()
    rows = list_records("clip_performance")
    matched = 0
    deltas: list[float] = []

    for row in rows:
        clip_id = str(row.get("clip_id") or "")
        if clip_id not in predicted_scores:
            continue
        predicted = float(predicted_scores[clip_id])
        actual = float(row.get("engagement_score") or 0.0)
        row["predicted_score"] = predicted
        row["score_delta"] = round(actual - predicted, 3)
        update_record("clip_performance", row["id"], row)
        deltas.append(row["score_delta"])
        matched += 1

    average_delta = round(sum(deltas) / matched, 3) if matched else 0.0
    return {"matched": matched, "avg_delta": average_delta}
