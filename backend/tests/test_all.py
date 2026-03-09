# -*- coding: utf-8 -*-
# Tests automatises complets pour ClipAI

from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import insert_record
from main import app
from services.encryption import encrypt_text
from utils.helpers import new_id, resolve_temp_dir, utc_now_iso

client = TestClient(app)


class TestURLValidation:
    def test_valid_youtube_url_standard(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://youtube.com/watch?v=abc123") is True

    def test_valid_youtube_url_short(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://youtu.be/abc123") is True

    def test_valid_youtube_url_with_params(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://www.youtube.com/watch?v=abc123&t=30s") is True

    def test_valid_youtube_shorts_url(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ?si=abc123") is True

    def test_valid_youtube_mobile_url_without_scheme(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("m.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_invalid_url_vimeo(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("https://vimeo.com/123") is False

    def test_invalid_url_empty(self):
        from utils.validators import validate_youtube_url

        assert validate_youtube_url("") is False

    def test_extract_youtube_id(self):
        from utils.validators import extract_youtube_id

        assert extract_youtube_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


class TestAuthentication:
    def test_register_new_user(self):
        email = f"test_{new_id()[:8]}@clipai.com"
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "Motdepasse123!",
                "full_name": "Test User",
            },
        )
        assert response.status_code in [200, 201]
        assert "access_token" in response.json()

    def test_register_duplicate_email(self):
        email = f"dup_{new_id()[:8]}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Dup"},
        )
        response = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Dup"},
        )
        assert response.status_code == 409

    def test_login_valid(self):
        email = f"login_{new_id()[:8]}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Login"},
        )
        response = client.post("/auth/login", json={"email": email, "password": "Pass123!"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self):
        email = f"wrong_{new_id()[:8]}@test.com"
        client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Wrong"},
        )
        response = client.post("/auth/login", json={"email": email, "password": "mauvaismdp"})
        assert response.status_code == 401

    def test_protected_route_without_token(self):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_protected_route_with_token(self):
        email = f"me_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Me"},
        )
        token = reg.json().get("access_token")
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200


class TestVideo:
    def test_process_without_auth(self):
        response = client.post("/video/process", json={"youtube_url": "https://youtube.com/watch?v=abc"})
        assert response.status_code == 401

    def test_process_invalid_url(self):
        email = f"vid_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Vid"},
        )
        token = reg.json().get("access_token")
        response = client.post(
            "/video/process",
            json={"youtube_url": "https://vimeo.com/123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    def test_process_prompt_mode_requires_prompt(self):
        email = f"prompt_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Prompt"},
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
        email = f"visual_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Visual"},
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

    def test_process_idempotent_same_payload_returns_same_video(self):
        email = f"idem_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Idem"},
        )
        token = reg.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "same-request-1"}
        payload = {
            "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "clip_mode": "talking",
            "max_clips": 4,
            "min_duration": 20,
            "max_duration": 45,
            "target_platform": "shorts",
            "layout": "centered",
        }

        first = client.post("/video/process", json=payload, headers=headers)
        second = client.post("/video/process", json=payload, headers=headers)

        assert first.status_code in [200, 201]
        assert second.status_code in [200, 201]
        assert first.json()["id"] == second.json()["id"]

    def test_user_cannot_see_other_clips(self):
        email1 = f"user1_{new_id()[:8]}@test.com"
        email2 = f"user2_{new_id()[:8]}@test.com"
        client.post(
            "/auth/register",
            json={"email": email1, "password": "Pass123!", "full_name": "U1"},
        )
        u2 = client.post(
            "/auth/register",
            json={"email": email2, "password": "Pass123!", "full_name": "U2"},
        )
        token2 = u2.json().get("access_token")
        response = client.get(
            "/clips/fake-video-id-user1",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code in [403, 404]


class TestPipeline:
    def test_detector_valid_json_response(self):
        from services.detector import parse_gemini_response

        valid_response = '[{"rank":1,"title":"Test","start":10.0,"end":50.0,"reason":"Good","hook":"Hook"}]'
        result = parse_gemini_response(valid_response)
        assert len(result) == 1
        assert result[0]["start"] == 10.0

    def test_detector_invalid_timestamps(self):
        from services.detector import validate_clip_timestamps

        assert validate_clip_timestamps(start=50.0, end=10.0) is False
        assert validate_clip_timestamps(start=0.0, end=5.0) is False
        assert validate_clip_timestamps(start=0.0, end=200.0) is False
        assert validate_clip_timestamps(start=0.0, end=60.0) is True

    def test_password_is_hashed(self):
        import bcrypt

        password = "monmotdepasse"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        assert hashed != password.encode()
        assert bcrypt.checkpw(password.encode(), hashed) is True

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


class TestVirality:
    def test_virality_score_range(self):
        from services.virality_scorer import score_clip_virality

        result = score_clip_virality(
            title="Les 3 erreurs qui ruinent vos ventes",
            hook_text="Tu perds des clients a cause de ces 3 details",
            reason="Conseils concrets et actionnables",
            start=20.0,
            end=62.0,
            total_duration=720.0,
            target_platform="tiktok",
        )
        assert 0.0 <= result["virality_score"] <= 100.0
        assert "hook_text" in result
        assert "best_platform" in result
        assert isinstance(result.get("sub_scores"), dict)

    def test_enrich_highlights_adds_virality(self):
        from services.virality_scorer import enrich_highlights_with_virality

        highlights = [{"title": "Clip 1", "hook": "Hook", "reason": "Reason", "start": 10.0, "end": 45.0}]
        enriched = enrich_highlights_with_virality(highlights, total_duration=120.0, target_platform="all")
        assert len(enriched) == 1
        assert "virality_score" in enriched[0]


class TestRoutesNew:
    def test_download_all_zip(self):
        email = f"zip_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Zip"},
        )
        token = reg.json().get("access_token")
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        user_id = me["id"]

        video_id = new_id()
        now = utc_now_iso()
        insert_record(
            "videos",
            video_id,
            {
                "id": video_id,
                "user_id": user_id,
                "youtube_url": "https://youtube.com/watch?v=testzip",
                "youtube_id": "testzip",
                "title": "Test Zip",
                "duration_seconds": 120,
                "thumbnail_url": "",
                "status": "done",
                "progress_percent": 100,
                "clips_count": 1,
                "created_at": now,
                "updated_at": now,
            },
        )

        published_dir = os.path.join(resolve_temp_dir(), "published", video_id)
        os.makedirs(published_dir, exist_ok=True)
        clip_path = os.path.join(published_dir, "clip1.mp4")
        with open(clip_path, "wb") as file:
            file.write(b"fake_mp4_data")

        clip_id = new_id()
        insert_record(
            "clips",
            clip_id,
            {
                "id": clip_id,
                "video_id": video_id,
                "user_id": user_id,
                "title": "Clip ZIP",
                "start_time": 0.0,
                "end_time": 20.0,
                "duration_seconds": 20.0,
                "file_url": f"http://127.0.0.1:8000/media/published/{video_id}/clip1.mp4",
                "thumbnail_url": "",
                "resolution": "1080x1920",
                "format": "mp4",
                "created_at": now,
            },
        )

        response = client.get(
            f"/clips/{video_id}/download-all",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "application/zip" in response.headers.get("content-type", "")
        assert response.content.startswith(b"PK")

    def test_public_stats_keys(self):
        response = client.get("/stats/public")
        assert response.status_code == 200
        data = response.json()
        for key in ["clips_today", "total_creators", "clips_total", "videos_total", "updated_at"]:
            assert key in data

    def test_pipeline_stats_keys(self):
        email = f"pipe_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Pipe"},
        )
        token = reg.json().get("access_token")
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        user_id = me["id"]

        now = utc_now_iso()
        done_video_id = new_id()
        insert_record(
            "videos",
            done_video_id,
            {
                "id": done_video_id,
                "user_id": user_id,
                "youtube_url": "https://youtube.com/watch?v=p1",
                "youtube_id": "p1",
                "title": "Done",
                "duration_seconds": 100,
                "thumbnail_url": "",
                "status": "done",
                "progress_percent": 100,
                "clips_count": 2,
                "created_at": now,
                "updated_at": now,
            },
        )
        error_video_id = new_id()
        insert_record(
            "videos",
            error_video_id,
            {
                "id": error_video_id,
                "user_id": user_id,
                "youtube_url": "https://youtube.com/watch?v=p2",
                "youtube_id": "p2",
                "title": "Error",
                "duration_seconds": 80,
                "thumbnail_url": "",
                "status": "error",
                "progress_percent": 100,
                "clips_count": 0,
                "created_at": now,
                "updated_at": now,
            },
        )

        response = client.get("/stats/pipeline", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        for key in [
            "total_videos",
            "processing_active",
            "done_count",
            "error_count",
            "success_rate_percent",
            "avg_processing_seconds",
            "status_breakdown",
            "updated_at",
        ]:
            assert key in data
        assert data["done_count"] >= 1
        assert data["error_count"] >= 1

    def test_scheduler_event_created(self):
        email = f"sched_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Sched"},
        )
        token = reg.json().get("access_token")
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        user_id = me["id"]

        video_id = new_id()
        clip_id = new_id()
        now = utc_now_iso()
        insert_record(
            "videos",
            video_id,
            {
                "id": video_id,
                "user_id": user_id,
                "youtube_url": "https://youtube.com/watch?v=schedtest",
                "youtube_id": "schedtest",
                "title": "Sched video",
                "duration_seconds": 100,
                "thumbnail_url": "",
                "status": "done",
                "progress_percent": 100,
                "clips_count": 1,
                "created_at": now,
                "updated_at": now,
            },
        )
        insert_record(
            "clips",
            clip_id,
            {
                "id": clip_id,
                "video_id": video_id,
                "user_id": user_id,
                "title": "Sched clip",
                "start_time": 0.0,
                "end_time": 30.0,
                "duration_seconds": 30.0,
                "file_url": "http://127.0.0.1:8000/media/published/fake.mp4",
                "thumbnail_url": "",
                "resolution": "1080x1920",
                "format": "mp4",
                "created_at": now,
            },
        )

        response = client.post(
            "/scheduler/events",
            json={
                "clip_id": clip_id,
                "platform": "tiktok",
                "scheduled_at": utc_now_iso(),
                "title": "Mon post",
                "description": "Desc",
                "hashtags": ["#clipai"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["event"]["status"] == "scheduled"

    def test_scheduler_publish_due_posts_task(self):
        from services.scheduler_service import create_scheduled_post
        from tasks.video_tasks import publish_scheduled_posts

        user_id = new_id()
        clip_id = new_id()
        account_id = new_id()
        insert_record(
            "social_accounts",
            account_id,
            {
                "id": account_id,
                "user_id": user_id,
                "platform": "tiktok",
                "platform_user_id": "u123",
                "platform_username": "demo",
                "access_token_encrypted": encrypt_text("token-demo", context=f"social:{user_id}:tiktok"),
                "refresh_token_encrypted": None,
                "expires_at": None,
                "is_active": True,
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
            },
        )
        create_scheduled_post(
            user_id=user_id,
            clip_id=clip_id,
            platform="tiktok",
            scheduled_at=utc_now_iso(),
            title="test",
            description="test",
            hashtags=["#x"],
        )

        result = publish_scheduled_posts()
        assert "total" in result
        assert "published" in result


class TestProfileAndNewPages:
    def test_update_profile_and_preferences(self):
        email = f"profile_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Profile User"},
        )
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        updated = client.put(
            "/auth/me",
            json={
                "full_name": "Updated User",
                "bio": "Creator",
                "youtube_url": "https://youtube.com/@clipai",
            },
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["full_name"] == "Updated User"

        prefs = client.put(
            "/auth/preferences",
            json={
                "language": "fr",
                "timezone": "Europe/Paris",
                "preferred_format": "tiktok",
                "preferred_quality": "1080p",
                "subtitles_default": True,
            },
            headers=headers,
        )
        assert prefs.status_code == 200
        assert prefs.json()["preferences"]["preferred_format"] == "tiktok"

    def test_ai_coach_report_endpoint(self):
        email = f"coach_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Coach User"},
        )
        token = reg.json()["access_token"]
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        user_id = me["id"]

        video_id = new_id()
        now = utc_now_iso()
        insert_record(
            "videos",
            video_id,
            {
                "id": video_id,
                "user_id": user_id,
                "youtube_url": "https://youtube.com/watch?v=coachtest",
                "youtube_id": "coachtest",
                "title": "Coach test",
                "duration_seconds": 200,
                "thumbnail_url": "",
                "status": "done",
                "progress_percent": 100,
                "clips_count": 5,
                "created_at": now,
                "updated_at": now,
            },
        )
        for index in range(5):
            clip_id = new_id()
            insert_record(
                "clips",
                clip_id,
                {
                    "id": clip_id,
                    "video_id": video_id,
                    "user_id": user_id,
                    "title": f"Clip {index}",
                    "start_time": float(index * 10),
                    "end_time": float(index * 10 + 30),
                    "duration_seconds": 30.0,
                    "virality_score": 65 + index,
                    "hook_text": f"Hook {index}",
                    "file_url": "http://127.0.0.1:8000/media/published/fake.mp4",
                    "thumbnail_url": "",
                    "resolution": "1080x1920",
                    "format": "mp4",
                    "created_at": now,
                },
            )

        response = client.get("/ai-coach/report", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        payload = response.json()
        assert "report" in payload
        assert "weekly_score" in payload["report"]

    def test_content_hub_endpoint(self):
        email = f"content_{new_id()[:8]}@test.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": "Pass123!", "full_name": "Content User"},
        )
        token = reg.json()["access_token"]
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        user_id = me["id"]

        video_id = new_id()
        now = utc_now_iso()
        insert_record(
            "videos",
            video_id,
            {
                "id": video_id,
                "user_id": user_id,
                "youtube_url": "https://youtube.com/watch?v=contenttest",
                "youtube_id": "contenttest",
                "title": "Content test",
                "duration_seconds": 180,
                "thumbnail_url": "",
                "status": "done",
                "progress_percent": 100,
                "clips_count": 1,
                "created_at": now,
                "updated_at": now,
            },
        )
        clip_id = new_id()
        insert_record(
            "clips",
            clip_id,
            {
                "id": clip_id,
                "video_id": video_id,
                "user_id": user_id,
                "title": "Clip Content",
                "start_time": 0.0,
                "end_time": 30.0,
                "duration_seconds": 30.0,
                "hook_text": "Voici le hook principal",
                "file_url": "http://127.0.0.1:8000/media/published/fake.mp4",
                "thumbnail_url": "",
                "resolution": "1080x1920",
                "format": "mp4",
                "created_at": now,
            },
        )

        response = client.get(
            f"/content-repurpose/{video_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert "content" in payload
        assert "blog" in payload["content"]
