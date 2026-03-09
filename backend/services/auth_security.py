# -*- coding: utf-8 -*-
"""Services de securite auth (sessions, 2FA, OAuth, anti-bruteforce)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import httpx
import pyotp
import qrcode
from fastapi import HTTPException, Request

from database.connection import get_record, insert_record, list_records, update_record
from services.encryption import decrypt_text, encrypt_text
from utils.helpers import new_id, utc_now_iso

PASSWORD_POLICY_REGEX = re.compile(
    r"^(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,128}$"
)

_FAILED_ATTEMPTS: dict[str, dict[str, Any]] = {}
_IP_ATTEMPTS: dict[str, dict[str, Any]] = {}


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def validate_password_policy(password: str) -> tuple[bool, str]:
    if not PASSWORD_POLICY_REGEX.match(password or ""):
        return (
            False,
            "Mot de passe faible (min 8, 1 majuscule, 1 chiffre, 1 caractere special).",
        )
    return True, ""


def is_pwned_password(password: str, *, timeout_seconds: int = 8) -> bool:
    if not password:
        return False
    if os.getenv("ENABLE_HIBP_PASSWORD_CHECK", "false").strip().lower() != "true":
        return False

    sha1_value = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1_value[:5], sha1_value[5:]
    url = f"https://api.pwnedpasswords.com/range/{prefix}"

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.get(url, headers={"Add-Padding": "true"})
        if response.status_code != 200:
            return False
        for line in response.text.splitlines():
            candidate, _, _count = line.partition(":")
            if hmac.compare_digest(candidate.strip().upper(), suffix):
                return True
    except Exception:
        return False
    return False


def hash_token(token: str) -> str:
    return _sha256(token)


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def build_totp_uri(email: str, secret: str) -> str:
    issuer = os.getenv("TOTP_ISSUER", "ClipAI")
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def encrypt_totp_secret(user_id: str, secret: str) -> str:
    return encrypt_text(secret, context=f"totp:{user_id}")


def decrypt_totp_secret(user_id: str, encrypted_secret: str) -> str:
    return decrypt_text(encrypted_secret, context=f"totp:{user_id}")


def verify_totp_code(*, user_id: str, encrypted_secret: str, code: str) -> bool:
    try:
        secret = decrypt_totp_secret(user_id, encrypted_secret)
    except Exception:
        return False
    return pyotp.TOTP(secret).verify((code or "").strip(), valid_window=1)


def generate_qr_code_base64(uri: str) -> str:
    image = qrcode.make(uri)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token manquant")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Format token invalide")
    token = authorization.split(" ", maxsplit=1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token vide")
    return token


def get_client_ip(request: Request) -> str:
    x_forwarded_for = (request.headers.get("x-forwarded-for") or "").strip()
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


def get_country(request: Request) -> str:
    return (
        request.headers.get("x-vercel-ip-country")
        or request.headers.get("cf-ipcountry")
        or "ZZ"
    ).upper()


def build_device_fingerprint(ip_address: str, user_agent: str) -> str:
    base = f"{ip_address}|{user_agent or ''}"
    return _sha256(base)


def _session_is_valid(session: dict | None, *, kind: str) -> bool:
    if not session:
        return False
    if session.get("revoked") or not session.get("is_active", True):
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


def create_session_token(
    *,
    user_id: str,
    kind: str,
    expires_in_seconds: int,
    ip_address: str,
    user_agent: str,
    country: str,
    fingerprint: str,
) -> str:
    token = secrets.token_urlsafe(48)
    token_hash = hash_token(token)
    now = utc_now_iso()
    expires_at = (_utc_now() + timedelta(seconds=max(30, expires_in_seconds))).isoformat()
    record = {
        "id": new_id(),
        "token_hash": token_hash,
        "user_id": user_id,
        "kind": kind,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "country": country,
        "fingerprint": fingerprint,
        "is_active": True,
        "revoked": False,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
        "last_used_at": now,
    }
    insert_record("sessions", token_hash, record)
    return token


def issue_token_pair(
    *,
    user_id: str,
    ip_address: str,
    user_agent: str,
    country: str,
) -> dict[str, str]:
    access_ttl_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15") or 15)
    refresh_ttl_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30") or 30)
    fingerprint = build_device_fingerprint(ip_address, user_agent)

    access_token = create_session_token(
        user_id=user_id,
        kind="access",
        expires_in_seconds=access_ttl_minutes * 60,
        ip_address=ip_address,
        user_agent=user_agent,
        country=country,
        fingerprint=fingerprint,
    )
    refresh_token = create_session_token(
        user_id=user_id,
        kind="refresh",
        expires_in_seconds=refresh_ttl_days * 24 * 60 * 60,
        ip_address=ip_address,
        user_agent=user_agent,
        country=country,
        fingerprint=fingerprint,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user_id,
    }


def validate_session_token(token: str, *, kind: str) -> dict:
    token_hash = hash_token(token)
    session = get_record("sessions", token_hash) or get_record("sessions", token)
    if not _session_is_valid(session, kind=kind):
        raise HTTPException(status_code=401, detail="Session invalide ou expiree")
    update_record(
        "sessions",
        session.get("token_hash", token_hash),
        {"last_used_at": utc_now_iso(), "updated_at": utc_now_iso()},
    )
    return session


def revoke_session_token(token: str) -> None:
    token_hash = hash_token(token)
    session = get_record("sessions", token_hash) or get_record("sessions", token)
    if not session:
        return
    update_record(
        "sessions",
        session.get("token_hash", token_hash),
        {"revoked": True, "is_active": False, "updated_at": utc_now_iso()},
    )


def revoke_session_by_id(*, user_id: str, session_id: str) -> bool:
    for session in list_records("sessions"):
        if session.get("id") != session_id:
            continue
        if session.get("user_id") != user_id:
            continue
        update_record(
            "sessions",
            session.get("token_hash", ""),
            {"revoked": True, "is_active": False, "updated_at": utc_now_iso()},
        )
        return True
    return False


def revoke_all_user_sessions(user_id: str, *, except_token: str | None = None) -> None:
    except_hash = hash_token(except_token) if except_token else None
    for session in list_records("sessions"):
        if session.get("user_id") != user_id:
            continue
        token_hash = session.get("token_hash")
        if except_hash and token_hash == except_hash:
            continue
        update_record(
            "sessions",
            token_hash,
            {"revoked": True, "is_active": False, "updated_at": utc_now_iso()},
        )


def list_user_active_sessions(user_id: str) -> list[dict[str, Any]]:
    now = _utc_now()
    result: list[dict[str, Any]] = []
    for session in list_records("sessions"):
        if session.get("user_id") != user_id:
            continue
        if session.get("revoked") or not session.get("is_active", True):
            continue
        expires_at = session.get("expires_at")
        if not expires_at:
            continue
        try:
            if _parse_iso(expires_at) <= now:
                continue
        except Exception:
            continue
        result.append(session)
    result.sort(key=lambda item: item.get("last_used_at", ""), reverse=True)
    return result


def mark_failed_attempt(scope: str, identifier: str, *, limit: int, block_seconds: int) -> int:
    key = f"{scope}:{identifier.lower()}"
    now = _utc_now()
    row = _FAILED_ATTEMPTS.get(key, {"count": 0, "blocked_until": None})
    blocked_until = row.get("blocked_until")
    if blocked_until and blocked_until > now:
        row["count"] = int(row.get("count", 0)) + 1
        _FAILED_ATTEMPTS[key] = row
        return int(row["count"])

    row["count"] = int(row.get("count", 0)) + 1
    if row["count"] >= limit:
        row["blocked_until"] = now + timedelta(seconds=block_seconds)
    _FAILED_ATTEMPTS[key] = row
    return int(row["count"])


def clear_failed_attempts(scope: str, identifier: str) -> None:
    _FAILED_ATTEMPTS.pop(f"{scope}:{identifier.lower()}", None)


def assert_not_blocked(scope: str, identifier: str) -> None:
    row = _FAILED_ATTEMPTS.get(f"{scope}:{identifier.lower()}")
    if not row:
        return
    blocked_until = row.get("blocked_until")
    if blocked_until and blocked_until > _utc_now():
        remaining = int((blocked_until - _utc_now()).total_seconds())
        raise HTTPException(
            status_code=429,
            detail=f"Trop de tentatives. Reessaie dans {max(1, remaining)} secondes.",
        )


def mark_ip_attempt(ip_address: str) -> None:
    now = _utc_now()
    row = _IP_ATTEMPTS.get(ip_address, {"count": 0, "window_start": now, "blocked_until": None})
    if row.get("blocked_until") and row["blocked_until"] > now:
        _IP_ATTEMPTS[ip_address] = row
        return

    window_start = row.get("window_start", now)
    if (now - window_start).total_seconds() > 3600:
        row = {"count": 0, "window_start": now, "blocked_until": None}

    row["count"] = int(row.get("count", 0)) + 1
    if row["count"] >= 50:
        row["blocked_until"] = now + timedelta(hours=1)
    _IP_ATTEMPTS[ip_address] = row


def assert_ip_not_blacklisted(ip_address: str) -> None:
    row = _IP_ATTEMPTS.get(ip_address)
    if not row:
        return
    blocked_until = row.get("blocked_until")
    if blocked_until and blocked_until > _utc_now():
        raise HTTPException(status_code=429, detail="IP temporairement bloquee.")


def should_require_turnstile(email: str) -> bool:
    row = _FAILED_ATTEMPTS.get(f"login:{email.lower()}")
    if not row:
        return False
    return int(row.get("count", 0)) >= 3


def validate_turnstile(token: str | None) -> bool:
    secret = os.getenv("TURNSTILE_SECRET_KEY", "").strip()
    if not secret:
        return True
    if not token:
        return False
    try:
        response = httpx.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token},
            timeout=8,
        )
        body = response.json()
        return bool(body.get("success"))
    except Exception:
        return False


def get_password_history(user: dict) -> list[str]:
    history = user.get("password_history") or []
    if isinstance(history, list):
        return [str(item) for item in history]
    return []


def update_password_history(current_history: list[str], new_hash: str) -> list[str]:
    merged = [new_hash] + [value for value in current_history if value != new_hash]
    return merged[:5]


def password_used_before(password: str, password_history: list[str]) -> bool:
    for old_hash in password_history:
        if verify_password(password, old_hash):
            return True
    return False


def oauth_authorization_url(provider: str, state: str) -> str:
    provider_key = provider.strip().lower()
    config = {
        "google": {
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "scope": "openid email profile",
        },
        "github": {
            "authorize_url": "https://github.com/login/oauth/authorize",
            "scope": "read:user user:email",
        },
        "discord": {
            "authorize_url": "https://discord.com/api/oauth2/authorize",
            "scope": "identify email",
        },
    }.get(provider_key)
    if not config:
        raise HTTPException(status_code=404, detail="Provider OAuth inconnu")

    client_id = os.getenv(f"OAUTH_{provider_key.upper()}_CLIENT_ID", "").strip()
    callback = os.getenv(
        f"OAUTH_{provider_key.upper()}_CALLBACK",
        f"{os.getenv('BACKEND_PUBLIC_URL', 'http://127.0.0.1:8000')}/auth/{provider_key}/callback",
    ).strip()
    if not client_id:
        raise HTTPException(status_code=503, detail=f"OAuth {provider_key} non configure")

    return (
        f"{config['authorize_url']}?client_id={client_id}&redirect_uri={callback}"
        f"&response_type=code&scope={config['scope']}&state={state}"
    )
