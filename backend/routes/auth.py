# -*- coding: utf-8 -*-
"""Routes d'authentification securisees pour ClipAI."""

import bcrypt
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request

from database.connection import find_one, get_record, insert_record
from models.user import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserPublic
from utils.auth import (
    extract_bearer_token,
    issue_tokens,
    require_current_user,
    revoke_all_tokens_for_user,
    revoke_token,
    user_from_refresh_token,
)
from utils.helpers import new_id, utc_now_iso
from utils.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest) -> TokenResponse:
    normalized_email = payload.email.lower()
    existing = find_one("users", "email", normalized_email)
    if existing:
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user_id = new_id()
    now = utc_now_iso()
    record = {
        "id": user_id,
        "email": normalized_email,
        "full_name": payload.full_name,
        "password_hash": _hash_password(payload.password),
        "plan": "free",
        "videos_used_this_month": 0,
        "created_at": now,
        "updated_at": now,
    }
    insert_record("users", user_id, record)
    return TokenResponse(**issue_tokens(user_id))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest = Body(...)) -> TokenResponse:
    normalized_email = payload.email.lower()
    user = find_one("users", "email", normalized_email)
    if not user or not _verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    return TokenResponse(**issue_tokens(user["id"]))


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    token = extract_bearer_token(authorization)
    session = get_record("sessions", token)
    if not session or session.get("revoked"):
        raise HTTPException(status_code=401, detail="Session introuvable")
    revoke_all_tokens_for_user(session["user_id"])
    return {"message": "Déconnecté"}


@router.get("/me", response_model=UserPublic)
def me(current_user: dict = Depends(require_current_user)) -> UserPublic:
    return UserPublic(**current_user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest) -> TokenResponse:
    user = user_from_refresh_token(payload.refresh_token)
    revoke_token(payload.refresh_token)
    return TokenResponse(**issue_tokens(user["id"]))


@router.post("/forgot-password")
def forgot_password() -> dict:
    return {"message": "Endpoint prêt (MVP)."}


@router.post("/reset-password")
def reset_password() -> dict:
    return {"message": "Endpoint prêt (MVP)."}
