"""
Celery application configuration.
Workers are launched separately via: celery -A app.tasks.celery_app worker
"""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "logistics_dss",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.optimization_tasks",
        # Phase 4: "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",          # Indian Standard Time
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,             # Requeue if worker crashes mid-task
    worker_prefetch_multiplier=1,    # One task at a time per worker (optimization can be long)
    result_expires=3600,             # Results expire after 1 hour
    task_routes={
        "app.tasks.optimization_tasks.*": {"queue": "optimization"},
        # Phase 4: "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
)

if __name__ == "__main__":
    celery_app.start()
