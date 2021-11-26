from django.db import models
from safedelete.queryset import SafeDeleteQueryset
from safedelete.managers import SafeDeleteManager, DELETED_INVISIBLE
from .resources import normalize_str


class GameTypeQuerySet(SafeDeleteQueryset):
    def get_typegame_lower_nospecial(self, type_name):
        pass


class GameTypeManager(SafeDeleteManager):
    def get_typegame_lower_nospecial(self, type_name):
        for typegame in self.get_queryset():
            print()
            if normalize_str(typegame.type_name).lower() == type_name:
                return typegame
        # return self.get_queryset().get_typegame_lower_nospecial(type_name)


class GameQuerySet(models.QuerySet):
    def get_before_datetime(self, datetime):
        return self.filter(datetime__lt=datetime)

    def get_after_datetime(self, datetime):
        return self.filter(datetime__gt=datetime)

    def get_on_date(self, date):
        return self.filter(datetime__date=date)

    def get_gametype_games(self, gametype):
        return self.filter(game_type__type_name__iexact=gametype)

    def get_by_gameroom_id(self, gameroom_id):
        return self.filter(start_state__game_id=gameroom_id)


class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    def get_games_before(self, datetime):
        return self.get_queryset().get_before_datetime(datetime)

    def get_games_after(self, datetime):
        return self.get_queryset().get_after_datetime(datetime)

    def get_on_date(self, date):
        return self.get_queryset().get_on_date(date)

    def get_gametype_games(self, gametype):
        return self.get_queryset().get_gametype_games(gametype)

    def get_by_gameroom_id(self, gameroom_id):
        return self.get_queryset().get_by_gameroom_id(gameroom_id)


class ParticipationQuerySet(models.QuerySet):
    pass


class ParticipationManager(models.Manager):
    def get_queryset(self):
        return ParticipationQuerySet(self.model, using=self._db)


class MoveQuerySet(models.QuerySet):
    pass


class MoveManager(models.Manager):
    def get_queryset(self):
        return MoveQuerySet(self.model, using=self._db)
