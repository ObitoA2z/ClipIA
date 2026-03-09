# -*- coding: utf-8 -*-
"""Upload clips vers Cloudflare R2 avec fallback local /media."""

from __future__ import annotations

import os
import shutil
from urllib.parse import quote

import boto3

from utils.helpers import ffmpeg_binary, probe_duration_seconds, resolve_temp_dir, run_subprocess


def _relative_media_path(file_path: str) -> str:
    """Calcule le chemin relatif du media pour construire une URL locale."""
    media_root = resolve_temp_dir()
    rel = os.path.relpath(file_path, media_root)
    return rel.replace("\\", "/")


def _make_thumbnail(clip_path: str, index: int) -> str:
    """Genere une miniature JPG au milieu du clip."""
    duration = probe_duration_seconds(clip_path)
    midpoint = max(0.1, duration / 2) if duration > 0 else 0.5

    thumb_path = os.path.join(os.path.dirname(clip_path), f"thumb_{index}.jpg")
    command = [
        ffmpeg_binary(),
        "-y",
        "-ss",
        f"{midpoint:.3f}",
        "-i",
        clip_path,
        "-frames:v",
        "1",
        thumb_path,
    ]
    run_subprocess(command, timeout=120)
    return thumb_path


def _is_r2_configured() -> bool:
    """Verifie si les variables minimales R2 sont presentes."""
    required_env = [
        "CLOUDFLARE_R2_ACCESS_KEY",
        "CLOUDFLARE_R2_SECRET_KEY",
        "CLOUDFLARE_R2_BUCKET",
        "CLOUDFLARE_R2_ENDPOINT",
    ]
    return all(os.getenv(name, "").strip() for name in required_env)


def _build_r2_client():
    """Construit un client S3 pour Cloudflare R2."""
    endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT", "").strip()
    access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY", "").strip()
    secret_key = os.getenv("CLOUDFLARE_R2_SECRET_KEY", "").strip()
    region = os.getenv("CLOUDFLARE_R2_REGION", "auto").strip() or "auto"

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )


def _content_type_for_path(path: str) -> str:
    """Retourne le content-type adapte au fichier."""
    lowered = path.lower()
    if lowered.endswith(".mp4"):
        return "video/mp4"
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
        return "image/jpeg"
    if lowered.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


def _r2_object_key(video_id: str, filename: str) -> str:
    """Construit une cle d'objet stable dans le bucket R2."""
    safe_filename = filename.replace(" ", "_")
    return f"clips/{video_id}/{safe_filename}"


def _r2_public_url(client, bucket: str, object_key: str) -> str:
    """Construit une URL de lecture pour un objet R2."""
    public_base = os.getenv("CLOUDFLARE_R2_PUBLIC_BASE_URL", "").strip().rstrip("/")
    encoded_key = quote(object_key, safe="/")

    if public_base:
        return f"{public_base}/{encoded_key}"

    expiry = int(os.getenv("R2_PRESIGNED_EXPIRES_SECONDS", "604800") or 604800)
    expiry = max(60, expiry)
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expiry,
    )


def _upload_file_to_r2(client, bucket: str, local_path: str, object_key: str) -> str:
    """Upload un fichier local vers R2 puis renvoie son URL de lecture."""
    extra_args = {"ContentType": _content_type_for_path(local_path)}
    with open(local_path, "rb") as file_obj:
        client.upload_fileobj(file_obj, bucket, object_key, ExtraArgs=extra_args)
    return _r2_public_url(client, bucket, object_key)


def _local_media_url(file_path: str) -> str:
    """Construit l'URL locale d'un media servi par FastAPI (/media)."""
    backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")
    return f"{backend_public_url}/media/{_relative_media_path(file_path)}"


def _publish_local_file(video_id: str, local_path: str) -> str:
    """Copie un fichier genere vers un dossier media persistant hors workdir."""
    published_dir = os.path.join(resolve_temp_dir(), "published", video_id)
    os.makedirs(published_dir, exist_ok=True)
    destination = os.path.join(published_dir, os.path.basename(local_path))
    shutil.copy2(local_path, destination)
    return destination


def _upload_mode():
    """Determine le mode d'upload (R2 ou local fallback)."""
    if not _is_r2_configured():
        return {"mode": "local", "client": None, "bucket": ""}

    try:
        client = _build_r2_client()
        bucket = os.getenv("CLOUDFLARE_R2_BUCKET", "").strip()
        return {"mode": "r2", "client": client, "bucket": bucket}
    except Exception:
        return {"mode": "local", "client": None, "bucket": ""}


def upload_clips(video_id: str, clips: list[dict]) -> list[dict]:
    """Upload les clips sur R2 si possible, sinon conserve le mode local."""
    try:
        mode_info = _upload_mode()
        uploaded: list[dict] = []

        for index, clip in enumerate(clips, start=1):
            clip_path = clip["path"]
            meta = clip["meta"]

            try:
                thumbnail_path = _make_thumbnail(clip_path, index=index)
            except Exception:
                thumbnail_path = ""

            if mode_info["mode"] == "r2":
                client = mode_info["client"]
                bucket = mode_info["bucket"]
                clip_key = _r2_object_key(video_id, os.path.basename(clip_path))
                file_url = _upload_file_to_r2(client, bucket, clip_path, clip_key)

                if thumbnail_path:
                    thumb_key = _r2_object_key(video_id, os.path.basename(thumbnail_path))
                    thumbnail_url = _upload_file_to_r2(client, bucket, thumbnail_path, thumb_key)
                else:
                    thumbnail_url = ""
            else:
                published_clip = _publish_local_file(video_id, clip_path)
                file_url = _local_media_url(published_clip)

                if thumbnail_path:
                    published_thumb = _publish_local_file(video_id, thumbnail_path)
                    thumbnail_url = _local_media_url(published_thumb)
                else:
                    thumbnail_url = ""

            start = float(meta.get("start", 0.0))
            end = float(meta.get("end", start))

            uploaded.append(
                {
                    "title": meta.get("title") or f"Clip {index}",
                    "start_time": round(start, 3),
                    "end_time": round(end, 3),
                    "duration_seconds": round(max(0.0, end - start), 3),
                    "virality_score": meta.get("virality_score"),
                    "hook_text": meta.get("hook_text") or meta.get("hook"),
                    "improvement_tip": meta.get("improvement_tip"),
                    "best_platform": meta.get("best_platform"),
                    "file_url": file_url,
                    "thumbnail_url": thumbnail_url,
                    "resolution": "1080x1920",
                    "format": "mp4",
                    "video_id": video_id,
                    "storage": mode_info["mode"],
                }
            )

        if not uploaded:
            raise RuntimeError("No clips uploaded")

        return uploaded
    except Exception as exc:
        raise RuntimeError(f"upload_clips failed: {exc}") from exc
