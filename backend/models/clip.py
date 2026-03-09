# -*- coding: utf-8 -*-
"""Modèle clip retourné par l'API."""

from pydantic import BaseModel


class ClipPublic(BaseModel):
    id: str
    video_id: str
    title: str
    start_time: float
    end_time: float
    duration_seconds: float
    file_url: str
    thumbnail_url: str
    resolution: str = "1080x1920"
    format: str = "mp4"
    virality_score: float | None = None
    hook_text: str | None = None
    improvement_tip: str | None = None
    best_platform: str | None = None
