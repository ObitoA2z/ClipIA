# -*- coding: utf-8 -*-
"""Routes admin (dashboard, utilisateurs, pipeline, analytics)."""


from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from database.connection import get_record, list_records, update_record
from services.audit import log_audit
from utils.auth import require_current_user
from utils.helpers import utc_now_iso

router = APIRouter(prefix="/admin", tags=["admin"])


class PlanUpdateRequest(BaseModel):
    plan: str = Field(pattern="^(free|pro|business)$")


def _require_admin(user: dict = Depends(require_current_user)) -> dict:
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Acces admin requis")
    return user


@router.get("/overview")
def admin_overview(current_admin: dict = Depends(_require_admin)) -> dict:
    users = list_records("users")
    videos = list_records("videos")
    clips = list_records("clips")
    active_subs = [sub for sub in list_records("subscriptions") if sub.get("status") == "active"]
    plan_counts = Counter([user.get("plan", "free") for user in users])

    mrr = plan_counts.get("pro", 0) * 19 + plan_counts.get("business", 0) * 49
    processing = len([video for video in videos if video.get("status") not in {"done", "error"}])

    return {
        "generated_at": utc_now_iso(),
        "kpis": {
            "mrr": mrr,
            "users_total": len(users),
            "clips_total": len(clips),
            "videos_processing": processing,
            "subscriptions_active": len(active_subs),
        },
        "plan_distribution": plan_counts,
        "requested_by": current_admin.get("id"),
    }


@router.get("/users")
def admin_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=200),
    plan: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_admin: dict = Depends(_require_admin),
) -> dict:
    users = list_records("users")
    if plan:
        users = [user for user in users if user.get("plan") == plan]
    if status == "deleted":
        users = [user for user in users if user.get("is_deleted")]
    elif status == "active":
        users = [user for user in users if not user.get("is_deleted")]

    users.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    page = users[skip : skip + limit]
    return {"items": page, "total": len(users), "skip": skip, "limit": limit, "admin_id": current_admin["id"]}


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


@router.get("/pipeline")
def admin_pipeline(current_admin: dict = Depends(_require_admin)) -> dict:
    videos = list_records("videos")
    queue = [item for item in videos if item.get("status") not in {"done", "error"}]
    errors = [item for item in videos if item.get("status") == "error"]
    return {
        "queue_size": len(queue),
        "in_progress": queue,
        "errors": errors[:50],
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
        "plan_distribution": plan_counts,
        "admin_id": current_admin["id"],
    }


@router.get("/activity")
def admin_activity(
    limit: int = Query(default=50, ge=1, le=200),
    current_admin: dict = Depends(_require_admin),
) -> dict:
    logs = list_records("audit_logs")
    logs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"items": logs[:limit], "total": len(logs), "admin_id": current_admin["id"]}

