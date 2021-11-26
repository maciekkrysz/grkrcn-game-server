from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gameserver.settings')
app = Celery('gameserver')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)

app.conf.beat_schedule = {
    'is_alive_func': {
        'task': 'games.tasks.is_alive',
        'schedule': 5,
    },
    'delete_empty_lobbies': {
        'task': 'games.tasks.delete_empty_lobbies',
        'schedule': 60,
    },
}
app.conf.timezone = 'UTC'
