# -*- coding: utf-8 -*-
"""Routes d'authentification securisees pour ClipAI."""

import secrets
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from database.connection import find_one, get_record, insert_record, list_records, update_record
from models.user import (
    ChangePasswordRequest,
    Disable2FARequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionPublic,
    Setup2FAResponse,
    TokenResponse,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
    UserPublic,
    Verify2FARequest,
)
from services.audit import log_audit, notify_security_event
from services.auth_security import (
    assert_ip_not_blacklisted,
    assert_not_blocked,
    build_totp_uri,
    clear_failed_attempts,
    encrypt_totp_secret,
    extract_bearer_token,
    generate_qr_code_base64,
    generate_totp_secret,
    get_client_ip,
    get_password_history,
    hash_password,
    hash_token,
    is_pwned_password,
    issue_token_pair,
    list_user_active_sessions,
    mark_failed_attempt,
    mark_ip_attempt,
    oauth_authorization_url,
    password_used_before,
    revoke_all_user_sessions,
    revoke_session_by_id,
    revoke_session_token,
    should_require_turnstile,
    update_password_history,
    validate_password_policy,
    validate_session_token,
    validate_turnstile,
    verify_password,
    verify_totp_code,
)
from utils.auth import require_current_user, user_from_refresh_token
from utils.helpers import new_id, utc_now_iso
from utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

REGISTER_RATE_LIMIT = os.getenv("REGISTER_RATE_LIMIT", "30/minute")
LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
FORGOT_PASSWORD_RATE_LIMIT = os.getenv("FORGOT_PASSWORD_RATE_LIMIT", "10/day")


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _build_user_public(user: dict) -> UserPublic:
    return UserPublic(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name") or "",
        plan=user.get("plan", "free"),
        is_admin=bool(user.get("is_admin", False)),
        two_factor_enabled=bool(user.get("two_factor_enabled", False)),
        avatar_url=user.get("avatar_url"),
        bio=user.get("bio"),
        youtube_url=user.get("youtube_url"),
        preferences=user.get("preferences") or {},
        stripe_customer_id=user.get("stripe_customer_id"),
    )


def _build_tokens_for_user(*, user_id: str, request: Request) -> TokenResponse:
    tokens = issue_token_pair(
        user_id=user_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        country=(request.headers.get("x-vercel-ip-country") or request.headers.get("cf-ipcountry") or "ZZ"),
    )
    return TokenResponse(**tokens)


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit(REGISTER_RATE_LIMIT)
def register(request: Request, payload: RegisterRequest = Body(...)) -> TokenResponse:
    email = payload.email.lower().strip()
    assert_ip_not_blacklisted(get_client_ip(request))

    if should_require_turnstile(email) and not validate_turnstile(payload.turnstile_token):
        raise HTTPException(status_code=400, detail="Validation CAPTCHA requise")

    password_ok, password_error = validate_password_policy(payload.password)
    if not password_ok:
        raise HTTPException(status_code=400, detail=password_error)
    if is_pwned_password(payload.password):
        raise HTTPException(status_code=400, detail="Mot de passe compromis (haveibeenpwned).")

    if find_one("users", "email", email):
        raise HTTPException(status_code=409, detail="Email deja utilise")

    user_id = new_id()
    now = utc_now_iso()
    password_hash = hash_password(payload.password)
    totp_secret = generate_totp_secret()
    user_record = {
        "id": user_id,
        "email": email,
        "full_name": payload.full_name.strip(),
        "avatar_url": "",
        "bio": "",
        "youtube_url": "",
        "password_hash": password_hash,
        "password_history": [password_hash],
        "plan": "free",
        "videos_used_this_month": 0,
        "preferences": {
            "language": "fr",
            "timezone": "Europe/Paris",
            "preferred_format": "all",
            "preferred_quality": "1080p",
            "subtitles_default": True,
        },
        "totp_secret_encrypted": "",
        "pending_totp_secret_encrypted": encrypt_totp_secret(user_id, totp_secret),
        "two_factor_enabled": False,
        "is_admin": False,
        "created_at": now,
        "updated_at": now,
    }
    insert_record("users", user_id, user_record)
    response = _build_tokens_for_user(user_id=user_id, request=request)
    log_audit(
        action="auth.register",
        success=True,
        user_id=user_id,
        request=request,
        metadata={"plan": "free"},
    )
    return response


@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
def login(request: Request, payload: LoginRequest = Body(...)) -> TokenResponse:
    email = payload.email.lower().strip()
    ip_address = get_client_ip(request)

    assert_ip_not_blacklisted(ip_address)
    assert_not_blocked("login", email)
    if should_require_turnstile(email) and not validate_turnstile(payload.turnstile_token):
        raise HTTPException(status_code=400, detail="Validation CAPTCHA requise")

    user = find_one("users", "email", email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        mark_failed_attempt("login", email, limit=5, block_seconds=15 * 60)
        mark_ip_attempt(ip_address)
        log_audit(
            action="auth.login",
            success=False,
            user_id=user.get("id") if user else None,
            request=request,
            metadata={"reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if user.get("is_banned"):
        raise HTTPException(status_code=403, detail="Compte banni. Contacte le support.")
    if user.get("is_suspended"):
        raise HTTPException(status_code=403, detail="Compte suspendu temporairement.")

    if bool(user.get("two_factor_enabled")):
        assert_not_blocked("2fa", email)
        if not payload.totp_code:
            raise HTTPException(status_code=401, detail="Code 2FA requis")
        if not verify_totp_code(
            user_id=user["id"],
            encrypted_secret=user.get("totp_secret_encrypted", ""),
            code=payload.totp_code,
        ):
            mark_failed_attempt("2fa", email, limit=3, block_seconds=60 * 60)
            log_audit(
                action="auth.login.2fa_failed",
                success=False,
                user_id=user["id"],
                request=request,
            )
            raise HTTPException(status_code=401, detail="Code 2FA invalide")

    clear_failed_attempts("login", email)
    clear_failed_attempts("2fa", email)

    previous_sessions = list_user_active_sessions(user["id"])
    is_new_country = bool(
        previous_sessions and all(item.get("country") != request.headers.get("x-vercel-ip-country", "ZZ") for item in previous_sessions)
    )
    response = _build_tokens_for_user(user_id=user["id"], request=request)

    log_audit(
        action="auth.login",
        success=True,
        user_id=user["id"],
        request=request,
        metadata={"two_factor": bool(user.get("two_factor_enabled"))},
    )

    if is_new_country:
        notify_security_event(
            event_type="new_country_login",
            email=user["email"],
            details={"country": request.headers.get("x-vercel-ip-country", "ZZ")},
        )
    return response


@router.post("/logout")
def logout(request: Request, authorization: str | None = Header(default=None)) -> dict:
    token = extract_bearer_token(authorization)
    session = validate_session_token(token, kind="access")
    revoke_all_user_sessions(session["user_id"])
    log_audit(action="auth.logout", success=True, user_id=session["user_id"], request=request)
    return {"message": "Deconnecte"}


@router.get("/me", response_model=UserPublic)
def me(current_user: dict = Depends(require_current_user)) -> UserPublic:
    return _build_user_public(current_user)


@router.put("/me", response_model=UserPublic)
def update_me(
    request: Request,
    payload: UpdateProfileRequest = Body(...),
    current_user: dict = Depends(require_current_user),
) -> UserPublic:
    updates: dict = {"updated_at": utc_now_iso()}
    if payload.full_name is not None:
        full_name = payload.full_name.strip()
        if len(full_name) < 2:
            raise HTTPException(status_code=400, detail="Nom complet invalide")
        updates["full_name"] = full_name
    if payload.avatar_url is not None:
        updates["avatar_url"] = payload.avatar_url.strip()
    if payload.bio is not None:
        updates["bio"] = payload.bio.strip()
    if payload.youtube_url is not None:
        updates["youtube_url"] = payload.youtube_url.strip()

    update_record("users", current_user["id"], updates)
    refreshed = get_record("users", current_user["id"]) or current_user
    log_audit(
        action="auth.profile.updated",
        success=True,
        user_id=current_user["id"],
        request=request,
    )
    return _build_user_public(refreshed)


@router.post("/change-password")
def change_password(
    request: Request,
    payload: ChangePasswordRequest = Body(...),
    current_user: dict = Depends(require_current_user),
) -> dict:
    user = get_record("users", current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if not verify_password(payload.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Mot de passe actuel invalide")

    password_ok, password_error = validate_password_policy(payload.new_password)
    if not password_ok:
        raise HTTPException(status_code=400, detail=password_error)
    if is_pwned_password(payload.new_password):
        raise HTTPException(status_code=400, detail="Mot de passe compromis (haveibeenpwned).")

    history = get_password_history(user)
    if password_used_before(payload.new_password, history):
        raise HTTPException(status_code=400, detail="Tu as deja utilise ce mot de passe.")

    new_hash = hash_password(payload.new_password)
    update_record(
        "users",
        current_user["id"],
        {
            "password_hash": new_hash,
            "password_history": update_password_history(history, new_hash),
            "updated_at": utc_now_iso(),
        },
    )
    revoke_all_user_sessions(current_user["id"])
    log_audit(
        action="auth.password.changed",
        success=True,
        user_id=current_user["id"],
        request=request,
    )
    return {"message": "Mot de passe mis a jour, reconnecte-toi."}


@router.get("/preferences")
def get_preferences(current_user: dict = Depends(require_current_user)) -> dict:
    user = get_record("users", current_user["id"]) or current_user
    return {"preferences": user.get("preferences") or {}}


@router.put("/preferences")
def update_preferences(
    request: Request,
    payload: UpdatePreferencesRequest = Body(...),
    current_user: dict = Depends(require_current_user),
) -> dict:
    user = get_record("users", current_user["id"]) or current_user
    preferences = dict(user.get("preferences") or {})
    if payload.language is not None:
        preferences["language"] = payload.language.strip() or "fr"
    if payload.timezone is not None:
        preferences["timezone"] = payload.timezone.strip() or "Europe/Paris"
    if payload.preferred_format is not None:
        preferences["preferred_format"] = payload.preferred_format.strip() or "all"
    if payload.preferred_quality is not None:
        preferences["preferred_quality"] = payload.preferred_quality.strip() or "1080p"
    if payload.subtitles_default is not None:
        preferences["subtitles_default"] = bool(payload.subtitles_default)

    update_record(
        "users",
        current_user["id"],
        {"preferences": preferences, "updated_at": utc_now_iso()},
    )
    log_audit(
        action="auth.preferences.updated",
        success=True,
        user_id=current_user["id"],
        request=request,
    )
    return {"message": "Preferences mises a jour", "preferences": preferences}


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, payload: RefreshRequest) -> TokenResponse:
    user = user_from_refresh_token(payload.refresh_token)
    revoke_session_token(payload.refresh_token)
    response = _build_tokens_for_user(user_id=user["id"], request=request)
    log_audit(
        action="auth.refresh",
        success=True,
        user_id=user["id"],
        request=request,
    )
    return response


@router.get("/sessions", response_model=list[SessionPublic])
def list_sessions(current_user: dict = Depends(require_current_user)) -> list[SessionPublic]:
    sessions = list_user_active_sessions(current_user["id"])
    return [
        SessionPublic(
            id=item["id"],
            kind=item["kind"],
            ip_address=item.get("ip_address", ""),
            user_agent=item.get("user_agent", ""),
            country=item.get("country", "ZZ"),
            last_used_at=item.get("last_used_at", item.get("created_at", "")),
            created_at=item.get("created_at", ""),
            expires_at=item.get("expires_at", ""),
        )
        for item in sessions
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    revoked = revoke_session_by_id(user_id=current_user["id"], session_id=session_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Session introuvable")
    log_audit(
        action="auth.session.revoke",
        success=True,
        user_id=current_user["id"],
        resource_type="session",
        resource_id=session_id,
        request=request,
    )
    return {"message": "Session revoquee"}


@router.get("/2fa/setup", response_model=Setup2FAResponse)
def setup_2fa(
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> Setup2FAResponse:
    secret = generate_totp_secret()
    encrypted = encrypt_totp_secret(current_user["id"], secret)
    update_record(
        "users",
        current_user["id"],
        {"pending_totp_secret_encrypted": encrypted, "updated_at": utc_now_iso()},
    )
    otpauth_url = build_totp_uri(current_user["email"], secret)
    qr_code_base64 = generate_qr_code_base64(otpauth_url)
    log_audit(
        action="auth.2fa.setup",
        success=True,
        user_id=current_user["id"],
        request=request,
    )
    return Setup2FAResponse(
        secret_preview=f"***{secret[-4:]}",
        otpauth_url=otpauth_url,
        qr_code_base64=qr_code_base64,
    )


@router.post("/2fa/enable")
def enable_2fa(
    payload: Verify2FARequest,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    user = get_record("users", current_user["id"])
    pending = (user or {}).get("pending_totp_secret_encrypted", "")
    if not pending:
        raise HTTPException(status_code=400, detail="Setup 2FA requis")
    if not verify_totp_code(user_id=current_user["id"], encrypted_secret=pending, code=payload.code):
        raise HTTPException(status_code=401, detail="Code 2FA invalide")
    update_record(
        "users",
        current_user["id"],
        {
            "two_factor_enabled": True,
            "totp_secret_encrypted": pending,
            "pending_totp_secret_encrypted": "",
            "updated_at": utc_now_iso(),
        },
    )
    log_audit(action="auth.2fa.enable", success=True, user_id=current_user["id"], request=request)
    return {"message": "2FA active"}


@router.post("/2fa/disable")
def disable_2fa(
    payload: Disable2FARequest,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    user = get_record("users", current_user["id"])
    if not user or not user.get("two_factor_enabled"):
        raise HTTPException(status_code=400, detail="2FA deja desactive")
    if not verify_totp_code(
        user_id=current_user["id"],
        encrypted_secret=user.get("totp_secret_encrypted", ""),
        code=payload.code,
    ):
        raise HTTPException(status_code=401, detail="Code 2FA invalide")
    update_record(
        "users",
        current_user["id"],
        {
            "two_factor_enabled": False,
            "totp_secret_encrypted": "",
            "pending_totp_secret_encrypted": "",
            "updated_at": utc_now_iso(),
        },
    )
    log_audit(action="auth.2fa.disable", success=True, user_id=current_user["id"], request=request)
    return {"message": "2FA desactive"}


@router.post("/forgot-password")
@limiter.limit(FORGOT_PASSWORD_RATE_LIMIT)
def forgot_password(request: Request, payload: ForgotPasswordRequest = Body(...)) -> dict:
    email = payload.email.lower().strip()
    user = find_one("users", "email", email)
    if user:
        raw_token = secrets.token_urlsafe(48)
        token_hash = hash_token(raw_token)
        expires_at = (_utc_now() + timedelta(hours=1)).isoformat()
        update_record(
            "users",
            user["id"],
            {
                "password_reset_token_hash": token_hash,
                "password_reset_expires_at": expires_at,
                "updated_at": utc_now_iso(),
            },
        )
        log_audit(
            action="auth.password_reset.requested",
            success=True,
            user_id=user["id"],
            request=request,
            metadata={"token_preview": f"{raw_token[:8]}..."},
        )
    return {"message": "Si le compte existe, un email de reinitialisation est envoye."}


@router.post("/reset-password")
def reset_password(request: Request, payload: ResetPasswordRequest = Body(...)) -> dict:
    password_ok, password_error = validate_password_policy(payload.new_password)
    if not password_ok:
        raise HTTPException(status_code=400, detail=password_error)
    if is_pwned_password(payload.new_password):
        raise HTTPException(status_code=400, detail="Mot de passe compromis (haveibeenpwned).")

    token_hash = hash_token(payload.token)
    candidate_user = None
    for user in list_records("users"):
        if user.get("password_reset_token_hash") != token_hash:
            continue
        expires = user.get("password_reset_expires_at")
        if not expires:
            continue
        try:
            if datetime.fromisoformat(expires) <= _utc_now():
                continue
        except Exception:
            continue
        candidate_user = user
        break

    if not candidate_user:
        raise HTTPException(status_code=400, detail="Token invalide ou expire")

    history = candidate_user.get("password_history") or []
    if password_used_before(payload.new_password, history):
        raise HTTPException(status_code=400, detail="Tu as deja utilise ce mot de passe.")

    new_hash = hash_password(payload.new_password)
    update_record(
        "users",
        candidate_user["id"],
        {
            "password_hash": new_hash,
            "password_history": update_password_history(history, new_hash),
            "password_reset_token_hash": "",
            "password_reset_expires_at": "",
            "updated_at": utc_now_iso(),
        },
    )
    revoke_all_user_sessions(candidate_user["id"])
    log_audit(
        action="auth.password_reset.completed",
        success=True,
        user_id=candidate_user["id"],
        request=request,
    )
    return {"message": "Mot de passe mis a jour"}


def _oauth_redirect(provider: str) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    url = oauth_authorization_url(provider, state=state)
    return RedirectResponse(url=url, status_code=307)


@router.get("/google")
def google_oauth_redirect() -> RedirectResponse:
    return _oauth_redirect("google")


@router.get("/github")
def github_oauth_redirect() -> RedirectResponse:
    return _oauth_redirect("github")


@router.get("/discord")
def discord_oauth_redirect() -> RedirectResponse:
    return _oauth_redirect("discord")


@router.get("/google/callback")
def google_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> dict:
    return {"provider": "google", "code_received": bool(code), "state_received": bool(state)}


@router.get("/github/callback")
def github_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> dict:
    return {"provider": "github", "code_received": bool(code), "state_received": bool(state)}


@router.get("/discord/callback")
def discord_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
) -> dict:
    return {"provider": "discord", "code_received": bool(code), "state_received": bool(state)}
