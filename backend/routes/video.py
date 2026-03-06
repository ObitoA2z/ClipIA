# -*- coding: utf-8 -*-
"""Routes video avec pipeline reelle (yt-dlp + ffmpeg + IA optionnelle)."""

import asyncio
import os
import shutil

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from database.connection import delete_record, get_record, insert_record, list_records, update_record
from models.video import ProcessVideoRequest, VideoStatus
from services.audio_extractor import extract_audio
from services.cutter import cut_clips
from services.detector import detect_highlights
from services.downloader import download_video, get_video_metadata
from services.formatter import format_vertical
from services.transcriber import transcribe_audio
from services.uploader import upload_clips
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso
from utils.rate_limit import limiter
from utils.validators import extract_youtube_id, is_valid_youtube_url

router = APIRouter(prefix="/video", tags=["video"])
processing_tasks: dict[str, asyncio.Task] = {}


def _video_or_404(video_id: str, user_id: str) -> dict:
    video = get_record("videos", video_id)
    if not video or video.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Video introuvable")
    return video


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


async def _process_video(video_id: str, youtube_url: str, user_id: str) -> None:
    """Lance la pipeline de traitement en arriere-plan."""
    work_dir = ""
    try:
        _set_video_state(video_id, "downloading", 10)
        download_result = await asyncio.to_thread(download_video, youtube_url, video_id)
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

        _set_video_state(video_id, "transcribing", 30)
        audio_path = await asyncio.to_thread(extract_audio, download_result["video_path"])
        transcript = await asyncio.to_thread(transcribe_audio, audio_path)

        _set_video_state(video_id, "detecting", 55)
        highlights = await asyncio.to_thread(detect_highlights, transcript)

        _set_video_state(video_id, "cutting", 72)
        clips = await asyncio.to_thread(
            cut_clips,
            download_result["video_path"],
            highlights,
            download_result.get("duration_seconds", 0),
        )

        _set_video_state(video_id, "formatting", 84)
        vertical_clips = await asyncio.to_thread(format_vertical, clips)

        _set_video_state(video_id, "uploading", 94)
        uploaded = await asyncio.to_thread(upload_clips, video_id, vertical_clips)

        for payload in uploaded:
            clip_id = new_id()
            clip_record = {
                "id": clip_id,
                "video_id": video_id,
                "user_id": user_id,
                **payload,
                "created_at": utc_now_iso(),
            }
            insert_record("clips", clip_id, clip_record)

        _set_video_state(video_id, "done", 100)
        update_record("videos", video_id, {"clips_count": len(uploaded), "updated_at": utc_now_iso()})
    except Exception as exc:
        _set_video_state(video_id, "error", 100, str(exc))
    finally:
        if work_dir and os.path.isdir(work_dir):
            shutil.rmtree(work_dir, ignore_errors=True)
        processing_tasks.pop(video_id, None)


@router.post("/process", response_model=VideoStatus)
@limiter.limit("3/minute")
async def process_video(
    request: Request,
    payload: ProcessVideoRequest = Body(...),
    current_user: dict = Depends(require_current_user),
) -> VideoStatus:
    """Valide l'URL, recupere la metadata, cree la video et lance la pipeline."""
    if not is_valid_youtube_url(payload.youtube_url):
        raise HTTPException(status_code=400, detail="URL YouTube invalide")

    metadata_error = None
    try:
        metadata = await asyncio.to_thread(get_video_metadata, payload.youtube_url)
    except Exception as exc:
        metadata_error = str(exc)
        metadata = {
            "title": "Video importee",
            "duration_seconds": 60,
            "thumbnail_url": "",
            "uploader": "",
        }

    video_id = new_id()
    youtube_id = extract_youtube_id(payload.youtube_url)
    now = utc_now_iso()

    record = {
        "id": video_id,
        "user_id": current_user["id"],
        "youtube_url": payload.youtube_url,
        "youtube_id": youtube_id,
        "title": metadata.get("title") or "En preparation",
        "duration_seconds": int(metadata.get("duration_seconds") or 0),
        "thumbnail_url": metadata.get("thumbnail_url") or "",
        "status": "pending",
        "progress_percent": 0,
        "clips_count": 0,
        "error_message": metadata_error,
        "created_at": now,
        "updated_at": now,
    }
    insert_record("videos", video_id, record)

    processing_tasks[video_id] = asyncio.create_task(_process_video(video_id, payload.youtube_url, current_user["id"]))
    return VideoStatus(**record)


@router.get("/list", response_model=list[VideoStatus])
def list_videos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_current_user),
) -> list[VideoStatus]:
    videos = [video for video in list_records("videos") if video.get("user_id") == current_user["id"]]
    videos.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    page = videos[skip : skip + limit]
    return [VideoStatus(**video) for video in page]


@router.get("/{video_id}", response_model=VideoStatus)
def get_video(video_id: str, current_user: dict = Depends(require_current_user)) -> VideoStatus:
    return VideoStatus(**_video_or_404(video_id, current_user["id"]))


@router.get("/{video_id}/status")
def get_video_status(video_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    video = _video_or_404(video_id, current_user["id"])
    return {
        "id": video["id"],
        "status": video["status"],
        "progress_percent": video["progress_percent"],
        "error_message": video.get("error_message"),
        "clips_count": video.get("clips_count", 0),
    }


@router.delete("/{video_id}")
def delete_video(video_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    video = _video_or_404(video_id, current_user["id"])
    for clip in list_records("clips"):
        if clip.get("video_id") == video_id and clip.get("user_id") == current_user["id"]:
            delete_record("clips", clip["id"])
    delete_record("videos", video_id)
    return {"message": f"Video {video['id']} supprimee"}
