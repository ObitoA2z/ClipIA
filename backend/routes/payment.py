# -*- coding: utf-8 -*-
"""Routes paiement (mock local)."""

import os

import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/payment", tags=["payment"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "").strip()


class CheckoutRequest(BaseModel):
    plan: str


@router.post("/create-checkout")
def create_checkout(payload: CheckoutRequest) -> dict:
    return {
        "checkout_url": f"https://checkout.clipai.local/{payload.plan}",
        "message": "Mock checkout créé",
    }


@router.post("/cancel")
def cancel_subscription() -> dict:
    return {"message": "Abonnement annulé (mock)"}


@router.get("/status")
def payment_status() -> dict:
    return {"plan": "free", "status": "active"}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict:
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook secret non configuré")
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Header Stripe-Signature manquant")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Payload webhook invalide: {exc}") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail=f"Signature webhook invalide: {exc}") from exc

    return {"received": True, "event_type": event.get("type", "unknown")}
