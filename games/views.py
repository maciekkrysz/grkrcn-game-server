from django.shortcuts import render
from django.http import JsonResponse, Http404
from .models import GameType
from .resources import normalize_str

# Create your views here.


def room(request, room_id):
    return render(request, 'games/room.html', {
        'room_id': room_id
    })


def games(request):
    data = list(GameType.objects.all().values('type_name', 'description'))
    for game in data:
        game['name'] = normalize_str(game['type_name']).lower()
    return JsonResponse(data, safe=False)


def games_info(request, game_name):
    for typegame in list(GameType.objects.all().values('type_name', 'description')):
        if normalize_str(typegame['type_name']).lower() == game_name:
            typegame['name'] = game_name
            return JsonResponse(typegame, safe=False)
    raise Http404("Game does not exist")
