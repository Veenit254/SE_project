# backend/celery_worker.py
from app.ingestion.tasks import celery

if __name__ == "__main__":
    celery.start()