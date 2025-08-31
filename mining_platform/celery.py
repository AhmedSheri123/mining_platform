import os
from celery import Celery
from celery.schedules import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mining_platform.settings')

app = Celery('mining_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# الجدولة لكل 5 ثواني
app.conf.beat_schedule = {
    'update-every-5-seconds': {
        'task': 'devices.tasks.update_device_earnings',
        'schedule': 2.0,  # 5 ثواني
    },
}
