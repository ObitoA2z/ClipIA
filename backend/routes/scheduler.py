# -*- coding: utf-8 -*-
"""Routes planification des publications."""


from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import delete_record, get_record, insert_record, list_records
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class ScheduledPostRequest(BaseModel):
    clip_id: str = Field(min_length=6)
    platform: str = Field(pattern="^(tiktok|reels|shorts|youtube)$")
    scheduled_at: str = Field(min_length=10)


@router.get("/events")
def list_scheduled_events(current_user: dict = Depends(require_current_user)) -> dict:
    events = [
        item
        for item in list_records("usage_logs")
        if item.get("type") == "scheduled_post" and item.get("user_id") == current_user["id"]
    ]
    events.sort(key=lambda row: row.get("scheduled_at", ""))
    return {"events": events}


@router.post("/events")
def create_scheduled_event(
    payload: ScheduledPostRequest,
    current_user: dict = Depends(require_current_user),
) -> dict:
    clip = get_record("clips", payload.clip_id)
    if not clip or clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Clip introuvable")

    event_id = new_id()
    event = {
        "id": event_id,
        "type": "scheduled_post",
        "user_id": current_user["id"],
        "clip_id": payload.clip_id,
        "platform": payload.platform,
        "scheduled_at": payload.scheduled_at,
        "status": "planned",
        "created_at": utc_now_iso(),
    }
    insert_record("usage_logs", event_id, event)
    return {"message": "Publication planifiee", "event": event}


@router.delete("/events/{event_id}")
def delete_scheduled_event(event_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    event = get_record("usage_logs", event_id)
    if not event or event.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Evenement introuvable")
    delete_record("usage_logs", event_id)
    return {"message": "Evenement supprime"}

