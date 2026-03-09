# -*- coding: utf-8 -*-
# Tests automatisÃ©s complets pour ClipAI

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


# â”€â”€ TESTS VALIDATION URL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ TESTS AUTHENTIFICATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ TESTS VIDÃ‰O â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    def test_process_prompt_mode_requires_prompt(self):
        reg = client.post(
            "/auth/register",
            json={"email": "prompt@test.com", "password": "Pass123!", "full_name": "Prompt"},
        )
        token = reg.json().get("access_token")
        response = client.post(
            "/video/process",
            json={
                "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "clip_mode": "prompt",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_process_visual_mode_is_accepted(self):
        reg = client.post(
            "/auth/register",
            json={"email": "visual@test.com", "password": "Pass123!", "full_name": "Visual"},
        )
        token = reg.json().get("access_token")
        response = client.post(
            "/video/process",
            json={
                "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "clip_mode": "visual",
                "max_clips": 5,
                "min_duration": 20,
                "max_duration": 60,
                "target_platform": "tiktok",
                "layout": "split",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [200, 201]
        assert "id" in response.json()

    def test_user_cannot_see_other_clips(self):
        # CrÃ©e 2 utilisateurs diffÃ©rents
        client.post(
            "/auth/register",
            json={"email": "user1@test.com", "password": "Pass123!", "full_name": "U1"},
        )
        u2 = client.post(
            "/auth/register",
            json={"email": "user2@test.com", "password": "Pass123!", "full_name": "U2"},
        )
        token2 = u2.json().get("access_token")
        # User2 essaie d'accÃ©der aux clips de User1 avec un faux video_id
        response = client.get(
            "/clips/fake-video-id-user1",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code in [403, 404]


# â”€â”€ TESTS PIPELINE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    def test_detector_prompt_mode_local_matching(self):
        from services.detector import detect_highlights

        transcript = {
            "duration_seconds": 180,
            "segments": [
                {"start": 0.0, "end": 15.0, "text": "Introduction generale"},
                {"start": 15.0, "end": 40.0, "text": "Conseils de vente concrets pour independants"},
                {"start": 40.0, "end": 70.0, "text": "Etude de cas marketing"},
            ],
        }
        result = detect_highlights(
            transcript,
            clip_mode="prompt",
            user_prompt="vente",
            max_clips=3,
            min_duration=20,
            max_duration=60,
        )
        assert len(result) >= 1
        assert any("vente" in item["reason"].lower() or "vente" in item["hook"].lower() for item in result)

    def test_detector_visual_mode_fallback_without_video_path(self):
        from services.detector import detect_highlights

        transcript = {
            "duration_seconds": 120,
            "segments": [{"start": 0.0, "end": 35.0, "text": "Segment 1"}, {"start": 36.0, "end": 80.0, "text": "Segment 2"}],
        }
        result = detect_highlights(transcript, clip_mode="visual", video_path="", max_clips=2)
        assert len(result) >= 1

    def test_detector_energy_mode_fallback_without_audio_path(self):
        from services.detector import detect_highlights

        transcript = {
            "duration_seconds": 120,
            "segments": [{"start": 0.0, "end": 35.0, "text": "Segment 1"}, {"start": 36.0, "end": 80.0, "text": "Segment 2"}],
        }
        result = detect_highlights(transcript, clip_mode="energy", audio_path="", max_clips=2)
        assert len(result) >= 1
