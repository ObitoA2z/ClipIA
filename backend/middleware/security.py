# -*- coding: utf-8 -*-
"""Middlewares et helpers de securite pour l'API ClipAI."""

from __future__ import annotations

import os
import re
from typing import Iterable

import bleach
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

MAX_JSON_BODY_BYTES = 1 * 1024 * 1024  # 1MB
STRICT_YOUTUBE_REGEX = re.compile(
    r"^(https?://)(www\.)?(youtube\.com/watch\?v=[A-Za-z0-9_-]{6,}|youtu\.be/[A-Za-z0-9_-]{6,})(&.*)?$",
    re.IGNORECASE,
)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Bloque les payloads JSON trop volumineux (protection DoS basique)."""

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_type = request.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                content_length = request.headers.get("content-length")
                if content_length and content_length.isdigit():
                    if int(content_length) > MAX_JSON_BODY_BYTES:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Payload trop volumineux (max 1MB)."},
                        )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Ajoute les headers de securite HTTP recommandes OWASP."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: https:; "
            "connect-src 'self' https: wss:;"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return response


def sanitize_text(value: str) -> str:
    """Nettoie un champ texte libre pour limiter les injections XSS."""
    return bleach.clean(value or "", tags=[], attributes={}, protocols=[], strip=True)


def validate_youtube_url_strict(url: str) -> bool:
    """Validation YouTube stricte pour les endpoints sensibles."""
    return bool(STRICT_YOUTUBE_REGEX.match((url or "").strip()))


def _build_allowed_origins() -> list[str]:
    frontend_url = (os.getenv("FRONTEND_URL", "http://localhost:5173") or "").strip()
    vercel_url = (os.getenv("VERCEL_URL", "") or "").strip()
    custom_origins = (os.getenv("ALLOWED_ORIGINS", "") or "").strip()

    origins: list[str] = [
        frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]
    if vercel_url:
        if not vercel_url.startswith("http"):
            origins.append(f"https://{vercel_url}")
        else:
            origins.append(vercel_url)

    if custom_origins:
        origins.extend([item.strip() for item in custom_origins.split(",") if item.strip()])

    unique = []
    seen = set()
    for origin in origins:
        if not origin:
            continue
        if origin in seen:
            continue
        seen.add(origin)
        unique.append(origin)
    return unique


def apply_security_middleware(app: FastAPI) -> None:
    """Applique les middlewares de securite et le CORS strict."""
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_build_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )


def enforce_known_fields(payload: dict, allowed_fields: Iterable[str]) -> None:
    """Refuse les champs inconnus d'un payload JSON."""
    allowed = set(allowed_fields)
    extra = [key for key in payload.keys() if key not in allowed]
    if extra:
        raise HTTPException(status_code=422, detail=f"Champs non autorises: {', '.join(extra)}")
