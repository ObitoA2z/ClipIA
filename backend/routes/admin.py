# -*- coding: utf-8 -*-
"""Routes admin (dashboard, users, pipeline, analytics)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from database.connection import get_record, list_records, update_record
from services.audit import log_audit
from utils.auth import require_current_user
from utils.helpers import utc_now_iso

router = APIRouter(prefix="/admin", tags=["admin"])


class PlanUpdateRequest(BaseModel):
    plan: str = Field(pattern="^(free|pro|business)$")


class UserStatusRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=240)


class UserEmailRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=120)
    message: str = Field(min_length=3, max_length=4000)


def _require_admin(user: dict = Depends(require_current_user)) -> dict:
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Acces admin requis")
    return user


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _series_last_months(month_count: int = 12) -> list[str]:
    now = _utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    labels = []
    for offset in range(month_count - 1, -1, -1):
        month = now
        for _ in range(offset):
            month = (month.replace(day=1) - timedelta(days=1)).replace(day=1)
        labels.append(month.strftime("%Y-%m"))
    return labels


def _safe_month(value: str | None) -> str:
    parsed = _parse_iso(value)
    if not parsed:
        return ""
    return parsed.strftime("%Y-%m")


def _safe_day(value: str | None) -> str:
    parsed = _parse_iso(value)
    if not parsed:
        return ""
    return parsed.strftime("%Y-%m-%d")


@router.get("/overview")
def admin_overview(current_admin: dict = Depends(_require_admin)) -> dict:
    users = list_records("users")
    videos = list_records("videos")
    clips = list_records("clips")
    active_subs = [sub for sub in list_records("subscriptions") if sub.get("status") == "active"]
    plan_counts = Counter([user.get("plan", "free") for user in users])

    mrr = plan_counts.get("pro", 0) * 19 + plan_counts.get("business", 0) * 49
    processing = len([video for video in videos if video.get("status") not in {"done", "error"}])

    months = _series_last_months(12)
    users_by_month = Counter(_safe_month(item.get("created_at")) for item in users if item.get("created_at"))
    subs_by_month = Counter(_safe_month(item.get("created_at")) for item in active_subs if item.get("created_at"))
    mrr_history = []
    running_users = 0
    running_subs = 0
    for label in months:
        running_users += int(users_by_month.get(label, 0))
        running_subs += int(subs_by_month.get(label, 0))
        mrr_history.append(
            {
                "month": label,
                "mrr": max(0, int((running_subs * 19) + (plan_counts.get("business", 0) * 49))),
                "new_users": int(users_by_month.get(label, 0)),
                "users_total": running_users,
            }
        )

    today = _utc_now().date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    users_by_day = Counter(_safe_day(item.get("created_at")) for item in users if item.get("created_at"))
    users_daily = [{"day": day, "users": int(users_by_day.get(day, 0))} for day in days]

    plan_distribution = [
        {"name": "Free", "value": int(plan_counts.get("free", 0))},
        {"name": "Pro", "value": int(plan_counts.get("pro", 0))},
        {"name": "Business", "value": int(plan_counts.get("business", 0))},
    ]

    previous_mrr = mrr_history[-2]["mrr"] if len(mrr_history) > 1 else mrr
    mrr_change_percent = round((((mrr - previous_mrr) / max(1, previous_mrr)) * 100), 2)

    return {
        "generated_at": utc_now_iso(),
        "kpis": {
            "mrr": mrr,
            "mrr_change_percent": mrr_change_percent,
            "users_total": len(users),
            "clips_total": len(clips),
            "videos_processing": processing,
            "subscriptions_active": len(active_subs),
        },
        "mrr_history": mrr_history,
        "users_daily": users_daily,
        "plan_distribution": plan_distribution,
        "requested_by": current_admin.get("id"),
    }


@router.get("/users")
def admin_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    plan: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=120),
    current_admin: dict = Depends(_require_admin),
) -> dict:
    users = list_records("users")
    if plan:
        users = [user for user in users if user.get("plan") == plan]

    if status == "deleted":
        users = [user for user in users if user.get("is_deleted")]
    elif status == "active":
        users = [user for user in users if not user.get("is_deleted") and not user.get("is_banned")]
    elif status == "suspended":
        users = [user for user in users if user.get("is_suspended")]
    elif status == "banned":
        users = [user for user in users if user.get("is_banned")]

    if search:
        term = search.strip().lower()
        users = [
            user
            for user in users
            if term in str(user.get("email", "")).lower() or term in str(user.get("full_name", "")).lower()
        ]

    users.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    page = users[skip : skip + limit]

    sessions = list_records("sessions")
    session_by_user: dict[str, str] = {}
    for session in sessions:
        user_id = str(session.get("user_id") or "")
        last_used = str(session.get("last_used_at") or "")
        if not user_id:
            continue
        if not session_by_user.get(user_id) or last_used > session_by_user[user_id]:
            session_by_user[user_id] = last_used

    normalized_items = []
    for user in page:
        normalized = dict(user)
        normalized["last_active_at"] = session_by_user.get(user["id"], "")
        normalized_items.append(normalized)

    return {
        "items": normalized_items,
        "total": len(users),
        "skip": skip,
        "limit": limit,
        "admin_id": current_admin["id"],
    }


@router.post("/users/{user_id}/plan")
def admin_update_user_plan(
    user_id: str,
    payload: PlanUpdateRequest,
    request: Request,
    current_admin: dict = Depends(_require_admin),
) -> dict:
    user = get_record("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    update_record("users", user_id, {"plan": payload.plan, "updated_at": utc_now_iso()})
    log_audit(
        action="admin.user.plan.updated",
        success=True,
        user_id=user_id,
        admin_id=current_admin["id"],
        resource_type="user",
        resource_id=user_id,
        request=request,
        metadata={"new_plan": payload.plan},
    )
    return {"message": "Plan mis a jour", "user_id": user_id, "plan": payload.plan}


@router.post("/users/{user_id}/suspend")
def admin_suspend_user(
    user_id: str,
    payload: UserStatusRequest,
    request: Request,
    current_admin: dict = Depends(_require_admin),
) -> dict:
    user = get_record("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    update_record(
        "users",
        user_id,
        {"is_suspended": True, "suspension_reason": payload.reason or "", "updated_at": utc_now_iso()},
    )
    log_audit(
        action="admin.user.suspended",
        success=True,
        user_id=user_id,
        admin_id=current_admin["id"],
        request=request,
        metadata={"reason": payload.reason or ""},
    )
    return {"message": "Utilisateur suspendu", "user_id": user_id}


@router.post("/users/{user_id}/unsuspend")
def admin_unsuspend_user(
    user_id: str,
    request: Request,
    current_admin: dict = Depends(_require_admin),
) -> dict:
    user = get_record("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    update_record(
        "users",
        user_id,
        {"is_suspended": False, "suspension_reason": "", "updated_at": utc_now_iso()},
    )
    log_audit(
        action="admin.user.unsuspended",
        success=True,
        user_id=user_id,
        admin_id=current_admin["id"],
        request=request,
    )
    return {"message": "Utilisateur reactive", "user_id": user_id}


@router.post("/users/{user_id}/ban")
def admin_ban_user(
    user_id: str,
    payload: UserStatusRequest,
    request: Request,
    current_admin: dict = Depends(_require_admin),
) -> dict:
    user = get_record("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    update_record(
        "users",
        user_id,
        {"is_banned": True, "ban_reason": payload.reason or "", "updated_at": utc_now_iso()},
    )
    log_audit(
        action="admin.user.banned",
        success=True,
        user_id=user_id,
        admin_id=current_admin["id"],
        request=request,
        metadata={"reason": payload.reason or ""},
    )
    return {"message": "Utilisateur banni", "user_id": user_id}


@router.post("/users/{user_id}/email")
def admin_send_user_email(
    user_id: str,
    payload: UserEmailRequest,
    request: Request,
    current_admin: dict = Depends(_require_admin),
) -> dict:
    user = get_record("users", user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    log_audit(
        action="admin.user.email.sent",
        success=True,
        user_id=user_id,
        admin_id=current_admin["id"],
        request=request,
        metadata={"subject": payload.subject},
    )
    return {"message": "Email mis en file", "user_id": user_id}


@router.get("/users/{user_id}/activity")
def admin_user_activity(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=300),
    current_admin: dict = Depends(_require_admin),
) -> dict:
    _ = current_admin
    logs = [
        row
        for row in list_records("audit_logs")
        if row.get("user_id") == user_id or row.get("admin_id") == user_id
    ]
    logs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"items": logs[:limit], "total": len(logs)}


@router.get("/pipeline")
def admin_pipeline(current_admin: dict = Depends(_require_admin)) -> dict:
    videos = list_records("videos")
    queue = [item for item in videos if item.get("status") not in {"done", "error"}]
    errors = [item for item in videos if item.get("status") == "error"]
    return {
        "queue_size": len(queue),
        "in_progress": queue,
        "errors": errors[:100],
        "workers_active": 1,
        "generated_at": utc_now_iso(),
        "admin_id": current_admin["id"],
    }


@router.get("/analytics")
def admin_analytics(current_admin: dict = Depends(_require_admin)) -> dict:
    users = list_records("users")
    videos = list_records("videos")
    clips = list_records("clips")
    plan_counts = Counter([user.get("plan", "free") for user in users])

    activation = 0
    for user in users:
        has_video = any(video.get("user_id") == user.get("id") for video in videos)
        if has_video:
            activation += 1
    activation_rate = round((activation / len(users)) * 100, 2) if users else 0.0

    return {
        "generated_at": utc_now_iso(),
        "users_total": len(users),
        "videos_total": len(videos),
        "clips_total": len(clips),
        "activation_rate_percent": activation_rate,
        "free_to_pro_conversion_percent": round(
            ((plan_counts.get("pro", 0) + plan_counts.get("business", 0)) / max(1, len(users))) * 100,
            2,
        ),
        "plan_distribution": dict(plan_counts),
        "admin_id": current_admin["id"],
    }


@router.get("/activity")
def admin_activity(
    limit: int = Query(default=50, ge=1, le=200),
    current_admin: dict = Depends(_require_admin),
) -> dict:
    logs = list_records("audit_logs")
    logs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    items: list[dict[str, Any]] = logs[:limit]
    return {"items": items, "total": len(logs), "admin_id": current_admin["id"]}
