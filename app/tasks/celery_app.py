from celery import Celery
from app.config import settings

celery_app = Celery(
    "landslide_ews",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.risk_tasks",
        "app.tasks.alert_tasks",
        "app.tasks.monitoring_tasks",   # continuous monitoring
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.risk_tasks.*":       {"queue": "risk"},
        "app.tasks.alert_tasks.*":      {"queue": "alerts"},
        "app.tasks.monitoring_tasks.*": {"queue": "monitoring"},
    },
    # Celery beat schedule — runs the monitoring pass every N minutes.
    # MONITORING_INTERVAL_MINUTES is read at import time; restart beat if changed.
    beat_schedule={
        "continuous-zone-monitoring": {
            "task": "monitoring_tasks.recompute_tracked_zones",
            "schedule": settings.MONITORING_INTERVAL_MINUTES * 60,
        },
    },
)