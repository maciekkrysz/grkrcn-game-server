
from os import path
from django.conf import settings
from rejson import Client
import json

redis = Client(host=settings.REDIS_HOST,
               port=settings.REDIS_PORT, decode_responses=True)


def redis_list_from_dict(object_name, path_to_dict):
    try:
        dictt = redis.jsonget(object_name, path_to_dict)
        listt = []
        for k, v in dictt.items():
            listt.append({k:v})
        return listt
    except:
        return []

def redis_game_info(object_name, path_to_dict, game_id):
    game = redis.jsonget(object_name, path_to_dict + f'.{game_id}')
    game_info = {}
    game_info['parameters'] = game['game_parameters']
    game_info['game_id'] = game_id
    # game_info['max_players'] = params['max_players']
    # game_info['time_per_player'] = params['time_per_player']
    # game_info['is_ranked'] = params['is_ranked']
    # game_info['cards_on_hand'] = params['cards_on_hand']
    players = []
    for p, value in game['players'].items():
        players.append(value['nickname'])
    game_info['players'] = players
    return game_info

# def redis_get_json(key):
#     return json.loads(redis_inst.get(key).decode('utf-8'))


# def redis_set_json(key, val):
#     return redis_inst.set(key, json.dumps(val))
