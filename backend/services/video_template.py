# -*- coding: utf-8 -*-
"""Templates d'habillage video (intro/outro/watermark/bandeau)."""

from __future__ import annotations

import os
from typing import Any

from utils.helpers import ffmpeg_binary, run_subprocess


def apply_watermark(
    *,
    input_video_path: str,
    output_video_path: str,
    logo_path: str,
    position: str = "top-right",
    scale_width: int = 120,
) -> str:
    position_map = {
        "top-right": "main_w-overlay_w-20:20",
        "top-left": "20:20",
        "bottom-right": "main_w-overlay_w-20:main_h-overlay_h-20",
        "bottom-left": "20:main_h-overlay_h-20",
    }
    overlay_expr = position_map.get(position, position_map["top-right"])

    command = [
        ffmpeg_binary(),
        "-y",
        "-i",
        input_video_path,
        "-i",
        logo_path,
        "-filter_complex",
        f"[1:v]scale={scale_width}:-1[logo];[0:v][logo]overlay={overlay_expr}",
        "-codec:a",
        "copy",
        output_video_path,
    ]
    run_subprocess(command, timeout=900)
    return output_video_path


def apply_bottom_banner(
    *,
    input_video_path: str,
    output_video_path: str,
    text: str,
    color_hex: str = "2D2DBA",
) -> str:
    escaped_text = (text or "").replace(":", "\\:").replace("'", "\\'")
    vf = (
        f"drawbox=x=0:y=ih-160:w=iw:h=160:color=#{color_hex}@0.55:t=fill,"
        f"drawtext=text='{escaped_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-105"
    )
    command = [
        ffmpeg_binary(),
        "-y",
        "-i",
        input_video_path,
        "-vf",
        vf,
        "-codec:a",
        "copy",
        output_video_path,
    ]
    run_subprocess(command, timeout=900)
    return output_video_path


def build_intro_outro_concat(
    *,
    intro_video_path: str | None,
    main_video_path: str,
    outro_video_path: str | None,
    output_video_path: str,
) -> str:
    inputs: list[str] = []
    videos: list[str] = []

    if intro_video_path and os.path.exists(intro_video_path):
        inputs.extend(["-i", intro_video_path])
        videos.append("[0:v:0][0:a:0]")

    main_index = len(videos)
    inputs.extend(["-i", main_video_path])
    videos.append(f"[{main_index}:v:0][{main_index}:a:0]")

    if outro_video_path and os.path.exists(outro_video_path):
        outro_index = len(videos)
        inputs.extend(["-i", outro_video_path])
        videos.append(f"[{outro_index}:v:0][{outro_index}:a:0]")

    concat_inputs = "".join(videos)
    concat_filter = f"{concat_inputs}concat=n={len(videos)}:v=1:a=1[v][a]"
    command = [
        ffmpeg_binary(),
        "-y",
        *inputs,
        "-filter_complex",
        concat_filter,
        "-map",
        "[v]",
        "-map",
        "[a]",
        output_video_path,
    ]
    run_subprocess(command, timeout=1200)
    return output_video_path


def resolve_user_template_settings(user: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "enabled": False,
        "banner_text": "",
        "banner_color": "2D2DBA",
        "logo_path": "",
        "watermark_position": "top-right",
        "intro_video_path": "",
        "outro_video_path": "",
    }
    user_settings = user.get("video_template_settings") or {}
    if not isinstance(user_settings, dict):
        user_settings = {}
    return {**defaults, **user_settings}

