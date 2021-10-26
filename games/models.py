from django.db import models

# Create your models here.
class GameType(models.Model):
    type_name = models.CharField(max_length=50)

class Game(models.Model):
    # one card=two symbols; card deck=56 cards
    # chess FEN max length=90 symbols
    start_state = models.CharField(max_length=255)
    game_type=models.ForeignKey(
        GameType,
        on_delete=models.PROTECT,
    )

class Participation(models.Model):
    class ScoreTypes(models.IntegerChoices):
        WIN = 0
        DRAW = 1
        LOSE = 2
        WIN_BY_DISCONNECT = 3
        LOSE_BY_DISCONNECT = 4

    user = models.PositiveIntegerField
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
    )
    score=models.IntegerField(choices=ScoreTypes.choices)

class Move(models.Model):
    participation = models.ForeignKey(
        Participation,
        on_delete=models.CASCADE,
    )
    move = models.CharField(max_length=64)