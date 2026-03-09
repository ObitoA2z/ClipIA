# -*- coding: utf-8 -*-
"""Routes AI Coach pour le dashboard createur."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from database.connection import list_records
from services.ai_coach import generate_ai_coach_report
from utils.auth import require_current_user

router = APIRouter(prefix="/ai-coach", tags=["ai-coach"])


@router.get("/report")
def get_ai_coach_report(current_user: dict = Depends(require_current_user)) -> dict:
    clips = [clip for clip in list_records("clips") if clip.get("user_id") == current_user["id"]]
    clips.sort(key=lambda item: item.get("created_at", ""), reverse=True)

    previous_score = None
    preferences = current_user.get("preferences") or {}
    if isinstance(preferences, dict):
        previous_score = preferences.get("ai_coach_previous_score")

    report = generate_ai_coach_report(clips[:60], previous_score=previous_score)
    unlocked = len(clips) >= 5
    return {
        "unlocked": unlocked,
        "clips_analyzed": len(clips),
        "report": report,
    }
