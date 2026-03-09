# -*- coding: utf-8 -*-
"""Modeles utilisateur (requetes et reponses API)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    turnstile_token: str | None = None

    model_config = {"extra": "forbid"}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)
    turnstile_token: str | None = None

    model_config = {"extra": "forbid"}


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)

    model_config = {"extra": "forbid"}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    model_config = {"extra": "forbid"}


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)

    model_config = {"extra": "forbid"}


class SessionPublic(BaseModel):
    id: str
    kind: str
    ip_address: str
    user_agent: str
    country: str
    last_used_at: str
    created_at: str
    expires_at: str


class Setup2FAResponse(BaseModel):
    secret_preview: str
    otpauth_url: str
    qr_code_base64: str


class Verify2FARequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)

    model_config = {"extra": "forbid"}


class Disable2FARequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)

    model_config = {"extra": "forbid"}


class OAuthCallbackRequest(BaseModel):
    code: str | None = None
    state: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    requires_2fa: bool = False
    message: str | None = None


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    plan: str = "free"
    is_admin: bool = False
    two_factor_enabled: bool = False
    avatar_url: str | None = None
    bio: str | None = None
    youtube_url: str | None = None
    preferences: dict | None = None
    stripe_customer_id: str | None = None


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=400)
    youtube_url: str | None = Field(default=None, max_length=500)

    model_config = {"extra": "forbid"}


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    model_config = {"extra": "forbid"}


class UpdatePreferencesRequest(BaseModel):
    language: str | None = Field(default=None, max_length=10)
    timezone: str | None = Field(default=None, max_length=60)
    preferred_format: str | None = Field(default=None, max_length=20)
    preferred_quality: str | None = Field(default=None, max_length=20)
    subtitles_default: bool | None = None

    model_config = {"extra": "forbid"}
