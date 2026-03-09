# -*- coding: utf-8 -*-
"""Modeles video pour l'API ClipAI."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ClipMode = Literal["talking", "visual", "energy", "prompt"]
TargetPlatform = Literal["tiktok", "reels", "shorts", "all"]
ClipLayout = Literal["centered", "blurred", "split"]


class ProcessVideoRequest(BaseModel):
    youtube_url: str = Field(min_length=10, max_length=2048)
    clip_mode: ClipMode = "talking"
    prompt: str | None = Field(default=None, max_length=300)
    max_clips: int = Field(default=8, ge=1, le=12)
    min_duration: int = Field(default=30, ge=10, le=180)
    max_duration: int = Field(default=90, ge=15, le=240)
    target_platform: TargetPlatform = "all"
    layout: ClipLayout = "centered"

    @model_validator(mode="after")
    def validate_clipping_options(self) -> "ProcessVideoRequest":
        if self.min_duration >= self.max_duration:
            raise ValueError("min_duration doit etre inferieur a max_duration")
        if self.clip_mode == "prompt" and not (self.prompt or "").strip():
            raise ValueError("prompt est obligatoire quand clip_mode='prompt'")
        return self


class VideoStatus(BaseModel):
    id: str
    youtube_url: str
    youtube_id: str
    title: str
    duration_seconds: int
    thumbnail_url: str | None = None
    clip_mode: ClipMode | None = None
    prompt: str | None = None
    target_platform: TargetPlatform | None = None
    layout: ClipLayout | None = None
    status: str
    progress_percent: int
    clips_count: int
    avg_virality_score: float | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
