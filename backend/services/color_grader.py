# -*- coding: utf-8 -*-
"""Auto color grading presets pour clips video."""

from __future__ import annotations

import os

from utils.helpers import ffmpeg_binary, run_subprocess


COLOR_FILTERS = {
    "none": None,
    "cinematic": "curves=preset=medium_contrast,hue=s=1.2",
    "vibrant": "eq=saturation=1.3:contrast=1.1:brightness=0.05",
    "clean": "colorbalance=rs=0.1:gs=0:bs=-0.1",
    "warm": "eq=contrast=1.05:saturation=1.1, colorbalance=rs=0.05:gs=0.02:bs=-0.03",
}


def apply_color_grade(
    clip_path: str,
    *,
    preset: str = "none",
    output_path: str | None = None,
) -> str:
    """Applique un preset color grading et renvoie le chemin de sortie."""
    selected = (preset or "none").strip().lower()
    if selected not in COLOR_FILTERS:
        selected = "none"

    if output_path is None:
        base_dir = os.path.dirname(clip_path)
        stem = os.path.splitext(os.path.basename(clip_path))[0]
        output_path = os.path.join(base_dir, f"{stem}_grade_{selected}.mp4")

    filter_expr = COLOR_FILTERS[selected]
    if filter_expr is None:
        command = [
            ffmpeg_binary(),
            "-y",
            "-i",
            clip_path,
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            output_path,
        ]
    else:
        command = [
            ffmpeg_binary(),
            "-y",
            "-i",
            clip_path,
            "-vf",
            filter_expr,
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "22",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            output_path,
        ]

    run_subprocess(command, timeout=1200)
    return output_path


def list_color_presets() -> list[str]:
    return list(COLOR_FILTERS.keys())
