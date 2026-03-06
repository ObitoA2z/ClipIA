# -*- coding: utf-8 -*-
"""Extraction audio via ffmpeg."""

from __future__ import annotations

import os

from utils.helpers import ffmpeg_binary, run_subprocess


def extract_audio(video_path: str) -> str:
    """Extrait l'audio en mp3 16kHz mono depuis une video."""
    try:
        base_dir = os.path.dirname(video_path)
        audio_path = os.path.join(base_dir, "audio.mp3")
        command = [
            ffmpeg_binary(),
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "libmp3lame",
            "-ar",
            "16000",
            "-ac",
            "1",
            audio_path,
        ]
        run_subprocess(command, timeout=900)
        return audio_path
    except Exception as exc:
        raise RuntimeError(f"extract_audio failed: {exc}") from exc
