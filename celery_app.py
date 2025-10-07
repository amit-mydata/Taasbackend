from celery import Celery
import subprocess
import sys
import os

from app.core.config import settings

REDIS_URL = settings.REDIS_URL

celery_app = Celery(
    "worker",
    broker=REDIS_URL,  # Redis broker
    # backend="redis://localhost:6379/1"  # Optional: for result storage
)

celery_app.conf.task_routes = {
    "tasks.process_job_task": {"queue": "questions"}
}
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

if __name__ == "__main__":
    cmd = [
        sys.executable, 
        "-m", "celery",
        "-A", "tasks.celery_app",  
        "worker",
        "--loglevel=info",
        "-Q", "questions",
        "-c", "2"
    ]
    subprocess.run(cmd)

## Not Defined thread: # celery -A tasks.celery_app worker --loglevel=info -Q questions 
## Defined thread:     # celery -A tasks.celery_app worker --loglevel=info -Q questions -c 2