import os 
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docqa.settings')

app = Celery('docqa')
app.config_from_object('django.conf:settings', namespace='CELERY')
# namespace='CELERY' means it looks for settings prefixed with
# CELERY_ — so CELERY_BROKER_URL, CELERY_RESULT_BACKEND etc.

app.autodiscover_tasks()
# Scans every app in INSTALLED_APPS for a tasks.py file and
# registers all @shared_task functions automatically.
# This is why you don't manually import tasks anywhere.