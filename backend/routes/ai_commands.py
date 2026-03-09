# -*- coding: utf-8 -*-
"""Routes commandes conversationnelles pour edition de clips."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import get_record, update_record
from utils.auth import require_current_user

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None

router = APIRouter(prefix="/ai-commands", tags=["ai-commands"])


class ParseCommandRequest(BaseModel):
    command: str = Field(min_length=3, max_length=400)


class ApplyCommandRequest(BaseModel):
    clip_id: str = Field(min_length=6)
    command: str = Field(min_length=3, max_length=400)


def _rule_parse(command: str) -> dict[str, Any]:
    text = (command or "").strip().lower()

    match = re.search(r"debut\s+de\s+(\d+)", text)
    if "raccour" in text and match:
        return {"action": "shift_start", "params": {"seconds": int(match.group(1))}}

    match = re.search(r"(\d+)\s+dernieres?\s+secondes?", text)
    if "supprim" in text and match:
        return {"action": "trim_end", "params": {"seconds": int(match.group(1))}}

    if "mrbeast" in text:
        return {"action": "set_caption_style", "params": {"style": "mrbeast"}}

    if "musique" in text:
        return {"action": "add_music", "params": {"mood": "motivational"}}

    if "couleur" in text or "vives" in text:
        return {"action": "set_color_grade", "params": {"preset": "vibrant"}}

    if "tradui" in text and "anglais" in text:
        return {"action": "translate_captions", "params": {"language": "en"}}

    if "logo" in text:
        return {"action": "set_logo_position", "params": {"position": "top-right"}}

    return {"action": "noop", "params": {}, "reason": "Commande non reconnue"}


def _gemini_parse(command: str) -> dict[str, Any] | None:
    if genai is None:
        return None
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        model = genai.GenerativeModel(model_name=model_name)
        prompt = (
            "Traduis la commande utilisateur en JSON actionnable. "
            "Actions: shift_start, trim_end, shorter_version, set_caption_style, add_music, "
            "set_color_grade, translate_captions, generate_hook, set_logo_position, noop. "
            "Reponds UNIQUEMENT avec {\"action\":...,\"params\":{...}}.\n"
            f"Commande: {command!r}"
        )
        response = model.generate_content(prompt, request_options={"timeout": 120})
        raw = getattr(response, "text", "") or ""
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        parsed = json.loads(raw[start : end + 1])
        if isinstance(parsed, dict) and "action" in parsed:
            return parsed
    except Exception:
        return None

    return None


def parse_command(command: str) -> dict[str, Any]:
    parsed = _gemini_parse(command)
    if parsed:
        return parsed
    return _rule_parse(command)


@router.post("/parse")
def parse_command_endpoint(payload: ParseCommandRequest, current_user: dict = Depends(require_current_user)) -> dict:
    _ = current_user
    return {"result": parse_command(payload.command)}


@router.post("/apply")
def apply_command(payload: ApplyCommandRequest, current_user: dict = Depends(require_current_user)) -> dict:
    clip = get_record("clips", payload.clip_id)
    if not clip or clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Clip introuvable")

    parsed = parse_command(payload.command)
    action = parsed.get("action")
    params = parsed.get("params") or {}

    if action == "shift_start":
        seconds = max(0, int(params.get("seconds") or 0))
        clip["start_time"] = max(0.0, float(clip.get("start_time") or 0.0) + seconds)
        update_record("clips", clip["id"], clip)
    elif action == "trim_end":
        seconds = max(0, int(params.get("seconds") or 0))
        clip["end_time"] = max(float(clip.get("start_time") or 0.0), float(clip.get("end_time") or 0.0) - seconds)
        update_record("clips", clip["id"], clip)
    else:
        # Actions de post-production sont stockees pour traitement async.
        clip.setdefault("pending_ai_actions", []).append(parsed)
        update_record("clips", clip["id"], clip)

    return {"message": "Commande appliquee", "result": parsed, "clip": clip}
