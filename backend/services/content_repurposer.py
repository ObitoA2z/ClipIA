# -*- coding: utf-8 -*-
"""Repurposing multi-format depuis une transcription video."""

from __future__ import annotations

import json
import os
from typing import Any

import google.generativeai as genai
try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None

from utils.helpers import ensure_dir


def _fallback_blog(transcript_text: str) -> str:
    return (
        "# Article\n\n"
        "## Introduction\n"
        f"{transcript_text[:400]}\n\n"
        "## Points cles\n"
        "- Idee 1\n"
        "- Idee 2\n"
        "- Idee 3\n\n"
        "## Conclusion\n"
        "Passe a l'action avec une version courte de ce contenu."
    )


def _fallback_twitter(transcript_text: str) -> list[str]:
    base = transcript_text[:240]
    return [
        "1/10 Voici les idees principales de cette video:",
        f"2/10 {base}",
        "3/10 Le meilleur levier: clarifier le message en 1 phrase.",
        "4/10 Coupe tout ce qui n'apporte pas de valeur immediate.",
        "5/10 Un hook fort dans les 3 premieres secondes change tout.",
        "6/10 Fais simple, mesurable, repetable.",
        "7/10 Priorise la retention avant la longueur.",
        "8/10 Teste 3 variantes de hooks par sujet.",
        "9/10 Mesure les resultats apres publication.",
        "10/10 Repurpose > repartir de zero."
    ]


def _fallback_linkedin(transcript_text: str) -> str:
    return (
        "J'ai synthétise cette video en framework actionnable:\n\n"
        f"{transcript_text[:600]}\n\n"
        "Ce qui fonctionne: un message direct + exemples concrets + CTA clair.\n"
        "Si vous publiez du contenu, transformez chaque video longue en 5-10 assets."
    )


def _fallback_show_notes(transcript: dict[str, Any]) -> str:
    segments = transcript.get("segments", []) or []
    lines = ["# Show Notes"]
    for segment in segments[:20]:
        start = float(segment.get("start", 0.0))
        text = str(segment.get("text") or "").strip()
        lines.append(f"- [{start:06.2f}] {text}")
    return "\n".join(lines)


def _load_font(size: int) -> ImageFont.ImageFont:
    if ImageFont is None:
        raise RuntimeError("Pillow non disponible")
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _quote_card(text: str, author: str, output_path: str) -> str:
    if Image is None or ImageDraw is None:
        with open(output_path, "wb") as file:
            file.write(b"quote_card_unavailable")
        return output_path
    width, height = 1080, 1080
    image = Image.new("RGB", (width, height), color="#0F1023")
    draw = ImageDraw.Draw(image)

    for i in range(height):
        alpha = i / max(1, height - 1)
        color = (
            int(22 + 60 * alpha),
            int(15 + 25 * alpha),
            int(45 + 90 * alpha),
        )
        draw.line([(0, i), (width, i)], fill=color)

    headline_font = _load_font(56)
    body_font = _load_font(44)
    small_font = _load_font(28)

    draw.text((70, 80), "ClipAI Quote", fill=(210, 190, 255), font=headline_font)

    wrapped = text[:180]
    draw.multiline_text((70, 260), f'"{wrapped}"', fill=(245, 245, 255), font=body_font, spacing=14)
    draw.text((70, 930), f"- {author}", fill=(170, 170, 220), font=small_font)

    image.save(output_path, format="PNG", optimize=True)
    return output_path


def generate_quote_cards(
    quotes: list[str],
    output_dir: str,
    *,
    author: str = "Creator",
) -> list[str]:
    ensure_dir(output_dir)
    paths: list[str] = []
    for index, quote in enumerate(quotes[:8], start=1):
        path = os.path.join(output_dir, f"quote_{index}.png")
        paths.append(_quote_card(quote, author, path))
    return paths


def _gemini_json(prompt: str, fallback: Any) -> Any:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback
    try:
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt, request_options={"timeout": 300})
        raw = getattr(response, "text", "") or ""
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return fallback
        return json.loads(raw[start : end + 1])
    except Exception:
        return fallback


def repurpose_content(transcript: dict[str, Any], *, creator_name: str = "Creator") -> dict[str, Any]:
    """Genere 6 formats: blog, twitter, linkedin, show notes, quote cards."""
    text = str(transcript.get("text") or "").strip()
    if not text:
        text = " ".join(str(seg.get("text") or "") for seg in transcript.get("segments", [])[:80])

    blog = _fallback_blog(text)
    twitter_thread = _fallback_twitter(text)
    linkedin_post = _fallback_linkedin(text)
    show_notes = _fallback_show_notes(transcript)

    ai_payload = _gemini_json(
        (
            "Transforme cette transcription en JSON avec les champs blog, twitter_thread, "
            "linkedin_post, show_notes, quotes (liste)."
            f"\n\nTranscription:\n{text[:12000]}"
        ),
        fallback={},
    )

    if isinstance(ai_payload, dict):
        blog = str(ai_payload.get("blog") or blog)
        linkedin_post = str(ai_payload.get("linkedin_post") or linkedin_post)
        show_notes = str(ai_payload.get("show_notes") or show_notes)
        raw_thread = ai_payload.get("twitter_thread")
        if isinstance(raw_thread, list) and raw_thread:
            twitter_thread = [str(item) for item in raw_thread[:12]]

        raw_quotes = ai_payload.get("quotes")
        if isinstance(raw_quotes, list) and raw_quotes:
            quotes = [str(item) for item in raw_quotes[:8]]
        else:
            quotes = [segment["text"] for segment in (transcript.get("segments", []) or [])[:6] if segment.get("text")]
    else:
        quotes = [segment["text"] for segment in (transcript.get("segments", []) or [])[:6] if segment.get("text")]

    return {
        "blog": blog,
        "twitter_thread": twitter_thread,
        "linkedin_post": linkedin_post,
        "show_notes": show_notes,
        "quotes": quotes,
        "creator_name": creator_name,
    }
