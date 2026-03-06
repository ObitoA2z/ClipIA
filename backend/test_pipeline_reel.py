# -*- coding: utf-8 -*-
# Test du pipeline complet avec une vraie video YouTube courte

import sys
import time
import requests

BASE_URL = "http://localhost:8000"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=ysz5S6PUM-U"


def fail(message: str) -> None:
    print(f"\n[ERROR] {message}")
    sys.exit(1)


print("\n=== TEST PIPELINE CLIPAI ===\n")

print("1) Creation compte de test...")
register = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "test_pipeline@clipai.com",
        "password": "TestPipeline123!",
        "full_name": "Test Pipeline",
    },
    timeout=30,
)

if register.status_code in [200, 201]:
    token = register.json().get("access_token")
    if not token:
        fail("Token absent dans la reponse register")
    print("   [OK] Compte cree - Token obtenu")
elif register.status_code == 409:
    login = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "test_pipeline@clipai.com", "password": "TestPipeline123!"},
        timeout=30,
    )
    if login.status_code != 200:
        fail(f"Login impossible: {login.status_code} - {login.text}")
    token = login.json().get("access_token")
    if not token:
        fail("Token absent dans la reponse login")
    print("   [OK] Connecte avec compte existant")
else:
    fail(f"Erreur register: {register.status_code} - {register.text}")

headers = {"Authorization": f"Bearer {token}"}

print("\n2) Envoi de la video YouTube...")
print(f"   URL : {TEST_VIDEO_URL}")

process = requests.post(
    f"{BASE_URL}/video/process",
    json={"youtube_url": TEST_VIDEO_URL},
    headers=headers,
    timeout=60,
)

if process.status_code not in [200, 201]:
    fail(f"Erreur process: {process.status_code} - {process.text}")

video_id = process.json().get("id")
if not video_id:
    fail("Video ID absent dans la reponse /video/process")
print(f"   [OK] Traitement lance - Video ID : {video_id}")

print("\n3) Suivi de la progression...")
max_wait = 600
elapsed = 0
last_status = ""

while elapsed < max_wait:
    status_resp = requests.get(f"{BASE_URL}/video/{video_id}/status", headers=headers, timeout=30)
    if status_resp.status_code == 200:
        data = status_resp.json()
        status = data.get("status", "unknown")
        progress = data.get("progress_percent", 0)

        if status != last_status:
            print(f"   [{elapsed:3d}s] {progress:3d}% - {status}")
            last_status = status

        if status == "done":
            print(f"\n   [OK] TRAITEMENT TERMINE en {elapsed} secondes !")
            break
        if status == "error":
            fail(data.get("error_message", "Erreur inconnue"))

    time.sleep(5)
    elapsed += 5
else:
    fail(f"Timeout apres {max_wait} secondes")

print("\n4) Recuperation des clips...")
clips_resp = requests.get(f"{BASE_URL}/clips/{video_id}", headers=headers, timeout=30)
if clips_resp.status_code != 200:
    fail(f"Erreur recuperation clips: {clips_resp.status_code} - {clips_resp.text}")

clips = clips_resp.json()
print(f"   [OK] {len(clips)} clips generes !\n")
for i, clip in enumerate(clips, 1):
    print(f"   Clip {i} : {clip.get('title', 'Sans titre')}")
    print(f"           Duree : {float(clip.get('duration_seconds', 0.0)):.1f}s")
    print(f"           URL   : {clip.get('file_url', '')}")
    print()

print("===============================")
print("[OK] TEST PIPELINE COMPLET - SUCCES")
print("===============================\n")
