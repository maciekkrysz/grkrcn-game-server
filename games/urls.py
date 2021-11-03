from django.urls import path
from . import views


urlpatterns = [
    path('', views.games, name='games'),
    path('<str:room_id>/', views.room, name='room'),
    path('<str:game_name>/info/', views.games_info, name='games_info')
]
