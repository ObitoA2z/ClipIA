# -*- coding: utf-8 -*-
"""Helpers d'authentification utilises par les routes API."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from database.connection import get_record, insert_record, list_records, update_record
from utils.helpers import new_id, utc_now_iso


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token manquant")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Format token invalide")
    token = authorization.split(" ", maxsplit=1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token vide")
    return token


def _session_is_valid(session: dict, *, kind: str) -> bool:
    if not session:
        return False
    if session.get("revoked"):
        return False
    if session.get("kind") != kind:
        return False

    expires_at = session.get("expires_at")
    if not expires_at:
        return False

    try:
        return _parse_iso(expires_at) > _utc_now()
    except Exception:
        return False


def create_session_token(user_id: str, *, kind: str, expires_in_seconds: int) -> str:
    token = new_id()
    expires_at = (_utc_now() + timedelta(seconds=max(30, expires_in_seconds))).isoformat()
    record = {
        "token": token,
        "user_id": user_id,
        "kind": kind,
        "expires_at": expires_at,
        "revoked": False,
        "created_at": utc_now_iso(),
    }
    insert_record("sessions", token, record)
    return token


def revoke_token(token: str) -> None:
    update_record("sessions", token, {"revoked": True, "updated_at": utc_now_iso()})


def revoke_all_tokens_for_user(user_id: str) -> None:
    for session in list_records("sessions"):
        if session.get("user_id") == user_id and not session.get("revoked"):
            revoke_token(session["token"])


def issue_tokens(user_id: str) -> dict:
    access_ttl_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15") or 15)
    refresh_ttl_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7") or 7)

    access_token = create_session_token(
        user_id,
        kind="access",
        expires_in_seconds=access_ttl_minutes * 60,
    )
    refresh_token = create_session_token(
        user_id,
        kind="refresh",
        expires_in_seconds=refresh_ttl_days * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user_id,
    }


def user_from_access_header(authorization: str | None) -> dict:
    token = extract_bearer_token(authorization)
    session = get_record("sessions", token)
    if not _session_is_valid(session, kind="access"):
        raise HTTPException(status_code=401, detail="Session invalide ou expirée")

    user = get_record("users", session["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


def user_from_refresh_token(refresh_token: str) -> dict:
    session = get_record("sessions", refresh_token)
    if not _session_is_valid(session, kind="refresh"):
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")

    user = get_record("users", session["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


def require_current_user(authorization: str | None = Header(default=None)) -> dict:
    return user_from_access_header(authorization)
