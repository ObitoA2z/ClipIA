# -*- coding: utf-8 -*-
"""Routes clips."""

import io
import os
import re
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import requests

from database.connection import delete_record, get_record, list_records, update_record
from models.clip import ClipPublic
from services.audit import log_audit
from services.thumbnail_generator import generate_thumbnail_variants
from utils.auth import require_current_user
from utils.helpers import resolve_temp_dir
from utils.rate_limit import limiter

router = APIRouter(prefix="/clips", tags=["clips"])


class RecutClipRequest(BaseModel):
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)


class GenerateThumbnailRequest(BaseModel):
    hook: str | None = Field(default=None, max_length=120)
    target: str = Field(default="youtube", pattern="^(youtube|instagram)$")
    variants: int = Field(default=3, ge=1, le=5)


def _local_file_from_media_url(file_url: str) -> str:
    marker = "/media/"
    if marker not in file_url:
        return ""
    relative = file_url.split(marker, maxsplit=1)[1]
    return os.path.join(resolve_temp_dir(), relative.replace("/", os.sep))


def _media_url_from_local_path(path: str) -> str:
    base = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")
    root = resolve_temp_dir()
    relative = os.path.relpath(path, root).replace("\\", "/")
    return f"{base}/media/{relative}"


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", name or "").strip("._")
    return cleaned or "clip"


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


@router.get("/{video_id}/download-all")
def download_all_clips(video_id: str, current_user: dict = Depends(require_current_user)) -> StreamingResponse:
    video = get_record("videos", video_id)
    if not video or video.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Video introuvable")

    clips = [
        clip
        for clip in list_records("clips")
        if clip.get("video_id") == video_id and clip.get("user_id") == current_user["id"]
    ]
    if not clips:
        raise HTTPException(status_code=404, detail="Aucun clip a telecharger")

    archive_stream = io.BytesIO()
    with zipfile.ZipFile(archive_stream, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, clip in enumerate(clips, start=1):
            source_url = str(clip.get("file_url") or "")
            clip_title = _safe_filename(str(clip.get("title") or f"clip_{index}"))
            extension = ".mp4"
            if "." in source_url.rsplit("/", maxsplit=1)[-1]:
                extension = "." + source_url.rsplit(".", maxsplit=1)[-1].split("?", maxsplit=1)[0]
                if len(extension) > 8:
                    extension = ".mp4"

            output_name = f"{index:02d}_{clip_title}{extension}"
            local_path = _local_file_from_media_url(source_url)

            if local_path and os.path.isfile(local_path):
                with open(local_path, "rb") as file_obj:
                    archive.writestr(output_name, file_obj.read())
                continue

            try:
                response = requests.get(source_url, timeout=60)
                response.raise_for_status()
                archive.writestr(output_name, response.content)
            except Exception as exc:
                archive.writestr(f"{index:02d}_{clip_title}.error.txt", f"Download failed: {exc}")

        metadata_lines = [
            f"video_id={video_id}",
            f"user_id={current_user['id']}",
            f"clips={len(clips)}",
        ]
        archive.writestr("README.txt", "\n".join(metadata_lines))

    archive_stream.seek(0)
    filename = _safe_filename(str(video.get("title") or video_id))
    headers = {"Content-Disposition": f'attachment; filename="{filename}_clips.zip"'}
    return StreamingResponse(archive_stream, media_type="application/zip", headers=headers)


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


@router.post("/{clip_id}/thumbnails")
def create_clip_thumbnails(
    clip_id: str,
    payload: GenerateThumbnailRequest,
    current_user: dict = Depends(require_current_user),
) -> dict:
    clip = get_record("clips", clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip introuvable")
    if clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Accès refusé à ce clip")

    local_clip_path = _local_file_from_media_url(str(clip.get("file_url") or ""))
    if not local_clip_path or not os.path.isfile(local_clip_path):
        raise HTTPException(
            status_code=400,
            detail="Generation thumbnails disponible uniquement sur clips stockes localement",
        )

    output_dir = os.path.join(resolve_temp_dir(), "thumbnails", clip_id)
    variants = generate_thumbnail_variants(
        local_clip_path,
        output_dir,
        hook=payload.hook or clip.get("title") or "Top moment",
        creator_name=current_user.get("full_name") or "",
        target=payload.target,
        variants=payload.variants,
    )
    public_variants = [
        {
            **item,
            "url": _media_url_from_local_path(item["path"]),
        }
        for item in variants
    ]
    return {"thumbnails": public_variants}
