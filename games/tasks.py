from __future__ import absolute_import, unicode_literals
from celery import shared_task
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .redis_utils import redis_all_gametypes, redis_all_games_ids
from .classes.games_handler import get_all_chairs, ping_game, \
    try_finish_game_by_undertime, delete_game


@shared_task
def is_alive():
    channel_layer = get_channel_layer()
    for game_type in redis_all_gametypes():
        for id in redis_all_games_ids(game_type):
            ping_game(game_type, id)
            async_to_sync(channel_layer.group_send)(
                f'__game_{game_type}_{id}',
                {
                    'type': 'is_alive_message',
                }
            )
            try_finish_game_by_undertime(game_type, id)


@shared_task
def delete_empty_lobbies():
    for game_type in redis_all_gametypes():
        for id in redis_all_games_ids(game_type):
            try:
                if len(get_all_chairs(game_type, id)) == 0:
                    delete_game(game_type, id)
            except:
                pass
