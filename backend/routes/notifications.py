# -*- coding: utf-8 -*-
"""Routes push notifications (PWA/web push)."""


import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from database.connection import insert_record, list_records
from services.audit import log_audit
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

try:
    from pywebpush import WebPushException, webpush
except Exception:  # pragma: no cover - optional runtime import
    WebPushException = Exception
    webpush = None

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(min_length=16)
    auth: str = Field(min_length=8)


class PushSubscriptionRequest(BaseModel):
    endpoint: str = Field(min_length=20)
    keys: PushSubscriptionKeys


class PushMessageRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=500)
    url: str = Field(default="/dashboard", min_length=1, max_length=500)
    send_to_all: bool = False


def _vapid_private_key() -> str:
    return os.getenv("VAPID_PRIVATE_KEY", "").strip()


def _vapid_public_key() -> str:
    return os.getenv("VAPID_PUBLIC_KEY", "").strip()


def _vapid_claims() -> dict[str, str]:
    subject = os.getenv("VAPID_SUBJECT", "mailto:security@clipai.local").strip()
    return {"sub": subject}


@router.get("/public-key")
def get_public_key() -> dict:
    value = _vapid_public_key()
    if not value:
        raise HTTPException(status_code=503, detail="VAPID_PUBLIC_KEY non configuree")
    return {"public_key": value}


@router.post("/subscribe")
def subscribe(
    payload: PushSubscriptionRequest,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    subscription_id = new_id()
    insert_record(
        "push_subscriptions",
        subscription_id,
        {
            "id": subscription_id,
            "user_id": current_user["id"],
            "endpoint": payload.endpoint,
            "p256dh": payload.keys.p256dh,
            "auth": payload.keys.auth,
            "created_at": utc_now_iso(),
        },
    )
    log_audit(
        action="push.subscribe",
        success=True,
        user_id=current_user["id"],
        resource_type="push_subscription",
        resource_id=subscription_id,
        request=request,
    )
    return {"message": "Subscription enregistree", "subscription_id": subscription_id}


@router.post("/send")
def send_push(
    payload: PushMessageRequest,
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    if not webpush:
        raise HTTPException(status_code=503, detail="pywebpush indisponible")

    private_key = _vapid_private_key()
    if not private_key:
        raise HTTPException(status_code=503, detail="VAPID_PRIVATE_KEY non configuree")

    subscriptions = list_records("push_subscriptions")
    if not payload.send_to_all:
        subscriptions = [sub for sub in subscriptions if sub.get("user_id") == current_user["id"]]

    delivered = 0
    errors = 0
    body = json.dumps({"title": payload.title, "body": payload.body, "url": payload.url})

    for subscription in subscriptions:
        info = {
            "endpoint": subscription.get("endpoint"),
            "keys": {
                "p256dh": subscription.get("p256dh"),
                "auth": subscription.get("auth"),
            },
        }
        try:
            webpush(
                subscription_info=info,
                data=body,
                vapid_private_key=private_key,
                vapid_claims=_vapid_claims(),
            )
            delivered += 1
        except WebPushException:
            errors += 1

    log_audit(
        action="push.send",
        success=errors == 0,
        user_id=current_user["id"],
        request=request,
        metadata={"delivered": delivered, "errors": errors, "broadcast": payload.send_to_all},
    )
    return {"delivered": delivered, "errors": errors}

