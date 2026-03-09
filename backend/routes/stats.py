# -*- coding: utf-8 -*-
"""Routes statistiques publiques (cache 5 minutes)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import redis as redis_client
from fastapi import APIRouter

from database.connection import list_records

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
