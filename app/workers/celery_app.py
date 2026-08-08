from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("graphrag", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.autodiscover_tasks(["app.workers"])
