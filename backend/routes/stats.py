# -*- coding: utf-8 -*-
"""Routes statistiques publiques (cache 5 minutes)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import redis as redis_client
from fastapi import APIRouter, Depends

from database.connection import list_records
from utils.auth import require_current_user

router = APIRouter(prefix="/stats", tags=["stats"])

_LOCAL_CACHE: dict[str, object] = {"expires_at": None, "payload": None}
_CACHE_KEY = "clipai:stats:public"


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _today_key() -> str:
    return _utc_now().date().isoformat()


def _from_redis() -> dict | None:
    redis_url = ""
    try:
        import os

        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            return None
        client = redis_client.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
        raw = client.get(_CACHE_KEY)
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def _save_redis(payload: dict) -> None:
    try:
        import os

        redis_url = os.getenv("REDIS_URL", "").strip()
        if not redis_url:
            return
        client = redis_client.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.setex(_CACHE_KEY, 300, json.dumps(payload))
    except Exception:
        return


def _compute_public_stats() -> dict:
    today = _today_key()
    clips = list_records("clips")
    users = list_records("users")
    videos = list_records("videos")

    clips_today = 0
    for clip in clips:
        created = str(clip.get("created_at") or "")
        if created.startswith(today):
            clips_today += 1

    total_creators = len(users)
    clips_total = len(clips)
    videos_total = len(videos)

    return {
        "clips_today": clips_today,
        "total_creators": total_creators,
        "clips_total": clips_total,
        "videos_total": videos_total,
        "updated_at": _utc_now().isoformat(),
    }


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.get("/public")
def public_stats() -> dict:
    expires_at = _LOCAL_CACHE.get("expires_at")
    payload = _LOCAL_CACHE.get("payload")
    now = _utc_now()
    if isinstance(expires_at, datetime) and payload and now < expires_at:
        return payload  # type: ignore[return-value]

    redis_payload = _from_redis()
    if isinstance(redis_payload, dict):
        _LOCAL_CACHE["payload"] = redis_payload
        _LOCAL_CACHE["expires_at"] = now + timedelta(minutes=5)
        return redis_payload

    computed = _compute_public_stats()
    _LOCAL_CACHE["payload"] = computed
    _LOCAL_CACHE["expires_at"] = now + timedelta(minutes=5)
    _save_redis(computed)
    return computed


@router.get("/pipeline")
def pipeline_stats(current_user: dict = Depends(require_current_user)) -> dict:
    videos = [video for video in list_records("videos") if video.get("user_id") == current_user["id"]]
    status_breakdown: dict[str, int] = {}
    active_statuses = {
        "pending",
        "downloading",
        "extracting",
        "transcribing",
        "detecting",
        "cutting",
        "formatting",
        "uploading",
    }

    processing_active = 0
    done_count = 0
    error_count = 0
    durations_seconds: list[float] = []

    for video in videos:
        status = str(video.get("status") or "unknown")
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
        if status in active_statuses:
            processing_active += 1
        if status == "done":
            done_count += 1
            started = _parse_iso(video.get("created_at"))
            ended = _parse_iso(video.get("updated_at"))
            if started and ended and ended >= started:
                durations_seconds.append((ended - started).total_seconds())
        if status == "error":
            error_count += 1

    completed = done_count + error_count
    success_rate = round((done_count / completed) * 100, 2) if completed else None
    avg_processing_seconds = round(sum(durations_seconds) / len(durations_seconds), 2) if durations_seconds else None

    return {
        "total_videos": len(videos),
        "processing_active": processing_active,
        "done_count": done_count,
        "error_count": error_count,
        "success_rate_percent": success_rate,
        "avg_processing_seconds": avg_processing_seconds,
        "status_breakdown": status_breakdown,
        "updated_at": _utc_now().isoformat(),
    }
