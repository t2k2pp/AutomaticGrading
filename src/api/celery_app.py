"""
Celeryアプリケーション設定
"""
from celery import Celery
from .config import settings

# Celeryアプリケーション作成
celery_app = Celery(
    "pm_scoring",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.api.tasks.scoring_tasks"]
)

# Celery設定
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_routes={
        "src.api.tasks.scoring_tasks.batch_scoring": {"queue": "scoring"},
        "src.api.tasks.scoring_tasks.single_scoring": {"queue": "scoring"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

if __name__ == "__main__":
    celery_app.start()