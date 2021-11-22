from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from .classes.games_handler import create_game
from .models import GameType
from .resources import normalize_str
from .redis_utils import redis, redis_list_from_dict
import json
from django.views.decorators.csrf import ensure_csrf_cookie
# Create your views here.


# def room(request, game_name, room_id):
#     return render(request, 'games/room.html', {
#         'room_id': room_id,
#         'game_name': game_name
#     })


def games(request):
    data = list(GameType.objects.all().values('type_name', 'description'))
    for game in data:
        game['name'] = normalize_str(game['type_name']).lower()
    return JsonResponse(data, safe=False)


<<<<<<< HEAD
def game_lobby(request, game_name):
    games = redis_list_from_dict('games', f'.{game_name}')
    # games.extend(redis_list_from_dict('ongoing_games', f'.{game_name}'))
=======
def games_lobby(request, game_name):
    games = redis_list_from_dict('available_games', f'.{game_name}')
    games.extend(redis_list_from_dict('ongoing_games', f'.{game_name}'))
>>>>>>> 2a2128e5dfa0e2024c8b104664601bf28588518b
    games_to_send = []
    for game in games:
        k, v = game.popitem()
        v['game_id'] = k
        games_to_send.append(v)
    return JsonResponse({'lobbies': games_to_send})
    pass

def game_lobby(request, game_name, game_id):
    pass

def game_info(request, game_name):
    for typegame in list(GameType.objects.all().values('type_name', 'description')):
        if normalize_str(typegame['type_name']).lower() == game_name:
            typegame['name'] = game_name
            return JsonResponse(typegame, safe=False)
    return HttpResponseNotFound("Game does not exist")


@ensure_csrf_cookie
def game_create(request, game_name):
    if request.method == 'GET':
        try:
            with open(f'games/games_configs/{game_name}.json') as json_file:
                data = json.load(json_file)
            return JsonResponse(data)
        except:
            return HttpResponseNotFound("Game does not exist")
    elif request.method == 'POST':
        # CREATE GAME
        try:
            game_id = create_game(game_name, json.loads(request.body))
            return JsonResponse({'game_id': game_id})
        except:
            return HttpResponseBadRequest("Cannot create game")
    return JsonResponse({})
