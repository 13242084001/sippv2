from __future__ import absolute_import, unicode_literals
from django.conf import settings
import os
from celery import Celery
from datetime import timedelta
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sippv2.settings')
app = Celery('sippv2')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERYBEAT_SCHEDULE={
        'run-every-1-seconds': {
            'task': 'app01.tasks.taskStatusCheck',
            'schedule': timedelta(seconds=1)
        },
        'run-every-2-seconds': {
            'task': 'app01.tasks.updateTaskStatInfo',
            'schedule': timedelta(seconds=2)
        }
    },
)
