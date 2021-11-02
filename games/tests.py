import datetime
from django.test import TestCase
from .models import GameType, Game, Participation, Move


# Create your tests here.
class GameTypeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gametype = GameType.objects.create(
            type_name='makao',
        )
        cls.game1 = Game.objects.create(
            game_type=cls.gametype,
            start_state='no_matter'
        )
        cls.game2 = Game.objects.create(
            game_type=cls.gametype,
            start_state=''
        )

    def test_safedelete_gametype(self):
        self.assertEqual(GameType.objects.count(), 1)
        self.assertEqual(Game.objects.count(), 2)
        self.gametype.delete()
        self.assertEqual(GameType.objects.count(), 0)
        self.assertEqual(Game.objects.count(), 2)


class GameModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.makao = GameType.objects.create(
            type_name='makao'
        )
        cls.war = GameType.objects.create(
            type_name='war'
        )
        cls.game1 = Game.objects.create(
            game_type=cls.makao,
            start_state='no_matter'
        )
        cls.game2 = Game.objects.create(
            game_type=cls.makao,
            start_state=''
        )
        cls.game3 = Game.objects.create(
            game_type=cls.war,
            start_state=''
        )

    def test_datetime_default_sort(self):
        self.assertEqual(
            list(Game.objects.all().values_list('pk', flat=True)), [3, 2, 1])

    def test_manager_after_date(self):
        self.assertEqual(
            sorted(list(Game.objects.get_games_after(self.game1.datetime).values_list('pk', flat=True))), [2, 3])
        self.assertEqual(
            sorted(list(Game.objects.get_games_after(self.game2.datetime).values_list('pk', flat=True))), [3])

    def test_manager_before_date(self):
        self.assertEqual(
            sorted(list(Game.objects.get_games_before(self.game3.datetime).values_list('pk', flat=True))), [1, 2])
        self.assertEqual(
            sorted(list(Game.objects.get_games_before(self.game2.datetime).values_list('pk', flat=True))), [1])

    def test_manager_on_date(self):
        today = datetime.date.today()
        self.assertEqual(Game.objects.get_on_date(today).count(), 3)

    def test_manager_gametype_games(self):
        self.assertEqual(Game.objects.get_gametype_games(
            self.makao.type_name).count(), 2)
        self.assertEqual(Game.objects.get_gametype_games(
            self.war.type_name).count(), 1)
