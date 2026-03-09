# -*- coding: utf-8 -*-
"""Routes parrainage utilisateur."""


import random
import string

from fastapi import APIRouter, Depends, HTTPException

from database.connection import find_one, insert_record, list_records
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

router = APIRouter(prefix="/referral", tags=["referral"])


def _new_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _ensure_referral_code(user_id: str) -> str:
    existing = find_one("referrals", "referrer_id", user_id)
    if existing and existing.get("code"):
        return existing["code"]

    code = _new_code()
    insert_record(
        "referrals",
        new_id(),
        {
            "id": new_id(),
            "referrer_id": user_id,
            "referred_id": None,
            "code": code,
            "status": "owner",
            "reward_given": False,
            "created_at": utc_now_iso(),
        },
    )
    return code


@router.get("/me")
def my_referral_dashboard(current_user: dict = Depends(require_current_user)) -> dict:
    code = _ensure_referral_code(current_user["id"])
    rows = [row for row in list_records("referrals") if row.get("referrer_id") == current_user["id"]]
    invited = len([row for row in rows if row.get("status") == "pending"])
    active = len([row for row in rows if row.get("status") == "active"])
    rewards = len([row for row in rows if row.get("reward_given")])
    return {
        "code": code,
        "referral_url": f"https://clipai.vercel.app/ref/{code}",
        "invited": invited,
        "active": active,
        "rewards": rewards,
        "history": rows,
    }


@router.post("/claim/{code}")
def claim_referral(code: str, current_user: dict = Depends(require_current_user)) -> dict:
    owner = find_one("referrals", "code", code.upper())
    if not owner:
        raise HTTPException(status_code=404, detail="Code de parrainage introuvable")
    if owner.get("referrer_id") == current_user["id"]:
        raise HTTPException(status_code=400, detail="Tu ne peux pas utiliser ton propre code")

    entry_id = new_id()
    insert_record(
        "referrals",
        entry_id,
        {
            "id": entry_id,
            "referrer_id": owner["referrer_id"],
            "referred_id": current_user["id"],
            "code": code.upper(),
            "status": "pending",
            "reward_given": False,
            "created_at": utc_now_iso(),
        },
    )
    return {"message": "Code appliqué. L'essai Pro étendu sera activé après confirmation."}

