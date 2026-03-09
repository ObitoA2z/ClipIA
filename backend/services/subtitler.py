# -*- coding: utf-8 -*-
"""Generation et integration de sous-titres pour les clips."""

from __future__ import annotations

import os
from typing import Iterable

from utils.helpers import ffmpeg_binary, run_subprocess

try:
    from googletrans import Translator
except Exception:  # pragma: no cover
    Translator = None


def _to_srt_time(seconds: float) -> str:
    milliseconds = int(round(max(0.0, seconds) * 1000))
    hours = milliseconds // 3_600_000
    minutes = (milliseconds % 3_600_000) // 60_000
    secs = (milliseconds % 60_000) // 1000
    ms = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def generate_srt(segments: Iterable[dict], output_srt_path: str) -> str:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start + 1.0))
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        lines.extend(
            [
                str(index),
                f"{_to_srt_time(start)} --> {_to_srt_time(end)}",
                text,
                "",
            ]
        )

    os.makedirs(os.path.dirname(output_srt_path), exist_ok=True)
    with open(output_srt_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).strip() + "\n")
    return output_srt_path


def burn_subtitles(
    *,
    input_video_path: str,
    subtitles_path: str,
    output_video_path: str,
    font_name: str = "Arial",
    font_size: int = 18,
    text_color_ass: str = "&H00FFFFFF",
    outline_color_ass: str = "&H00000000",
    border_style: int = 3,
) -> str:
    style = (
        f"FontName={font_name},"
        f"FontSize={font_size},"
        f"PrimaryColour={text_color_ass},"
        f"OutlineColour={outline_color_ass},"
        f"BorderStyle={border_style}"
    )
    subtitles_path_normalized = subtitles_path.replace("\\", "/").replace(":", "\\:")
    vf = f"subtitles={subtitles_path_normalized}:force_style='{style}'"

    command = [
        ffmpeg_binary(),
        "-y",
        "-i",
        input_video_path,
        "-vf",
        vf,
        "-c:a",
        "copy",
        output_video_path,
    ]
    run_subprocess(command, timeout=900)
    return output_video_path


def translate_segments(segments: list[dict], target_language: str) -> list[dict]:
    if not segments:
        return []
    if not Translator:
        return segments

    translator = Translator()
    translated: list[dict] = []
    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            translated.append(segment)
            continue
        try:
            value = translator.translate(text, dest=target_language).text
        except Exception:
            value = text
        translated.append({**segment, "text": value})
    return translated

