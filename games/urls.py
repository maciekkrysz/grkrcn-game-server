from django.urls import path
from . import views


urlpatterns = [
    path('', views.games, name='games'),
    # path('<str:game_name>/<str:room_id>/', views.room, name='room'),
    path('<str:game_name>/info/', views.game_info, name='game_info'),
    path('<str:game_name>/lobby/create/', views.game_create, name='game_create'),
    path('<str:game_name>/lobby/list/', views.game_lobbies, name='game_lobbie'),
    path('<str:game_name>/<str:game_id>/info/', views.lobby_info, name='lobby_info'),
    path('saml/', views.saml_view, name='saml_view'),
    path('metadata/', views.metadata, name='metadata'),
]
