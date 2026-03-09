# -*- coding: utf-8 -*-
"""Routes Brand Kit utilisateur."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from database.connection import delete_record, get_record, insert_record, list_records, update_record
from utils.auth import require_current_user
from utils.helpers import new_id, utc_now_iso

router = APIRouter(prefix="/brand", tags=["brand"])


class BrandKitPayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    logo_url: str | None = None
    primary_color: str = Field(default="#7B61FF", max_length=16)
    secondary_color: str = Field(default="#FF61DC", max_length=16)
    caption_font: str = Field(default="Plus Jakarta Sans", max_length=80)
    caption_style: str = Field(default="minimal", max_length=40)
    intro_url: str | None = None
    outro_url: str | None = None
    logo_position: str = Field(default="top-right", max_length=20)
    logo_opacity: int = Field(default=80, ge=0, le=100)
    is_default: bool = False


@router.get("/kits")
def list_brand_kits(current_user: dict = Depends(require_current_user)) -> dict:
    kits = [row for row in list_records("brand_kits") if row.get("user_id") == current_user["id"]]
    kits.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return {"kits": kits}


@router.post("/kits")
def create_brand_kit(payload: BrandKitPayload, current_user: dict = Depends(require_current_user)) -> dict:
    if payload.is_default:
        for item in list_records("brand_kits"):
            if item.get("user_id") == current_user["id"] and item.get("is_default"):
                update_record("brand_kits", item["id"], {"is_default": False, "updated_at": utc_now_iso()})

    kit_id = new_id()
    kit = {
        "id": kit_id,
        "user_id": current_user["id"],
        **payload.model_dump(),
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    insert_record("brand_kits", kit_id, kit)
    return {"kit": kit}


@router.put("/kits/{kit_id}")
def update_brand_kit(kit_id: str, payload: BrandKitPayload, current_user: dict = Depends(require_current_user)) -> dict:
    kit = get_record("brand_kits", kit_id)
    if not kit or kit.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Brand kit introuvable")

    if payload.is_default:
        for item in list_records("brand_kits"):
            if item.get("user_id") == current_user["id"] and item.get("id") != kit_id and item.get("is_default"):
                update_record("brand_kits", item["id"], {"is_default": False, "updated_at": utc_now_iso()})

    updated = update_record(
        "brand_kits",
        kit_id,
        {
            **payload.model_dump(),
            "updated_at": utc_now_iso(),
        },
    )
    return {"kit": updated}


@router.delete("/kits/{kit_id}")
def delete_brand_kit(kit_id: str, current_user: dict = Depends(require_current_user)) -> dict:
    kit = get_record("brand_kits", kit_id)
    if not kit or kit.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Brand kit introuvable")
    delete_record("brand_kits", kit_id)
    return {"message": "Brand kit supprime"}
