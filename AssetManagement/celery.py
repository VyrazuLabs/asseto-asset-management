import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AssetManagement.settings')

app = Celery('AssetManagement')

app.config_from_object('django.conf:settings', namespace='CELERY')
print("getting tasks")
app.autodiscover_tasks()
