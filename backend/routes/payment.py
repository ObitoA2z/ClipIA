# -*- coding: utf-8 -*-
"""Routes paiement Stripe (checkout, statut, annulation, webhook signe)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from database.connection import find_one, get_record, insert_record, list_records, update_record
from services.audit import log_audit
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso
from utils.rate_limit import limiter

router = APIRouter(prefix="/payment", tags=["payment"])


class CheckoutRequest(BaseModel):
    plan: str = Field(pattern="^(pro|business)$")


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _iso_from_stripe_epoch(value: Any) -> str | None:
    try:
        epoch = int(value)
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _stripe_ready() -> bool:
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not stripe_key:
        return False
    stripe.api_key = stripe_key
    return True


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")


def _price_id_for_plan(plan: str) -> str:
    key = "STRIPE_PRICE_PRO" if plan == "pro" else "STRIPE_PRICE_BUSINESS"
    return os.getenv(key, "").strip()


def _plan_from_price_id(price_id: str) -> str:
    if price_id == os.getenv("STRIPE_PRICE_BUSINESS", "").strip():
        return "business"
    if price_id == os.getenv("STRIPE_PRICE_PRO", "").strip():
        return "pro"
    return "pro"


def _find_user_subscription(user_id: str) -> dict | None:
    subs = [row for row in list_records("subscriptions") if row.get("user_id") == user_id]
    if not subs:
        return None
    subs.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return subs[0]


def _upsert_subscription_for_user(
    *,
    user_id: str,
    stripe_subscription_id: str,
    stripe_price_id: str | None,
    status: str,
    current_period_start: str | None = None,
    current_period_end: str | None = None,
    cancel_at_period_end: bool | None = None,
) -> dict:
    existing = find_one("subscriptions", "stripe_subscription_id", stripe_subscription_id)
    now = utc_now_iso()
    payload = {
        "user_id": user_id,
        "stripe_subscription_id": stripe_subscription_id,
        "stripe_price_id": stripe_price_id or "",
        "plan": _plan_from_price_id(stripe_price_id or ""),
        "status": status,
        "current_period_start": current_period_start or "",
        "current_period_end": current_period_end or "",
        "cancel_at_period_end": bool(cancel_at_period_end),
        "updated_at": now,
    }
    if existing:
        update_record("subscriptions", existing["id"], payload)
        return get_record("subscriptions", existing["id"]) or existing

    record_id = new_id()
    insert_record(
        "subscriptions",
        record_id,
        {
            "id": record_id,
            "created_at": now,
            **payload,
        },
    )
    return get_record("subscriptions", record_id) or payload


def _ensure_customer_for_user(user: dict) -> str:
    existing_customer = str(user.get("stripe_customer_id") or "").strip()
    if existing_customer:
        return existing_customer

    customer = stripe.Customer.create(
        email=user.get("email", ""),
        name=user.get("full_name", ""),
        metadata={"user_id": user["id"]},
    )
    customer_id = str(customer.get("id") or "")
    if not customer_id:
        raise HTTPException(status_code=502, detail="Creation client Stripe impossible")
    update_record("users", user["id"], {"stripe_customer_id": customer_id, "updated_at": utc_now_iso()})
    return customer_id


@router.post("/create-checkout")
@limiter.limit("10/minute")
def create_checkout(
    request: Request,
    payload: CheckoutRequest,
    current_user: dict = Depends(require_current_user),
) -> dict:
    plan = payload.plan
    price_id = _price_id_for_plan(plan)
    if not price_id:
        raise HTTPException(status_code=503, detail=f"Prix Stripe non configure pour le plan {plan}")
    if not _stripe_ready():
        raise HTTPException(status_code=503, detail="Stripe non configure")

    customer_id = _ensure_customer_for_user(current_user)
    frontend_url = _frontend_url()

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{frontend_url}/pricing?checkout=success",
            cancel_url=f"{frontend_url}/pricing?checkout=cancel",
            client_reference_id=current_user["id"],
            metadata={"user_id": current_user["id"], "plan": plan},
            allow_promotion_codes=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Echec creation checkout Stripe: {exc}") from exc

    log_audit(
        action="payment.checkout.created",
        success=True,
        user_id=current_user["id"],
        request=request,
        metadata={"plan": plan, "stripe_session_id": session.get("id")},
    )
    return {"checkout_url": session.get("url"), "session_id": session.get("id"), "plan": plan}


@router.post("/cancel")
@limiter.limit("10/minute")
def cancel_subscription(
    request: Request,
    current_user: dict = Depends(require_current_user),
) -> dict:
    subscription = _find_user_subscription(current_user["id"])
    if not subscription:
        raise HTTPException(status_code=404, detail="Aucun abonnement actif")

    stripe_subscription_id = str(subscription.get("stripe_subscription_id") or "")
    if stripe_subscription_id and _stripe_ready():
        try:
            stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Echec annulation Stripe: {exc}") from exc

    update_record(
        "subscriptions",
        subscription["id"],
        {
            "status": "canceled",
            "cancel_at_period_end": True,
            "updated_at": utc_now_iso(),
        },
    )
    update_record("users", current_user["id"], {"plan": "free", "updated_at": utc_now_iso()})
    log_audit(
        action="payment.subscription.cancelled",
        success=True,
        user_id=current_user["id"],
        request=request,
        metadata={"stripe_subscription_id": stripe_subscription_id},
    )
    return {"message": "Abonnement annule", "cancel_at_period_end": True}


@router.get("/status")
def payment_status(current_user: dict = Depends(require_current_user)) -> dict:
    subscription = _find_user_subscription(current_user["id"])
    if not subscription:
        return {"plan": current_user.get("plan", "free"), "status": "inactive"}
    return {
        "plan": subscription.get("plan", current_user.get("plan", "free")),
        "status": subscription.get("status", "inactive"),
        "current_period_end": subscription.get("current_period_end"),
        "cancel_at_period_end": bool(subscription.get("cancel_at_period_end")),
    }


@router.get("/billing-portal")
def billing_portal(current_user: dict = Depends(require_current_user)) -> dict:
    if not _stripe_ready():
        return {"url": f"{_frontend_url()}/pricing"}

    customer_id = str(current_user.get("stripe_customer_id") or "").strip()
    if not customer_id:
        return {"url": f"{_frontend_url()}/pricing"}

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{_frontend_url()}/profile",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Echec portail billing Stripe: {exc}") from exc
    return {"url": session.get("url")}


def _user_id_from_customer(customer_id: str) -> str | None:
    user = find_one("users", "stripe_customer_id", customer_id)
    if user:
        return user.get("id")
    return None


def _handle_checkout_completed(event_payload: dict) -> None:
    customer_id = str(event_payload.get("customer") or "")
    user_id = str(event_payload.get("client_reference_id") or event_payload.get("metadata", {}).get("user_id") or "")
    subscription_id = str(event_payload.get("subscription") or "")
    if not user_id and customer_id:
        user_id = _user_id_from_customer(customer_id) or ""
    if not user_id or not subscription_id:
        return
    if customer_id:
        update_record("users", user_id, {"stripe_customer_id": customer_id, "updated_at": utc_now_iso()})

    plan = str(event_payload.get("metadata", {}).get("plan") or "pro")
    price_id = _price_id_for_plan(plan)
    _upsert_subscription_for_user(
        user_id=user_id,
        stripe_subscription_id=subscription_id,
        stripe_price_id=price_id,
        status="active",
    )
    update_record("users", user_id, {"plan": plan, "updated_at": utc_now_iso()})


def _handle_subscription_event(subscription_payload: dict) -> None:
    customer_id = str(subscription_payload.get("customer") or "")
    user_id = _user_id_from_customer(customer_id) or ""
    if not user_id:
        return

    items = subscription_payload.get("items", {}).get("data", [])
    first_item = items[0] if items else {}
    price_id = str((first_item.get("price") or {}).get("id") or "")
    status = str(subscription_payload.get("status") or "inactive")
    period_start = _iso_from_stripe_epoch(subscription_payload.get("current_period_start"))
    period_end = _iso_from_stripe_epoch(subscription_payload.get("current_period_end"))
    cancel_at_period_end = bool(subscription_payload.get("cancel_at_period_end"))

    _upsert_subscription_for_user(
        user_id=user_id,
        stripe_subscription_id=str(subscription_payload.get("id") or ""),
        stripe_price_id=price_id,
        status=status,
        current_period_start=period_start,
        current_period_end=period_end,
        cancel_at_period_end=cancel_at_period_end,
    )
    next_plan = "free" if status in {"canceled", "unpaid", "incomplete_expired"} else _plan_from_price_id(price_id)
    update_record("users", user_id, {"plan": next_plan, "updated_at": utc_now_iso()})


def _handle_invoice_failed(invoice_payload: dict) -> None:
    customer_id = str(invoice_payload.get("customer") or "")
    user_id = _user_id_from_customer(customer_id) or ""
    if not user_id:
        return
    sub = _find_user_subscription(user_id)
    if sub:
        update_record("subscriptions", sub["id"], {"status": "past_due", "updated_at": utc_now_iso()})


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict:
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook secret non configure")
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Header Stripe-Signature manquant")
    if not _stripe_ready():
        raise HTTPException(status_code=503, detail="Stripe non configure")

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

    event_type = str(event.get("type") or "")
    obj = event.get("data", {}).get("object", {})
    if event_type == "checkout.session.completed":
        _handle_checkout_completed(obj)
    elif event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        _handle_subscription_event(obj)
    elif event_type == "invoice.payment_failed":
        _handle_invoice_failed(obj)

    return {"received": True, "event_type": event_type}
