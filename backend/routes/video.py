# -*- coding: utf-8 -*-
"""Routes video avec pipeline reelle (yt-dlp + ffmpeg + IA optionnelle)."""

import asyncio
import hashlib
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Query, Request, WebSocket, WebSocketDisconnect

from database.connection import delete_record, get_record, insert_record, list_records, update_record
from middleware.security import validate_youtube_url_strict
from models.video import ProcessVideoRequest, VideoStatus
from services.audit import detect_abuse_signals, log_audit
from services.downloader import get_video_metadata
from services.auth_security import validate_session_token
from tasks.celery_app import celery_app
from tasks.video_tasks import process_video_pipeline
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso
from utils.rate_limit import limiter
from utils.validators import extract_youtube_id

router = APIRouter(prefix="/video", tags=["video"])
processing_tasks: dict[str, asyncio.Task] = {}
ACTIVE_PROCESSING_STATUSES = {
    "pending",
    "downloading",
    "extracting",
    "transcribing",
    "detecting",
    "cutting",
    "formatting",
    "uploading",
}


def _queue_for_plan(plan: str | None) -> tuple[str, int]:
    normalized = str(plan or "free").strip().lower()
    if normalized == "business":
        return "queue_pipeline_high", 9
    if normalized == "pro":
        return "queue_pipeline_medium", 6
    return "queue_pipeline_low", 3


def _video_or_404(video_id: str, user_id: str) -> dict:
    video = get_record("videos", video_id)
    if not video or video.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Video introuvable")
    return video


def _with_video_metrics(video: dict) -> dict:
    clips = [clip for clip in list_records("clips") if clip.get("video_id") == video.get("id")]
    scores = [float(clip.get("virality_score")) for clip in clips if clip.get("virality_score") is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None
    payload = dict(video)
    payload["avg_virality_score"] = avg_score
    return payload
def _build_idempotency_hash(
    user_id: str,
    payload: ProcessVideoRequest,
    idempotency_key: str | None,
) -> str:
    normalized = {
        "user_id": user_id,
        "youtube_url": payload.youtube_url.strip(),
        "clip_mode": payload.clip_mode,
        "prompt": (payload.prompt or "").strip(),
        "max_clips": payload.max_clips,
        "min_duration": payload.min_duration,
        "max_duration": payload.max_duration,
        "target_platform": payload.target_platform,
        "layout": payload.layout,
    }
    if idempotency_key:
        normalized["idempotency_key"] = idempotency_key.strip()
    payload_bytes = json.dumps(normalized, ensure_ascii=True, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


def _find_existing_processing_video(user_id: str, idempotency_key_hash: str) -> dict | None:
    matches = [
        video
        for video in list_records("videos")
        if video.get("user_id") == user_id
        and video.get("idempotency_key_hash") == idempotency_key_hash
        and video.get("status") in ACTIVE_PROCESSING_STATUSES
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return matches[0]


async def _process_video(video_id: str, payload: ProcessVideoRequest, user_id: str) -> None:
    """Fallback local uniquement si le broker Celery est indisponible."""
    try:
        await asyncio.to_thread(
            process_video_pipeline,
            video_id,
            payload.model_dump(),
            user_id,
        )
    finally:
        processing_tasks.pop(video_id, None)


@router.post("/process", response_model=VideoStatus)
@limiter.limit("3/minute")
async def process_video(
    request: Request,
    payload: ProcessVideoRequest = Body(...),
    current_user: dict = Depends(require_current_user),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> VideoStatus:
    """Valide l'URL, recupere la metadata, cree la video et lance la pipeline."""
    if not validate_youtube_url_strict(payload.youtube_url):
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

    idempotency_key_hash = _build_idempotency_hash(current_user["id"], payload, idempotency_key)
    existing_video = _find_existing_processing_video(current_user["id"], idempotency_key_hash)
    if existing_video:
        return VideoStatus(**_with_video_metrics(existing_video))

    video_id = new_id()
    youtube_id = extract_youtube_id(payload.youtube_url)
    now = utc_now_iso()

    record = {
        "id": video_id,
        "user_id": current_user["id"],
        "youtube_url": payload.youtube_url,
        "clip_mode": payload.clip_mode,
        "prompt": (payload.prompt or "").strip(),
        "max_clips": payload.max_clips,
        "min_duration": payload.min_duration,
        "max_duration": payload.max_duration,
        "target_platform": payload.target_platform,
        "layout": payload.layout,
        "idempotency_key_hash": idempotency_key_hash,
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
    log_audit(
        action="video.process.started",
        success=True,
        user_id=current_user["id"],
        resource_type="video",
        resource_id=video_id,
        request=request,
        metadata={"youtube_id": youtube_id},
    )
    abuse = detect_abuse_signals(user_id=current_user["id"])
    if abuse.get("too_many_videos"):
        log_audit(
            action="security.anomaly.video_burst",
            success=False,
            user_id=current_user["id"],
            request=request,
            metadata=abuse,
        )

    try:
        queue_name, queue_priority = _queue_for_plan(current_user.get("plan"))
        task = celery_app.send_task(
            "tasks.process_video_pipeline",
            args=[video_id, payload.model_dump(), current_user["id"]],
            queue=queue_name,
            priority=queue_priority,
        )
        update_record(
            "videos",
            video_id,
            {
                "worker_mode": "celery",
                "worker_job_id": task.id,
                "worker_queue": queue_name,
                "worker_priority": queue_priority,
                "updated_at": utc_now_iso(),
            },
        )
    except Exception as exc:
        update_record(
            "videos",
            video_id,
            {
                "worker_mode": "local_fallback",
                "worker_error": str(exc),
                "updated_at": utc_now_iso(),
            },
        )
        processing_tasks[video_id] = asyncio.create_task(_process_video(video_id, payload, current_user["id"]))
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
    return [VideoStatus(**_with_video_metrics(video)) for video in page]


@router.get("/{video_id}", response_model=VideoStatus)
def get_video(video_id: str, current_user: dict = Depends(require_current_user)) -> VideoStatus:
    return VideoStatus(**_with_video_metrics(_video_or_404(video_id, current_user["id"])))


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


@router.websocket("/{video_id}/ws")
async def video_status_ws(websocket: WebSocket, video_id: str, token: str | None = Query(default=None)) -> None:
    await websocket.accept()
    if not token:
        await websocket.send_json({"error": "token manquant"})
        await websocket.close(code=1008)
        return

    try:
        session = validate_session_token(token, kind="access")
    except Exception:
        await websocket.send_json({"error": "token invalide"})
        await websocket.close(code=1008)
        return

    user_id = session.get("user_id")
    if not user_id:
        await websocket.send_json({"error": "session invalide"})
        await websocket.close(code=1008)
        return

    try:
        while True:
            video = get_record("videos", video_id)
            if not video or video.get("user_id") != user_id:
                await websocket.send_json({"error": "video introuvable"})
                await websocket.close(code=1008)
                return

            payload = {
                "id": video["id"],
                "status": video.get("status", "pending"),
                "progress_percent": int(video.get("progress_percent", 0) or 0),
                "error_message": video.get("error_message"),
                "clips_count": int(video.get("clips_count", 0) or 0),
            }
            await websocket.send_json(payload)

            if payload["status"] in {"done", "error"}:
                await websocket.close(code=1000)
                return
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


@router.delete("/{video_id}")
def delete_video(video_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    video = _video_or_404(video_id, current_user["id"])
    for clip in list_records("clips"):
        if clip.get("video_id") == video_id and clip.get("user_id") == current_user["id"]:
            delete_record("clips", clip["id"])
    delete_record("videos", video_id)
    return {"message": f"Video {video['id']} supprimee"}
