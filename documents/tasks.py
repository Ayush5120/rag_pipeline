# Place at: docqa/documents/tasks.py

from celery import shared_task
from .services.pipeline import process_document as _process


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    # @shared_task: registers this with Celery's task registry.
    # bind=True: gives access to 'self' (the task instance).
    # max_retries=3: Celery will retry up to 3 times on failure.
    try:
        _process(document_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
        # countdown=10: wait 10 seconds before retrying.
        # Handles transient failures like a momentary DB connection blip.
        # After 3 retries the task is marked FAILED in Celery.