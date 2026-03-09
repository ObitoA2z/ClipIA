# -*- coding: utf-8 -*-
"""Routes planification des publications."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import get_record
from services.scheduler_service import (
    cancel_scheduled_post,
    create_scheduled_post,
    delete_scheduled_post,
    list_scheduled_posts,
    retry_scheduled_post,
)
from utils.auth import require_current_user

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class ScheduledPostRequest(BaseModel):
    clip_id: str = Field(min_length=6)
    platform: str = Field(pattern="^(tiktok|reels|shorts|youtube|instagram|linkedin)$")
    scheduled_at: str = Field(min_length=10)
    title: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=2200)
    hashtags: list[str] = Field(default_factory=list)


@router.get("/events")
def list_scheduled_events(current_user: dict = Depends(require_current_user)) -> dict:
    events = list_scheduled_posts(current_user["id"])
    return {"events": events}


@router.post("/events")
def create_scheduled_event(
    payload: ScheduledPostRequest,
    current_user: dict = Depends(require_current_user),
) -> dict:
    clip = get_record("clips", payload.clip_id)
    if not clip or clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Clip introuvable")

    event = create_scheduled_post(
        user_id=current_user["id"],
        clip_id=payload.clip_id,
        platform=payload.platform,
        scheduled_at=payload.scheduled_at,
        title=payload.title,
        description=payload.description,
        hashtags=payload.hashtags,
    )
    return {"message": "Publication planifiee", "event": event}


@router.post("/events/{event_id}/cancel")
def cancel_event(event_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    if not cancel_scheduled_post(event_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Evenement introuvable")
    return {"message": "Publication annulee"}


@router.delete("/events/{event_id}")
def delete_event(event_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    if not delete_scheduled_post(event_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Evenement introuvable")
    return {"message": "Evenement supprime"}


@router.post("/events/{event_id}/retry")
def retry_event(event_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    event = retry_scheduled_post(event_id, current_user["id"])
    if not event:
        raise HTTPException(status_code=404, detail="Evenement introuvable ou non relancable")
    return {"message": "Publication relancee", "event": event}
