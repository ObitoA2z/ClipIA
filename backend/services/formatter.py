# -*- coding: utf-8 -*-
"""Conversion des clips en format vertical 9:16."""

from __future__ import annotations

import os

from utils.helpers import ffmpeg_binary, run_subprocess


def format_vertical(clips: list[dict]) -> list[dict]:
    """Transforme chaque clip en video verticale 1080x1920."""
    try:
        result: list[dict] = []

        for clip in clips:
            source_path = clip["path"]
            base_dir = os.path.dirname(source_path)
            filename = os.path.basename(source_path).replace(".mp4", "_vertical.mp4")
            vertical_path = os.path.join(base_dir, filename)

            command = [
                ffmpeg_binary(),
                "-y",
                "-i",
                source_path,
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-crf",
                "23",
                "-preset",
                "fast",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                vertical_path,
            ]
            run_subprocess(command, timeout=900)

            result.append({"path": vertical_path, "meta": clip["meta"]})

        if not result:
            raise RuntimeError("No vertical clips generated")

        return result
    except Exception as exc:
        raise RuntimeError(f"format_vertical failed: {exc}") from exc
