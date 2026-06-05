from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "alert_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.workers.tasks"],
)

celery_app.conf.beat_schedule = {
    "fetch-and-dispatch-every-5-minutes": {
        "task": "src.workers.tasks.fetch_and_dispatch",
        "schedule": 300.0,
    }
}
celery_app.conf.timezone = "UTC"
