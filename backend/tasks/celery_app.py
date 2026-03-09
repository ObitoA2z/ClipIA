# -*- coding: utf-8 -*-
"""Configuration Celery (optionnelle, non bloquante en dev local)."""

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "clipai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.video_tasks"],
)

celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])

celery_app.conf.beat_schedule = {
    "publish-scheduled-posts": {
        "task": "tasks.publish_scheduled_posts",
        "schedule": crontab(minute="*/5"),
    },
    "cleanup-temp-files": {
        "task": "tasks.cleanup_temp_files",
        "schedule": crontab(hour="*/2"),
    },
    "track-clip-performance": {
        "task": "tasks.track_performance",
        "schedule": crontab(hour="*/6"),
    },
}
