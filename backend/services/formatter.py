# -*- coding: utf-8 -*-
"""Conversion des clips en format vertical 9:16 avec layouts avances."""

from __future__ import annotations

import os

from utils.helpers import ffmpeg_binary, ffprobe_binary, run_subprocess

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None


def _probe_resolution(video_path: str) -> tuple[int, int]:
    command = [
        ffprobe_binary(),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        video_path,
    ]
    result = run_subprocess(command, timeout=30)
    raw = (result.stdout or "").strip()
    if "x" not in raw:
        return 0, 0
    left, right = raw.split("x", 1)
    return int(left), int(right)


def _detect_subject_center_x(video_path: str, sample_frames: int = 10) -> float | None:
    if cv2 is None:
        return None

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return None

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total_frames <= 0:
        capture.release()
        return None

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    positions: list[float] = []

    for idx in range(sample_frames):
        frame_index = int((idx + 1) * total_frames / (sample_frames + 1))
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok or frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            continue

        frame_width = float(frame.shape[1])
        center_candidates = [(x + (w / 2.0), w * h) for (x, y, w, h) in faces]
        center_candidates.sort(key=lambda item: item[1], reverse=True)
        best_center_x = center_candidates[0][0] / frame_width
        positions.append(max(0.0, min(1.0, best_center_x)))

    capture.release()
    if not positions:
        return None
    return sum(positions) / len(positions)


def _centered_filter(source_path: str, tracked_center_x: float | None) -> str:
    width, height = _probe_resolution(source_path)
    if width <= 0 or height <= 0:
        return "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

    crop_width = int(height * 9 / 16)
    if crop_width <= 0 or crop_width > width:
        return "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

    if tracked_center_x is None:
        crop_x = max(0, int((width - crop_width) / 2))
    else:
        target_center = int(width * tracked_center_x)
        crop_x = max(0, min(width - crop_width, target_center - int(crop_width / 2)))

    return f"crop={crop_width}:{height}:{crop_x}:0,scale=1080:1920"


def _layout_filter(layout: str, source_path: str) -> str:
    normalized_layout = (layout or "centered").strip().lower()

    if normalized_layout == "blurred":
        return (
            "split[a][b];"
            "[b]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:30[bg];"
            "[a]scale=1080:-2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )

    if normalized_layout == "split":
        return (
            "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            "[0:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,boxblur=24:12[bottom];"
            "[top][bottom]vstack=inputs=2"
        )

    tracked_center_x = _detect_subject_center_x(source_path)
    return _centered_filter(source_path, tracked_center_x)


def format_vertical(clips: list[dict], *, layout: str = "centered") -> list[dict]:
    """Transforme chaque clip en video verticale 1080x1920 avec layout configurable."""
    try:
        result: list[dict] = []

        for clip in clips:
            source_path = clip["path"]
            base_dir = os.path.dirname(source_path)
            filename = os.path.basename(source_path).replace(".mp4", "_vertical.mp4")
            vertical_path = os.path.join(base_dir, filename)

            video_filter = _layout_filter(layout, source_path)
            command = [
                ffmpeg_binary(),
                "-y",
                "-i",
                source_path,
                "-vf",
                video_filter,
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
            run_subprocess(command, timeout=1200)

            result.append(
                {
                    "path": vertical_path,
                    "meta": {
                        **clip["meta"],
                        "layout": layout,
                    },
                }
            )

        if not result:
            raise RuntimeError("No vertical clips generated")

        return result
    except Exception as exc:
        raise RuntimeError(f"format_vertical failed: {exc}") from exc
