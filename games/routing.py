from django.urls import re_path
from django.urls import path
from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    path('ws/<type_game>/<room_id>/', consumers.GameConsumer.as_asgi()),
]