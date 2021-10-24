from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse



def room(request, room_id):
    return render(request, 'games/room.html', {
        'room_id': room_id
    })

def games(request):
    return HttpResponse()