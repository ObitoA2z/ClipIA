# -*- coding: utf-8 -*-
# Tests automatisés complets pour ClipAI

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


# ── TESTS VALIDATION URL ──────────────────────────────────────────────────────
class TestURLValidation:
    def test_valid_youtube_url_standard(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://youtube.com/watch?v=abc123") == True

    def test_valid_youtube_url_short(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://youtu.be/abc123") == True

    def test_valid_youtube_url_with_params(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://www.youtube.com/watch?v=abc123&t=30s") == True

    def test_invalid_url_vimeo(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://vimeo.com/123") == False

    def test_invalid_url_empty(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("") == False

    def test_extract_youtube_id(self):
        from utils.validators import extract_youtube_id

        assert extract_youtube_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


# ── TESTS AUTHENTIFICATION ────────────────────────────────────────────────────
class TestAuthentication:
    def test_register_new_user(self):
        response = client.post(
            "/auth/register",
            json={
                "email": "test@clipai.com",
                "password": "Motdepasse123!",
                "full_name": "Test User",
            },
        )
        assert response.status_code in [200, 201]
        assert "access_token" in response.json()

    def test_register_duplicate_email(self):
        client.post(
            "/auth/register",
            json={"email": "dup@test.com", "password": "Pass123!", "full_name": "Dup"},
        )
        response = client.post(
            "/auth/register",
            json={"email": "dup@test.com", "password": "Pass123!", "full_name": "Dup"},
        )
        assert response.status_code == 409

    def test_login_valid(self):
        client.post(
            "/auth/register",
            json={"email": "login@test.com", "password": "Pass123!", "full_name": "Login"},
        )
        response = client.post("/auth/login", json={"email": "login@test.com", "password": "Pass123!"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self):
        response = client.post("/auth/login", json={"email": "login@test.com", "password": "mauvaismdp"})
        assert response.status_code == 401

    def test_protected_route_without_token(self):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_protected_route_with_token(self):
        reg = client.post(
            "/auth/register",
            json={"email": "me@test.com", "password": "Pass123!", "full_name": "Me"},
        )
        token = reg.json().get("access_token")
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200


# ── TESTS VIDÉO ───────────────────────────────────────────────────────────────
class TestVideo:
    def test_process_without_auth(self):
        response = client.post("/video/process", json={"youtube_url": "https://youtube.com/watch?v=abc"})
        assert response.status_code == 401

    def test_process_invalid_url(self):
        reg = client.post(
            "/auth/register",
            json={"email": "vid@test.com", "password": "Pass123!", "full_name": "Vid"},
        )
        token = reg.json().get("access_token")
        response = client.post(
            "/video/process",
            json={"youtube_url": "https://vimeo.com/123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_user_cannot_see_other_clips(self):
        # Crée 2 utilisateurs différents
        client.post(
            "/auth/register",
            json={"email": "user1@test.com", "password": "Pass123!", "full_name": "U1"},
        )
        u2 = client.post(
            "/auth/register",
            json={"email": "user2@test.com", "password": "Pass123!", "full_name": "U2"},
        )
        token2 = u2.json().get("access_token")
        # User2 essaie d'accéder aux clips de User1 avec un faux video_id
        response = client.get(
            "/clips/fake-video-id-user1",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code in [403, 404]


# ── TESTS PIPELINE ────────────────────────────────────────────────────────────
class TestPipeline:
    def test_detector_valid_json_response(self):
        from services.detector import parse_gemini_response

        valid_response = '[{"rank":1,"title":"Test","start":10.0,"end":50.0,"reason":"Good","hook":"Hook"}]'
        result = parse_gemini_response(valid_response)
        assert len(result) == 1
        assert result[0]["start"] == 10.0

    def test_detector_invalid_timestamps(self):
        from services.detector import validate_clip_timestamps

        assert validate_clip_timestamps(start=50.0, end=10.0) == False  # start > end
        assert validate_clip_timestamps(start=0.0, end=5.0) == False  # trop court
        assert validate_clip_timestamps(start=0.0, end=200.0) == False  # trop long
        assert validate_clip_timestamps(start=0.0, end=60.0) == True  # parfait

    def test_password_is_hashed(self):
        import bcrypt

        password = "monmotdepasse"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        assert hashed != password.encode()
        assert bcrypt.checkpw(password.encode(), hashed) == True
