from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from .models import GameType, Game, Participation, Move


class MoveInLine(NestedStackedInline):
    model = Move
    extra = 1


class ParticipationsInLine(NestedStackedInline):
    model = Participation
    extra = 2
    inlines = [MoveInLine]


class GameAdmin(NestedModelAdmin):
    fieldsets = (
        (None, {
            "fields": (
                'game_type', 'start_state'
            ),
        }),
    )
    
    inlines = [ParticipationsInLine]


admin.site.register(GameType)
admin.site.register(Game, GameAdmin)
admin.site.register(Participation)
admin.site.register(Move)
# Register your models here.
