# -*- coding: utf-8 -*-
"""Modèles vidéo pour l'API ClipAI."""

from pydantic import BaseModel, Field


class ProcessVideoRequest(BaseModel):
    youtube_url: str = Field(min_length=10)


class VideoStatus(BaseModel):
    id: str
    youtube_url: str
    youtube_id: str
    title: str
    duration_seconds: int
    status: str
    progress_percent: int
    clips_count: int
    error_message: str | None = None
