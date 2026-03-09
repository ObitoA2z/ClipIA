# -*- coding: utf-8 -*-
"""Taches Celery operationnelles: scheduler, cleanup et performance."""

from __future__ import annotations

import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from random import randint
from typing import Any

from database.connection import list_records
from services.performance_tracker import list_clip_performance, record_clip_performance
from services.publishing_service import publish_scheduled_post
from services.scheduler_service import process_due_posts
from services.virality_scorer import enrich_highlights_with_virality
from tasks.celery_app import celery_app
from utils.helpers import resolve_temp_dir


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="tasks.publish_scheduled_posts")
def publish_scheduled_posts() -> dict[str, Any]:
    """Publie les posts planifies arrives a echeance."""
    return process_due_posts(publish_scheduled_post)


@celery_app.task(name="tasks.cleanup_temp_files")
def cleanup_temp_files(max_age_seconds: int = 2 * 60 * 60) -> dict[str, Any]:
    """Supprime les fichiers temporaires vieux de plus de 2h."""
    root = resolve_temp_dir()
    if not os.path.isdir(root):
        return {"cleaned": 0, "root": root}

    now = time.time()
    cleaned = 0
    for name in os.listdir(root):
        if name == "published":
            continue
        path = os.path.join(root, name)
        try:
            age_seconds = now - os.path.getmtime(path)
            if age_seconds < max_age_seconds:
                continue
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
            cleaned += 1
        except Exception:
            continue

    return {"cleaned": cleaned, "root": root}


@celery_app.task(name="tasks.track_performance")
def track_performance() -> dict[str, Any]:
    """Simule le tracking post-publication pour les clips publies recemment."""
    published_posts = [
        post
        for post in list_records("scheduled_posts")
        if post.get("status") == "published"
    ]
    window_start = _utc_now() - timedelta(hours=72)
    processed = 0

    for post in published_posts:
        created_at_raw = str(post.get("updated_at") or post.get("created_at") or "")
        try:
            created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
        except Exception:
            created_at = _utc_now()
        if created_at < window_start:
            continue

        clip_id = str(post.get("clip_id") or "")
        if not clip_id:
            continue
        existing = list_clip_performance(clip_id)
        if existing:
            continue

        # Placeholder deterministic range for local env.
        views = randint(300, 45000)
        likes = int(views * 0.06)
        comments = int(views * 0.008)
        shares = int(views * 0.012)
        watch = round(randint(12, 54) + (randint(0, 100) / 100), 2)
        record_clip_performance(
            clip_id=clip_id,
            scheduled_post_id=post.get("id"),
            platform=str(post.get("platform") or "tiktok"),
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
            avg_watch_time_seconds=watch,
        )
        processed += 1

    return {"processed": processed}


@celery_app.task(name="tasks.score_highlights")
def score_highlights(
    highlights: list[dict[str, Any]],
    total_duration: float,
    target_platform: str = "all",
    video_title: str = "",
) -> list[dict[str, Any]]:
    """Task utilitaire pour scorer des highlights via virality_scorer."""
    return enrich_highlights_with_virality(
        highlights,
        total_duration=total_duration,
        target_platform=target_platform,
        video_title=video_title,
    )
