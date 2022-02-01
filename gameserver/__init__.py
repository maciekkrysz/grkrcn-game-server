from __future__ import absolute_import, unicode_literals


import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameserver.settings")
django.setup()

from .celery import app as celery_app
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
