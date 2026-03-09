# -*- coding: utf-8 -*-
"""Routes Content Hub (repurposing multi-formats)."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from database.connection import get_record, list_records
from services.content_repurposer import generate_quote_cards, repurpose_content
from utils.auth import require_current_user
from utils.helpers import ensure_dir, resolve_temp_dir

router = APIRouter(prefix="/content-repurpose", tags=["content-repurpose"])


def _local_media_url(file_path: str) -> str:
    backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")
    relative = os.path.relpath(file_path, resolve_temp_dir()).replace("\\", "/")
    return f"{backend_public_url}/media/{relative}"


@router.get("/{video_id}")
def get_repurposed_content(video_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    video = get_record("videos", video_id)
    if not video or video.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Video introuvable")

    clips = [
        item
        for item in list_records("clips")
        if item.get("video_id") == video_id and item.get("user_id") == current_user["id"]
    ]
    if not clips:
        raise HTTPException(status_code=400, detail="Aucun clip disponible pour generer le Content Hub")

    clips.sort(key=lambda item: float(item.get("start_time") or 0.0))
    segments = []
    text_parts = []
    for clip in clips:
        segment_text = str(clip.get("hook_text") or clip.get("title") or "").strip()
        if segment_text:
            text_parts.append(segment_text)
        segments.append(
            {
                "start": float(clip.get("start_time") or 0.0),
                "end": float(clip.get("end_time") or 0.0),
                "text": segment_text or f"Clip {clip.get('id')}",
            }
        )

    transcript = {
        "text": " ".join(text_parts).strip(),
        "segments": segments,
    }
    content = repurpose_content(
        transcript,
        creator_name=str(current_user.get("full_name") or "Creator"),
    )

    quotes = content.get("quotes") or []
    output_dir = ensure_dir(os.path.join(resolve_temp_dir(), "content_hub", video_id))
    quote_paths = generate_quote_cards(
        quotes if isinstance(quotes, list) else [],
        output_dir,
        author=str(current_user.get("full_name") or "Creator"),
    )
    quote_cards = [{"path": path, "url": _local_media_url(path)} for path in quote_paths]

    return {
        "video": {
            "id": video_id,
            "title": video.get("title") or "Video",
        },
        "content": {
            "blog": content.get("blog") or "",
            "twitter_thread": content.get("twitter_thread") or [],
            "linkedin_post": content.get("linkedin_post") or "",
            "show_notes": content.get("show_notes") or "",
            "quotes": quotes,
            "quote_cards": quote_cards,
        },
    }
