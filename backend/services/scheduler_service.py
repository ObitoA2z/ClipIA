# -*- coding: utf-8 -*-
"""Scheduler service robuste: queue, retry, status publication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database.connection import delete_record, get_record, insert_record, list_records, update_record
from utils.helpers import new_id, utc_now_iso


MAX_ATTEMPTS = 3


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return _utc_now()


def create_scheduled_post(
    *,
    user_id: str,
    clip_id: str,
    platform: str,
    scheduled_at: str,
    title: str = "",
    description: str = "",
    hashtags: list[str] | None = None,
) -> dict[str, Any]:
    post_id = new_id()
    payload = {
        "id": post_id,
        "clip_id": clip_id,
        "user_id": user_id,
        "platform": platform,
        "scheduled_at": scheduled_at,
        "title": title,
        "description": description,
        "hashtags": hashtags or [],
        "status": "scheduled",
        "attempts": 0,
        "last_error": None,
        "published_url": None,
        "platform_post_id": None,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    insert_record("scheduled_posts", post_id, payload)
    return payload


def list_scheduled_posts(user_id: str) -> list[dict[str, Any]]:
    items = [row for row in list_records("scheduled_posts") if row.get("user_id") == user_id]
    items.sort(key=lambda row: row.get("scheduled_at", ""))
    return items


def cancel_scheduled_post(post_id: str, user_id: str) -> bool:
    post = get_record("scheduled_posts", post_id)
    if not post or post.get("user_id") != user_id:
        return False
    update_record(
        "scheduled_posts",
        post_id,
        {"status": "cancelled", "updated_at": utc_now_iso()},
    )
    return True


def due_scheduled_posts() -> list[dict[str, Any]]:
    now = _utc_now()
    rows = list_records("scheduled_posts")
    due = []
    for row in rows:
        if row.get("status") not in {"scheduled", "failed"}:
            continue
        if int(row.get("attempts", 0)) >= MAX_ATTEMPTS:
            continue
        when = _parse_dt(str(row.get("scheduled_at") or ""))
        if when <= now:
            due.append(row)
    due.sort(key=lambda row: row.get("scheduled_at", ""))
    return due


def mark_publish_success(
    post_id: str,
    *,
    platform_post_id: str,
    published_url: str,
) -> dict[str, Any] | None:
    return update_record(
        "scheduled_posts",
        post_id,
        {
            "status": "published",
            "platform_post_id": platform_post_id,
            "published_url": published_url,
            "last_error": None,
            "updated_at": utc_now_iso(),
        },
    )


def mark_publish_failure(post_id: str, error_message: str) -> dict[str, Any] | None:
    post = get_record("scheduled_posts", post_id)
    if not post:
        return None
    attempts = int(post.get("attempts", 0)) + 1
    next_status = "failed" if attempts < MAX_ATTEMPTS else "error"

    delay_minutes = 2 ** max(0, attempts - 1)
    next_try = _utc_now() + timedelta(minutes=delay_minutes)

    return update_record(
        "scheduled_posts",
        post_id,
        {
            "status": next_status,
            "attempts": attempts,
            "last_error": error_message,
            "scheduled_at": next_try.isoformat(),
            "updated_at": utc_now_iso(),
        },
    )


def process_due_posts(publisher_callback) -> dict[str, Any]:
    """Execute les posts dus avec retry exponentiel.

    publisher_callback(post) doit retourner dict avec:
      {"ok": bool, "post_id": "...", "url": "...", "error": "..."}
    """
    due = due_scheduled_posts()
    report = {"total": len(due), "published": 0, "failed": 0, "errors": []}

    for post in due:
        result = publisher_callback(post)
        if result.get("ok"):
            mark_publish_success(
                post["id"],
                platform_post_id=str(result.get("post_id") or ""),
                published_url=str(result.get("url") or ""),
            )
            report["published"] += 1
        else:
            mark_publish_failure(post["id"], str(result.get("error") or "publish_failed"))
            report["failed"] += 1
            report["errors"].append({"id": post["id"], "error": result.get("error")})

    return report


def delete_scheduled_post(post_id: str, user_id: str) -> bool:
    post = get_record("scheduled_posts", post_id)
    if not post or post.get("user_id") != user_id:
        return False
    return delete_record("scheduled_posts", post_id)
