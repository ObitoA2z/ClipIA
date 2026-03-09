# -*- coding: utf-8 -*-
"""Generation de thumbnails IA pour les clips."""

from __future__ import annotations

import os
import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from utils.helpers import ensure_dir, ffmpeg_binary, run_subprocess

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

try:
    from deepface import DeepFace  # type: ignore
except Exception:  # pragma: no cover
    DeepFace = None


THUMBNAIL_SIZES = {
    "youtube": (1280, 720),
    "instagram": (1080, 1080),
}


def extract_iframes(clip_path: str, output_dir: str, max_frames: int = 10) -> list[str]:
    """Extrait des frames I-frame de haute qualite depuis un clip."""
    ensure_dir(output_dir)
    frame_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    command = [
        ffmpeg_binary(),
        "-y",
        "-i",
        clip_path,
        "-vf",
        "select='eq(pict_type,I)',scale=1280:720",
        "-vsync",
        "vfr",
        frame_pattern,
    ]
    run_subprocess(command, timeout=900)

    frames = sorted(
        os.path.join(output_dir, name)
        for name in os.listdir(output_dir)
        if name.lower().startswith("frame_") and name.lower().endswith(".jpg")
    )
    return frames[: max(1, max_frames)]


def _face_score(frame_path: str) -> float:
    if cv2 is None:
        return 0.0
    image = cv2.imread(frame_path)
    if image is None:
        return 0.0

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(64, 64))
    if len(faces) == 0:
        return 0.0

    h, w = image.shape[:2]
    best = max(faces, key=lambda rect: rect[2] * rect[3])
    x, y, fw, fh = best
    area_ratio = (fw * fh) / float(w * h)
    center_x = x + (fw / 2.0)
    center_score = 1.0 - abs(center_x - (w / 2.0)) / (w / 2.0)
    return max(0.0, area_ratio * 6.0 + center_score)


def _emotion_score(frame_path: str) -> float:
    if DeepFace is None:
        return 0.0
    try:
        result = DeepFace.analyze(frame_path, actions=["emotion"], enforce_detection=False)
        if isinstance(result, list):
            result = result[0] if result else {}
        emotion = str((result or {}).get("dominant_emotion") or "").lower()
        if emotion in {"surprise", "happy"}:
            return 2.0
        if emotion in {"neutral", "fear"}:
            return 1.0
        return 0.5
    except Exception:
        return 0.0


def score_frame(frame_path: str) -> float:
    """Score heuristique d'une frame pour la choisir en thumbnail."""
    return _face_score(frame_path) + _emotion_score(frame_path)


def select_best_frames(frame_paths: list[str], variants: int = 3) -> list[str]:
    if not frame_paths:
        return []
    scored = [(path, score_frame(path)) for path in frame_paths]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [path for path, _ in scored[: max(1, variants)]]


def _safe_filename(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")
    return cleaned or "thumb"


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _render_thumbnail(
    frame_path: str,
    output_path: str,
    headline: str,
    *,
    size: tuple[int, int],
    logo_path: str | None = None,
    palette: tuple[str, str] = ("#7B61FF", "#FF61DC"),
) -> None:
    image = Image.open(frame_path).convert("RGB").resize(size)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    drawer = ImageDraw.Draw(overlay)

    width, height = size
    gradient_height = int(height * 0.38)
    for y in range(gradient_height):
        alpha = int(210 * (y / max(1, gradient_height)))
        drawer.rectangle([(0, height - gradient_height + y), (width, height - gradient_height + y + 1)], fill=(0, 0, 0, alpha))

    font = _load_font(max(34, int(height * 0.08)))
    text = headline[:60]
    text_x = int(width * 0.06)
    text_y = int(height * 0.64)
    drawer.text((text_x + 3, text_y + 3), text, font=font, fill=(0, 0, 0, 220))
    drawer.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    # Accent bar
    drawer.rectangle([(int(width * 0.04), int(height * 0.60)), (int(width * 0.05), int(height * 0.92))], fill=palette[0])

    if logo_path and os.path.isfile(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((int(width * 0.18), int(height * 0.18)))
            logo_x = width - logo.width - int(width * 0.03)
            logo_y = int(height * 0.03)
            overlay.alpha_composite(logo, (logo_x, logo_y))
        except Exception:
            pass

    result = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    result.save(output_path, format="PNG", optimize=True)


def generate_thumbnail_variants(
    clip_path: str,
    output_dir: str,
    *,
    hook: str,
    creator_name: str | None = None,
    logo_path: str | None = None,
    target: str = "youtube",
    variants: int = 3,
) -> list[dict[str, Any]]:
    """Genere 3 thumbnails candidates avec texte editable."""
    ensure_dir(output_dir)
    raw_frames_dir = ensure_dir(os.path.join(output_dir, "raw_frames"))
    frames = extract_iframes(clip_path, raw_frames_dir, max_frames=max(variants * 4, 10))
    selected = select_best_frames(frames, variants=variants)
    if not selected and frames:
        selected = frames[:variants]

    size = THUMBNAIL_SIZES.get(target, THUMBNAIL_SIZES["youtube"])
    prefix = _safe_filename(os.path.splitext(os.path.basename(clip_path))[0])

    payload: list[dict[str, Any]] = []
    for idx, frame in enumerate(selected, start=1):
        output_path = os.path.join(output_dir, f"{prefix}_thumb_{idx}.png")
        headline = hook.strip() or f"Top moment #{idx}"
        if creator_name:
            headline = f"{headline} | {creator_name}"
        _render_thumbnail(frame, output_path, headline, size=size, logo_path=logo_path)
        payload.append({"rank": idx, "path": output_path, "headline": headline, "target": target})

    return payload
