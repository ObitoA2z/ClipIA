# -*- coding: utf-8 -*-
"""Helpers auth relies on services.auth_security for token/session handling."""

from __future__ import annotations

from fastapi import Header, HTTPException, Request

from database.connection import get_record
from services.auth_security import (
    extract_bearer_token,
    get_client_ip,
    get_country,
    issue_token_pair,
    revoke_all_user_sessions,
    revoke_session_token,
    validate_session_token,
)


def issue_tokens(user_id: str, request: Request | None = None) -> dict:
    ip_address = get_client_ip(request) if request else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "") if request else ""
    country = get_country(request) if request else "ZZ"
    return issue_token_pair(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        country=country,
    )


def revoke_token(token: str) -> None:
    revoke_session_token(token)


def user_from_access_header(authorization: str | None) -> dict:
    token = extract_bearer_token(authorization)
    session = validate_session_token(token, kind="access")
    user = get_record("users", session["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


def user_from_refresh_token(refresh_token: str) -> dict:
    session = validate_session_token(refresh_token, kind="refresh")
    user = get_record("users", session["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


def require_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict:
    _ = request  # conserve la signature dependance FastAPI avec contexte Request.
    return user_from_access_header(authorization)


__all__ = [
    "extract_bearer_token",
    "issue_tokens",
    "require_current_user",
    "revoke_all_user_sessions",
    "revoke_token",
    "user_from_access_header",
    "user_from_refresh_token",
]

