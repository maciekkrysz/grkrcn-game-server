from django.db import models


class GameTypeQuerySet(models.QuerySet):
    pass


class GameTypeManager(models.Manager):
    def get_queryset(self):
        return GameTypeQuerySet(self.model, using=self._db)


class GameQuerySet(models.QuerySet):
    def get_before_date(self, date):
        return self.filter(datetime__lt=date)

    def get_after_date(self, date):
        return self.filter(datetime__gt=date)

    def get_gametype_games(self, gametype):
        return self.filter(gametype__type_name__iexact=gametype)


class GameManager(models.Manager):
    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    def get_games_before(self, date):
        return self.get_queryset().get_before_date(date)

    def get_games_after(self, date):
        return self.get_queryset().get_after_date(date)

    def get_gametype_games(self, gametype):
        return self.get_queryset().get_gametype_games(gametype)


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
