# -*- coding: utf-8 -*-
"""Tâches Celery de démonstration."""

from tasks.celery_app import celery_app


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return "pong"
