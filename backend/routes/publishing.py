# -*- coding: utf-8 -*-
"""Routes publishing multi-plateformes (tokens OAuth utilisateur)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import get_record, insert_record, list_records, update_record
from services.encryption import decrypt_text, encrypt_text
from services.publishing_service import publish_scheduled_post
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

router = APIRouter(prefix="/publishing", tags=["publishing"])


class SocialConnectRequest(BaseModel):
    platform: str = Field(pattern="^(tiktok|youtube|instagram|linkedin|twitter)$")
    platform_user_id: str = Field(min_length=2, max_length=200)
    platform_username: str | None = Field(default=None, max_length=200)
    access_token: str = Field(min_length=10)
    refresh_token: str | None = Field(default=None)
    expires_at: str | None = Field(default=None)


class PublishNowRequest(BaseModel):
    clip_id: str = Field(min_length=6)
    platform: str = Field(pattern="^(tiktok|youtube|instagram|linkedin|twitter)$")
    title: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=2200)
    hashtags: list[str] = Field(default_factory=list)


def _find_social_account(user_id: str, platform: str):
    accounts = [
        row
        for row in list_records("social_accounts")
        if row.get("user_id") == user_id and row.get("platform") == platform and row.get("is_active", True)
    ]
    return accounts[0] if accounts else None


@router.post("/accounts/connect")
def connect_social_account(payload: SocialConnectRequest, current_user: dict = Depends(require_current_user)) -> dict:
    existing = _find_social_account(current_user["id"], payload.platform)
    encrypted_access = encrypt_text(payload.access_token, context=f"social:{current_user['id']}:{payload.platform}")
    encrypted_refresh = (
        encrypt_text(payload.refresh_token, context=f"social:{current_user['id']}:{payload.platform}")
        if payload.refresh_token
        else None
    )

    if existing:
        updated = update_record(
            "social_accounts",
            existing["id"],
            {
                "platform_user_id": payload.platform_user_id,
                "platform_username": payload.platform_username,
                "access_token_encrypted": encrypted_access,
                "refresh_token_encrypted": encrypted_refresh,
                "expires_at": payload.expires_at,
                "is_active": True,
                "updated_at": utc_now_iso(),
            },
        )
        return {"message": "Compte social mis a jour", "account": updated}

    account_id = new_id()
    account = {
        "id": account_id,
        "user_id": current_user["id"],
        "platform": payload.platform,
        "platform_user_id": payload.platform_user_id,
        "platform_username": payload.platform_username,
        "access_token_encrypted": encrypted_access,
        "refresh_token_encrypted": encrypted_refresh,
        "expires_at": payload.expires_at,
        "is_active": True,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    insert_record("social_accounts", account_id, account)
    return {"message": "Compte social connecte", "account": account}


@router.get("/accounts")
def list_social_accounts(current_user: dict = Depends(require_current_user)) -> dict:
    accounts = [
        row
        for row in list_records("social_accounts")
        if row.get("user_id") == current_user["id"]
    ]
    safe_accounts = [
        {
            "id": row.get("id"),
            "platform": row.get("platform"),
            "platform_user_id": row.get("platform_user_id"),
            "platform_username": row.get("platform_username"),
            "is_active": row.get("is_active", True),
            "expires_at": row.get("expires_at"),
            "created_at": row.get("created_at"),
        }
        for row in accounts
    ]
    return {"accounts": safe_accounts}


@router.post("/publish-now")
def publish_now(payload: PublishNowRequest, current_user: dict = Depends(require_current_user)) -> dict:
    clip = get_record("clips", payload.clip_id)
    if not clip or clip.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Clip introuvable")

    account = _find_social_account(current_user["id"], payload.platform)
    if not account:
        raise HTTPException(status_code=400, detail=f"Compte {payload.platform} non connecte")

    decrypt_text(account["access_token_encrypted"], context=f"social:{current_user['id']}:{payload.platform}")
    result = publish_scheduled_post(
        {
            "user_id": current_user["id"],
            "platform": payload.platform,
            "clip_id": payload.clip_id,
        }
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=str(result.get("error") or "publish_failed"))

    return {
        "status": "published",
        "platform": payload.platform,
        "post_id": result.get("post_id"),
        "url": result.get("url"),
        "title": payload.title,
        "hashtags": payload.hashtags,
    }
