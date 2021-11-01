from django.contrib import admin
from .models import GameType, Game, Participation, Move

admin.site.register(GameType)
admin.site.register(Game)
admin.site.register(Participation)
admin.site.register(Move)
# Register your models here.
