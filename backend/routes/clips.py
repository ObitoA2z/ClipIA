# -*- coding: utf-8 -*-
"""Routes clips."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from database.connection import delete_record, get_record, list_records, update_record
from models.clip import ClipPublic
from services.audit import log_audit
from utils.auth import require_current_user
from utils.rate_limit import limiter

router = APIRouter(prefix="/clips", tags=["clips"])


class RecutClipRequest(BaseModel):
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)


@router.get("/{video_id}", response_model=list[ClipPublic])
def list_clips(
    video_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(require_current_user),
) -> list[ClipPublic]:
    video = get_record("videos", video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video introuvable")
    if video.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé à cette vidéo")

    clips = [
        clip
        for clip in list_records("clips")
        if clip.get("video_id") == video_id and clip.get("user_id") == current_user["id"]
    ]
    clips.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    page = clips[skip : skip + limit]
    return [ClipPublic(**clip) for clip in page]


@router.get("/{clip_id}/download")
@limiter.limit("50/hour")
def download_clip(
    request: Request,
    clip_id: str,
    current_user: dict = Depends(require_current_user),
) -> dict:
    clip = get_record("clips", clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip introuvable")
    if clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé à ce clip")
    log_audit(
        action="clip.download",
        success=True,
        user_id=current_user["id"],
        resource_type="clip",
        resource_id=clip_id,
        request=request,
    )
    return {"download_url": clip["file_url"]}


@router.delete("/{clip_id}")
def delete_clip(clip_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    clip = get_record("clips", clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip introuvable")
    if clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé à ce clip")
    if not delete_record("clips", clip_id):
        raise HTTPException(status_code=404, detail="Clip introuvable")
    return {"message": "Clip supprimé"}


@router.post("/{clip_id}/recut")
def recut_clip(
    clip_id: str,
    payload: RecutClipRequest,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    clip = get_record("clips", clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip introuvable")
    if clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé à ce clip")
    if payload.end <= payload.start:
        raise HTTPException(status_code=400, detail="end doit etre superieur a start")

    duration = round(payload.end - payload.start, 2)
    updated = {
        "start_time": payload.start,
        "end_time": payload.end,
        "duration_seconds": duration,
    }
    update_record("clips", clip_id, updated)
    refreshed = get_record("clips", clip_id)
    from services.audit import log_audit

    log_audit(
        action="clip.recut",
        success=True,
        user_id=current_user["id"],
        resource_type="clip",
        resource_id=clip_id,
        request=request,
        metadata=updated,
    )
    return {"message": "Clip recoupe", "clip": refreshed}
