# -*- coding: utf-8 -*-
"""Service de publication multi-plateformes (version robuste locale)."""

from __future__ import annotations

from typing import Any

from database.connection import list_records
from services.encryption import decrypt_text
from utils.helpers import new_id


def _find_social_account(user_id: str, platform: str) -> dict[str, Any] | None:
    for account in list_records("social_accounts"):
        if (
            account.get("user_id") == user_id
            and account.get("platform") == platform
            and account.get("is_active", True)
        ):
            return account
    return None


def publish_scheduled_post(post: dict[str, Any]) -> dict[str, Any]:
    """Publie un post planifie et renvoie un resultat standard."""
    user_id = str(post.get("user_id") or "")
    platform = str(post.get("platform") or "").strip().lower()
    account = _find_social_account(user_id, platform)
    if not account:
        return {"ok": False, "error": f"social_account_missing:{platform}"}

    try:
        decrypt_text(
            str(account.get("access_token_encrypted") or ""),
            context=f"social:{user_id}:{platform}",
        )
    except Exception:
        return {"ok": False, "error": f"token_invalid:{platform}"}

    # Placeholder deterministic ID/URL in local environment.
    post_id = f"{platform}_{new_id()[:10]}"
    url = f"https://{platform}.com/post/{post_id}"
    return {"ok": True, "post_id": post_id, "url": url}
