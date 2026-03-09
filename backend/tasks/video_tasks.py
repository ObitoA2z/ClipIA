# -*- coding: utf-8 -*-
"""Taches Celery operationnelles: scheduler, pipeline video, cleanup et performance."""

from __future__ import annotations

import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from random import randint
from typing import Any

from database.connection import insert_record, list_records, update_record
from services.audio_extractor import extract_audio
from services.cutter import cut_clips
from services.detector import detect_highlights
from services.downloader import download_video
from services.formatter import format_vertical
from services.performance_tracker import list_clip_performance, record_clip_performance
from services.publishing_service import publish_scheduled_post
from services.scheduler_service import process_due_posts
from services.transcriber import transcribe_audio
from services.uploader import upload_clips
from services.virality_scorer import enrich_highlights_with_virality
from tasks.celery_app import celery_app
from utils.helpers import new_id, resolve_temp_dir, utc_now_iso


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _set_video_state(video_id: str, status: str, progress: int, error: str | None = None) -> None:
    update_record(
        "videos",
        video_id,
        {
            "status": status,
            "progress_percent": progress,
            "error_message": error,
            "updated_at": utc_now_iso(),
        },
    )


def process_video_pipeline(video_id: str, payload: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Pipeline video synchrone reutilisable (Celery + fallback local)."""
    work_dir = ""
    try:
        _set_video_state(video_id, "downloading", 10)
        download_result = download_video(str(payload.get("youtube_url") or ""), video_id)
        work_dir = download_result.get("work_dir", "")

        update_record(
            "videos",
            video_id,
            {
                "title": download_result["title"],
                "duration_seconds": download_result["duration_seconds"],
                "thumbnail_url": download_result["thumbnail_url"],
                "source_mode": download_result.get("source_mode", "youtube"),
                "updated_at": utc_now_iso(),
            },
        )

        _set_video_state(video_id, "extracting", 22)
        audio_path = extract_audio(download_result["video_path"])

        _set_video_state(video_id, "transcribing", 35)
        transcript = transcribe_audio(audio_path)

        _set_video_state(video_id, "detecting", 55)
        highlights = detect_highlights(
            transcript,
            clip_mode=str(payload.get("clip_mode") or "talking"),
            user_prompt=str(payload.get("prompt") or "").strip(),
            video_path=download_result["video_path"],
            audio_path=audio_path,
            max_clips=int(payload.get("max_clips") or 8),
            min_duration=int(payload.get("min_duration") or 30),
            max_duration=int(payload.get("max_duration") or 90),
            target_platform=str(payload.get("target_platform") or "all"),
        )
        highlights = enrich_highlights_with_virality(
            highlights,
            total_duration=float(download_result.get("duration_seconds", 0) or 0),
            target_platform=str(payload.get("target_platform") or "all"),
            video_title=str(download_result.get("title") or ""),
        )

        _set_video_state(video_id, "cutting", 72)
        clips = cut_clips(
            download_result["video_path"],
            highlights,
            download_result.get("duration_seconds", 0),
        )

        _set_video_state(video_id, "formatting", 84)
        vertical_clips = format_vertical(clips, layout=str(payload.get("layout") or "centered"))

        _set_video_state(video_id, "uploading", 94)
        uploaded = upload_clips(video_id, vertical_clips)

        for clip_payload in uploaded:
            clip_id = new_id()
            clip_record = {
                "id": clip_id,
                "video_id": video_id,
                "user_id": user_id,
                **clip_payload,
                "created_at": utc_now_iso(),
            }
            insert_record("clips", clip_id, clip_record)

        _set_video_state(video_id, "done", 100)
        update_record("videos", video_id, {"clips_count": len(uploaded), "updated_at": utc_now_iso()})
        return {"video_id": video_id, "status": "done", "clips_count": len(uploaded)}
    except Exception as exc:
        _set_video_state(video_id, "error", 100, str(exc))
        return {"video_id": video_id, "status": "error", "error": str(exc)}
    finally:
        if work_dir and os.path.isdir(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="tasks.process_video_pipeline")
def process_video_pipeline_task(video_id: str, payload: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Task Celery principale pour le pipeline video."""
    return process_video_pipeline(video_id=video_id, payload=payload, user_id=user_id)


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
