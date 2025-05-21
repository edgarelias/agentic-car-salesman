import os
from celery import Celery

# Set default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_chatbot.settings')

# Instantiate Celery
app = Celery('agent_chatbot')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys
#   should be prefixed with 'CELERY_' in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover and load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """
    Simple debug task to check if Celery is working.
    """
    print(f'Request: {self.request!r}')
