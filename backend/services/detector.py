# -*- coding: utf-8 -*-
"""Detection des moments forts via IA + signaux visuels/audio."""

from __future__ import annotations

import audioop
import json
import os
import re
import tempfile
import wave
from typing import Any

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.helpers import ffmpeg_binary, run_subprocess

CLIP_MODES = {"talking", "visual", "energy", "prompt"}
_SCENE_TIME_RE = re.compile(r"pts_time:(\d+(?:\.\d+)?)")


def _infer_total_duration(transcript: dict) -> float:
    """Determine la duree totale a partir de la transcription."""
    explicit = float(transcript.get("duration_seconds") or 0.0)
    if explicit > 0:
        return explicit

    segments = transcript.get("segments", [])
    if not segments:
        return 60.0

    try:
        return max(float(segment.get("end", 0.0)) for segment in segments)
    except Exception:
        return 60.0


def _clip_duration_bounds(
    total_duration: float,
    min_duration: float,
    max_duration: float,
) -> tuple[float, float]:
    min_allowed = max(5.0, float(min_duration))
    max_allowed = max(min_allowed, float(max_duration))
    if total_duration > 0:
        max_allowed = min(max_allowed, total_duration)
        min_allowed = min(min_allowed, max_allowed)
    return min_allowed, max_allowed


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _sanitize_highlight(
    item: dict[str, Any],
    rank: int,
    total_duration: float,
    min_duration: float,
    max_duration: float,
) -> dict:
    """Valide et normalise un highlight issu d'une IA ou d'un fallback."""
    min_allowed, max_allowed = _clip_duration_bounds(total_duration, min_duration, max_duration)
    start = max(0.0, _safe_float(item.get("start"), 0.0))
    end = max(start + min_allowed, _safe_float(item.get("end"), start + min_allowed))

    if total_duration > 0:
        end = min(end, total_duration)
    if end <= start:
        end = start + min_allowed

    duration = end - start
    if duration > max_allowed:
        end = start + max_allowed
    if total_duration > 0:
        end = min(end, total_duration)

    hook = str(item.get("hook") or "").strip()
    if not hook:
        hook = "Extrait engageant"

    reason = str(item.get("reason") or "").strip()
    if not reason:
        reason = "Moment pertinent pour une video courte."

    title = str(item.get("title") or "").strip()
    if not title:
        title = f"Clip {rank}"

    return {
        "rank": rank,
        "title": title,
        "start": round(start, 3),
        "end": round(end, 3),
        "reason": reason,
        "hook": hook,
    }


def _extract_json_array(text: str) -> list[dict]:
    """Extrait un tableau JSON depuis un texte libre."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    raw = text[start : end + 1]
    try:
        payload = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def validate_clip_timestamps(
    start: float,
    end: float,
    *,
    min_duration: float = 20.0,
    max_duration: float = 120.0,
) -> bool:
    """Valide qu'un clip respecte les bornes de duree attendues."""
    start_value = float(start)
    end_value = float(end)
    if end_value <= start_value:
        return False
    duration = end_value - start_value
    return min_duration <= duration <= max_duration


def parse_gemini_response(raw_response: str) -> list[dict]:
    """Parse une reponse Gemini et renvoie la liste JSON nettoyee."""
    return _extract_json_array(raw_response)


def _segment_text_for_window(segments: list[dict], start: float, end: float) -> str:
    texts: list[str] = []
    for segment in segments:
        seg_start = _safe_float(segment.get("start"), 0.0)
        seg_end = _safe_float(segment.get("end"), 0.0)
        if seg_end < start or seg_start > end:
            continue
        text = str(segment.get("text") or "").strip()
        if text:
            texts.append(text)
    if not texts:
        return "Extrait detecte automatiquement."
    return " ".join(texts)[:220]


def _fallback_highlights(
    transcript: dict,
    *,
    max_clips: int,
    min_duration: float,
    max_duration: float,
) -> list[dict]:
    """Construit des highlights simples a partir des segments de transcription."""
    total_duration = _infer_total_duration(transcript)
    segments = transcript.get("segments", []) or []
    max_items = max(1, min(int(max_clips), 12))

    if not segments:
        end = min(total_duration, max_duration) if total_duration > 0 else max_duration
        return [
            _sanitize_highlight(
                {
                    "title": "Clip principal",
                    "start": 0.0,
                    "end": max(min_duration, end),
                    "reason": "Fallback sans transcription detaillee.",
                    "hook": "Extrait automatique",
                },
                rank=1,
                total_duration=total_duration,
                min_duration=min_duration,
                max_duration=max_duration,
            )
        ]

    step = max(1, len(segments) // max_items)
    highlights: list[dict] = []
    for index in range(0, len(segments), step):
        if len(highlights) >= max_items:
            break
        segment = segments[index]
        seg_start = max(0.0, _safe_float(segment.get("start"), 0.0) - 1.0)
        seg_end = _safe_float(segment.get("end"), seg_start + min_duration) + 1.0
        rank = len(highlights) + 1
        highlights.append(
            _sanitize_highlight(
                {
                    "title": f"Clip {rank} - Moment cle",
                    "start": seg_start,
                    "end": seg_end,
                    "reason": "Selection automatique basee sur la transcription.",
                    "hook": str(segment.get("text") or "Extrait court"),
                },
                rank=rank,
                total_duration=total_duration,
                min_duration=min_duration,
                max_duration=max_duration,
            )
        )

    return highlights


def _build_talking_prompt(
    transcript: dict,
    *,
    max_clips: int,
    min_duration: float,
    max_duration: float,
    target_platform: str,
) -> str:
    return (
        "Tu es monteur video court format. "
        "Reponds UNIQUEMENT en JSON valide (liste d'objets). "
        f"Trouve jusqu'a {max_clips} extraits de {int(min_duration)} a {int(max_duration)} secondes "
        f"optimises pour {target_platform}. "
        "Chaque item contient exactement: rank,title,start,end,reason,hook.\n\n"
        f"Transcription:\n{json.dumps(transcript, ensure_ascii=False)}"
    )


def _build_prompt_mode_prompt(
    transcript: dict,
    *,
    user_prompt: str,
    max_clips: int,
    min_duration: float,
    max_duration: float,
    target_platform: str,
) -> str:
    return (
        "Tu recois une transcription avec timestamps. "
        f"L'utilisateur cherche: {user_prompt!r}. "
        "Selectionne les segments qui correspondent le mieux a cette demande. "
        f"Retourne jusqu'a {max_clips} extraits entre {int(min_duration)} et {int(max_duration)} secondes "
        f"optimises pour {target_platform}. "
        "Reponds UNIQUEMENT en JSON valide avec les champs: rank,title,start,end,reason,hook.\n\n"
        f"Transcription:\n{json.dumps(transcript, ensure_ascii=False)}"
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def _detect_with_gemini(prompt: str, model_name: str) -> str:
    model = genai.GenerativeModel(model_name=model_name)
    response = model.generate_content(prompt, request_options={"timeout": 300})
    return getattr(response, "text", "") or ""


def _ai_highlights(
    transcript: dict,
    *,
    prompt: str,
    model_name: str,
    max_clips: int,
    min_duration: float,
    max_duration: float,
) -> list[dict]:
    total_duration = _infer_total_duration(transcript)
    raw_text = _detect_with_gemini(prompt, model_name=model_name)
    ai_items = parse_gemini_response(raw_text)
    if not ai_items:
        return []

    highlights: list[dict] = []
    for index, item in enumerate(ai_items[: max(1, max_clips)], start=1):
        highlights.append(
            _sanitize_highlight(
                item,
                rank=index,
                total_duration=total_duration,
                min_duration=min_duration,
                max_duration=max_duration,
            )
        )
    return highlights


def _dedupe_timestamps(timestamps: list[float], min_gap: float = 8.0) -> list[float]:
    clean = sorted({round(max(0.0, value), 3) for value in timestamps})
    deduped: list[float] = []
    for timestamp in clean:
        if not deduped or abs(timestamp - deduped[-1]) >= min_gap:
            deduped.append(timestamp)
    return deduped


def _timestamps_to_highlights(
    timestamps: list[float],
    transcript: dict,
    *,
    title_prefix: str,
    reason: str,
    max_clips: int,
    min_duration: float,
    max_duration: float,
) -> list[dict]:
    total_duration = _infer_total_duration(transcript)
    segments = transcript.get("segments", []) or []
    max_items = max(1, min(max_clips, 12))
    clip_len = max(min_duration, min(max_duration, 45.0))

    highlights: list[dict] = []
    for idx, ts in enumerate(timestamps[:max_items], start=1):
        start = max(0.0, ts - max(4.0, min_duration * 0.25))
        end = start + clip_len
        hook = _segment_text_for_window(segments, start, end)
        highlights.append(
            _sanitize_highlight(
                {
                    "title": f"{title_prefix} {idx}",
                    "start": start,
                    "end": end,
                    "reason": reason,
                    "hook": hook,
                },
                rank=idx,
                total_duration=total_duration,
                min_duration=min_duration,
                max_duration=max_duration,
            )
        )
    return highlights


def _scene_change_timestamps(video_path: str, threshold: float = 0.30) -> list[float]:
    if not video_path or not os.path.isfile(video_path):
        return []
    command = [
        ffmpeg_binary(),
        "-hide_banner",
        "-i",
        video_path,
        "-vf",
        f"select='gt(scene,{threshold})',showinfo",
        "-f",
        "null",
        "-",
    ]
    try:
        result = run_subprocess(command, timeout=1200)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        values = [float(match.group(1)) for match in _SCENE_TIME_RE.finditer(output)]
        return _dedupe_timestamps(values)
    except Exception:
        return []


def _energy_peak_timestamps(audio_path: str, max_clips: int) -> list[float]:
    if not audio_path or not os.path.isfile(audio_path):
        return []

    temp_wav_path = ""
    wav_path = audio_path
    if not audio_path.lower().endswith(".wav"):
        fd, temp_wav_path = tempfile.mkstemp(prefix="clipai_energy_", suffix=".wav")
        os.close(fd)
        command = [
            ffmpeg_binary(),
            "-y",
            "-i",
            audio_path,
            "-ac",
            "1",
            "-ar",
            "16000",
            temp_wav_path,
        ]
        try:
            run_subprocess(command, timeout=600)
            wav_path = temp_wav_path
        except Exception:
            if os.path.isfile(temp_wav_path):
                os.remove(temp_wav_path)
            return []

    peaks: list[tuple[float, float]] = []
    try:
        with wave.open(wav_path, "rb") as wav_file:
            frame_rate = wav_file.getframerate() or 16000
            sample_width = wav_file.getsampwidth() or 2
            window_seconds = 2.0
            chunk_size = max(1, int(frame_rate * window_seconds))
            index = 0

            while True:
                frames = wav_file.readframes(chunk_size)
                if not frames:
                    break
                rms = float(audioop.rms(frames, sample_width))
                center_time = (index + 0.5) * window_seconds
                peaks.append((center_time, rms))
                index += 1
    except Exception:
        peaks = []
    finally:
        if temp_wav_path and os.path.isfile(temp_wav_path):
            os.remove(temp_wav_path)

    if not peaks:
        return []

    peaks.sort(key=lambda item: item[1], reverse=True)
    selected: list[float] = []
    for ts, _rms in peaks:
        if any(abs(ts - picked) < 8.0 for picked in selected):
            continue
        selected.append(ts)
        if len(selected) >= max(1, max_clips):
            break
    return sorted(round(value, 3) for value in selected)


def _local_prompt_highlights(
    transcript: dict,
    user_prompt: str,
    *,
    max_clips: int,
    min_duration: float,
    max_duration: float,
) -> list[dict]:
    total_duration = _infer_total_duration(transcript)
    segments = transcript.get("segments", []) or []
    terms = {
        token.lower()
        for token in re.findall(r"[a-zA-Z0-9]{3,}", user_prompt or "")
        if len(token) >= 3
    }
    if not terms:
        return _fallback_highlights(
            transcript,
            max_clips=max_clips,
            min_duration=min_duration,
            max_duration=max_duration,
        )

    matches: list[dict] = []
    for segment in segments:
        text = str(segment.get("text") or "").lower()
        if any(term in text for term in terms):
            matches.append(segment)
    if not matches:
        return _fallback_highlights(
            transcript,
            max_clips=max_clips,
            min_duration=min_duration,
            max_duration=max_duration,
        )

    highlights: list[dict] = []
    clip_len = max(min_duration, min(max_duration, 45.0))
    for idx, segment in enumerate(matches[: max(1, max_clips)], start=1):
        start = max(0.0, _safe_float(segment.get("start"), 0.0) - 2.0)
        end = start + clip_len
        highlights.append(
            _sanitize_highlight(
                {
                    "title": f"Prompt match {idx}",
                    "start": start,
                    "end": end,
                    "reason": f"Correspond a la recherche: {user_prompt}",
                    "hook": str(segment.get("text") or "Extrait pertinent"),
                },
                rank=idx,
                total_duration=total_duration,
                min_duration=min_duration,
                max_duration=max_duration,
            )
        )
    return highlights


def detect_highlights(
    transcript: dict,
    *,
    clip_mode: str = "talking",
    user_prompt: str = "",
    video_path: str | None = None,
    audio_path: str | None = None,
    max_clips: int = 8,
    min_duration: float = 30.0,
    max_duration: float = 90.0,
    target_platform: str = "all",
) -> list[dict]:
    """Detecte les meilleurs extraits selon 4 modes: talking, visual, energy, prompt."""
    mode = (clip_mode or "talking").strip().lower()
    if mode not in CLIP_MODES:
        mode = "talking"

    max_clips = max(1, min(int(max_clips), 12))
    min_duration = float(min_duration)
    max_duration = float(max_duration)
    min_duration, max_duration = _clip_duration_bounds(
        _infer_total_duration(transcript),
        min_duration,
        max_duration,
    )

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    if api_key:
        genai.configure(api_key=api_key)

    try:
        if mode == "visual":
            visual_timestamps = _scene_change_timestamps(video_path or "")
            highlights = _timestamps_to_highlights(
                visual_timestamps,
                transcript,
                title_prefix="Visual moment",
                reason="Fort changement visuel detecte dans la video.",
                max_clips=max_clips,
                min_duration=min_duration,
                max_duration=max_duration,
            )
            if highlights:
                return highlights

        if mode == "energy":
            energy_timestamps = _energy_peak_timestamps(audio_path or "", max_clips=max_clips)
            highlights = _timestamps_to_highlights(
                energy_timestamps,
                transcript,
                title_prefix="Energy peak",
                reason="Pic d'energie audio detecte.",
                max_clips=max_clips,
                min_duration=min_duration,
                max_duration=max_duration,
            )
            if highlights:
                return highlights

        if mode == "prompt":
            if api_key and user_prompt.strip():
                ai_prompt = _build_prompt_mode_prompt(
                    transcript,
                    user_prompt=user_prompt.strip(),
                    max_clips=max_clips,
                    min_duration=min_duration,
                    max_duration=max_duration,
                    target_platform=target_platform,
                )
                highlights = _ai_highlights(
                    transcript,
                    prompt=ai_prompt,
                    model_name=model_name,
                    max_clips=max_clips,
                    min_duration=min_duration,
                    max_duration=max_duration,
                )
                if highlights:
                    return highlights

            return _local_prompt_highlights(
                transcript,
                user_prompt=user_prompt,
                max_clips=max_clips,
                min_duration=min_duration,
                max_duration=max_duration,
            )

        if api_key:
            ai_prompt = _build_talking_prompt(
                transcript,
                max_clips=max_clips,
                min_duration=min_duration,
                max_duration=max_duration,
                target_platform=target_platform,
            )
            highlights = _ai_highlights(
                transcript,
                prompt=ai_prompt,
                model_name=model_name,
                max_clips=max_clips,
                min_duration=min_duration,
                max_duration=max_duration,
            )
            if highlights:
                return highlights
    except Exception:
        pass

    return _fallback_highlights(
        transcript,
        max_clips=max_clips,
        min_duration=min_duration,
        max_duration=max_duration,
    )
