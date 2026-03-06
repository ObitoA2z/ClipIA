# -*- coding: utf-8 -*-
"""Decoupe des clips via ffmpeg."""

from __future__ import annotations

import os

from utils.helpers import ffmpeg_binary, probe_duration_seconds, run_subprocess


def cut_clips(video_path: str, highlights: list[dict], duration_seconds: float | None = None) -> list[dict]:
    """Decoupe la video source en clips individuels a partir des highlights."""
    try:
        source_duration = float(duration_seconds or 0.0)
        if source_duration <= 0:
            source_duration = probe_duration_seconds(video_path)

        base_dir = os.path.dirname(video_path)
        clip_paths: list[dict] = []

        for index, highlight in enumerate(highlights, start=1):
            raw_start = float(highlight.get("start", 0.0))
            raw_end = float(highlight.get("end", raw_start + 20.0))

            start = max(0.0, raw_start - 1.0)
            end = raw_end + 1.0
            if source_duration > 0:
                end = min(source_duration, end)

            if end <= start:
                continue

            clip_path = os.path.join(base_dir, f"clip_{index}.mp4")
            command = [
                ffmpeg_binary(),
                "-y",
                "-ss",
                f"{start:.3f}",
                "-to",
                f"{end:.3f}",
                "-i",
                video_path,
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                clip_path,
            ]
            run_subprocess(command, timeout=900)

            clip_paths.append(
                {
                    "path": clip_path,
                    "meta": {
                        **highlight,
                        "start": round(start, 3),
                        "end": round(end, 3),
                    },
                }
            )

        if not clip_paths:
            raise RuntimeError("No clips were generated")

        return clip_paths
    except Exception as exc:
        raise RuntimeError(f"cut_clips failed: {exc}") from exc
