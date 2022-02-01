import datetime
import json
from unittest.mock import patch
from django.test import TestCase
from django.core import management
from games.classes.game import FINISHED

from games.classes.war import War
from games.classes.makao import Makao
from ..models import GameType, Game
from ..ranking import calculate_elo
from ..classes.games_handler import create_game, current_username, delete_game, \
    disconnect_from_game, game_self_info, get_all_chairs, get_all_players, try_finish_game_by_undertime, \
    get_class, connect_to_game, get_finish_score, is_game_ongoing, make_move, mark_active, \
    mark_ready, ping_game, possible_moves, start_game, start_game_possible, surrender
from ..redis_utils import redis, redis_all_games_ids, redis_all_gametypes, redis_list_from_dict
from .consts import SURRENDER, WAR, MAKAO, WAR_BASE_CONFIG, GAMES_CONFIG_PATH

# Create your tests here.


class GameTypeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command('flush', '--noinput')
        cls.gametype = GameType.objects.create(
            type_name='Wąr',
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

    def test_get_typegame_lower_nospecial(self):
        self.assertEqual(
            GameType.objects.get_typegame_lower_nospecial('war'), self.gametype)


class GameModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        management.call_command('flush', '--noinput')
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


class RankingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rank1 = 1100
        cls.rank2 = 1300
        cls.rank3 = 1400
        cls.rank4 = 1000

    def test_ranking(self):
        p_rank = self.rank1
        opponents = [self.rank2, self.rank3, self.rank4]
        score = 3
        k = 12
        self.assertEqual(int(calculate_elo(p_rank, opponents, score, k)), 1123)

    def test_ranking(self):
        p_rank = self.rank1
        opponents = [self.rank2]
        score = 1
        k = 10
        self.assertEqual(int(calculate_elo(p_rank, opponents, score, k)), 1107)
        score = 0
        self.assertEqual(int(calculate_elo(p_rank, opponents, score, k)), 1097)


class CreateGameTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_config = WAR_BASE_CONFIG
        cls.game = WAR

        cls.config_path = GAMES_CONFIG_PATH + WAR + '.json'
        with open(cls.config_path) as file:
            cls.game_config = json.load(file)

    @classmethod
    def seconds_from_mm_ss(cls, mm_ss):
        mm, ss = mm_ss.split(':')
        return int(mm)*60 + int(ss)

    def test_create_game(self):
        id = create_game(self.game, self.user_config)
        self.assertIsNotNone(id)

    def test_create_game_minimum_int(self):
        self.user_config['game_parameters']['max_players'] = self.game_config['max_players']['min']
        id = create_game(self.game, self.user_config)
        self.assertIsNotNone(id)

    def test_create_game_maximum_int(self):
        self.user_config['game_parameters']['max_players'] = self.game_config['max_players']['max']
        id = create_game(self.game, self.user_config)
        self.assertIsNotNone(id)

    def test_create_game_minimum_time(self):
        seconds = self.seconds_from_mm_ss(
            self.game_config['time_per_player']['min'])
        self.user_config['game_parameters']['time_per_player'] = seconds
        id = create_game(self.game, self.user_config)
        self.assertIsNotNone(id)

    def test_create_game_maximum_time(self):
        seconds = self.seconds_from_mm_ss(
            self.game_config['time_per_player']['max'])
        self.user_config['game_parameters']['time_per_player'] = seconds
        id = create_game(self.game, self.user_config)
        self.assertIsNotNone(id)

    def test_create_game_exceed_maximum_int(self):
        self.user_config['game_parameters']['max_players'] = self.game_config['max_players']['max'] + 1
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_exceed_minimum_int(self):
        self.user_config['game_parameters']['max_players'] = self.game_config['max_players']['min'] - 1
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_exceed_maximum_time(self):
        seconds = self.seconds_from_mm_ss(
            self.game_config['time_per_player']['max'])
        self.user_config['game_parameters']['time_per_player'] = seconds + 1
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_exceed_maximum_time(self):
        seconds = self.seconds_from_mm_ss(
            self.game_config['time_per_player']['min'])
        self.user_config['game_parameters']['time_per_player'] = seconds - 1
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_no_int(self):
        self.user_config['game_parameters']['cards_on_hand'] = 'other'
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_no_time(self):
        self.user_config['game_parameters']['time_per_player'] = 'other'
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_none_value(self):
        self.user_config['game_parameters']['cards_on_hand'] = None
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    def test_create_game_no_value(self):
        self.user_config['game_parameters'] = {
            'time_per_player': 120,
            'max_players': 2,
            'rounds': 1,
            'is_ranked': True,
            # no cards_on_hand
        }
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    @patch('games.classes.game.redis.jsontype', side_effect=[True, False])
    def test_create_game_with_same_id(self, id):
        create_game(self.game, self.user_config)

    @patch('games.classes.game.Game.get_config_json', side_effect=[
        {
            'time_per_player': {
                'type': 'non_existing_type',
                'min': '0:15',
                'max': '60:00'
            }
        }
    ])
    def test_create_game_non_existing_type(self, id):
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)

    @patch('games.classes.game.Game.check_create_game', False)
    def test_create_game_non_existing_type(self):
        with self.assertRaises(Exception) as context:
            create_game(self.game, self.user_config)


class GameDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_config = WAR_BASE_CONFIG
        cls.game = WAR

    def setUp(self):
        self.game_id = create_game(self.game, self.user_config)

    def test_delete_game(self):
        self.assertTrue(redis.jsonget('games', f'.{self.game}.{self.game_id}'))
        delete_game(self.game, self.game_id)
        with self.assertRaises(Exception) as context:
            redis.jsonget('games', f'.{self.game}.{self.game_id}')


class GetClassTests(TestCase):
    def test_get_class_makao(self):
        self.assertEqual(get_class(MAKAO), Makao)

    def test_get_class_war(self):
        self.assertEqual(get_class(WAR), War)

    def test_get_class_other(self):
        with self.assertRaises(Exception) as context:
            get_class('other')


class GameOperationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gametype = GameType.objects.create(
            type_name=WAR,
        )
        cls.user_config = WAR_BASE_CONFIG
        cls.game = WAR
        cls.user1 = 'user1'
        cls.user2 = 'user2'
        cls.user1_data = {
            'nickname': cls.user1,
            'ranking': 1000,
            'id': 1
        }
        cls.user2_data = {
            'nickname': cls.user2,
            'ranking': 1100,
            'id': 2
        }

    def setUp(self):
        self.game_id = create_game(self.game, self.user_config)

    def tearDown(self):
        delete_game(self.game, self.game_id)

    def test_get_all_players(self):
        connect_to_game(WAR, self.game_id, self.user1_data)
        players = get_all_players(WAR, self.game_id)
        self.assertTrue(self.user1 in players)

        connect_to_game(WAR, self.game_id, self.user2_data)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        players = get_all_players(WAR, self.game_id)
        self.assertTrue(self.user1 in players)
        self.assertTrue(self.user2 in players)

        if start_game_possible(WAR, self.game_id):
            start_game(WAR, self.game_id)

        players = get_all_players(WAR, self.game_id)
        self.assertTrue(self.user1 in players)
        self.assertTrue(self.user2 in players)

        surrender(WAR, self.game_id, self.user1)
        self.assertTrue(self.user1 in players)
        self.assertTrue(self.user2 in players)

        disconnect_from_game(WAR, self.game_id, self.user1)
        players = get_all_players(WAR, self.game_id)
        self.assertTrue(self.user2 in players)

    def test_get_all_chairs(self):
        connect_to_game(WAR, self.game_id, self.user1_data)
        chairs = get_all_chairs(WAR, self.game_id)
        self.assertTrue('p1' in chairs)

        connect_to_game(WAR, self.game_id, self.user2_data)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        players = get_all_chairs(WAR, self.game_id)
        self.assertTrue('p1' in players)
        self.assertTrue('p2' in players)

    @patch('games.classes.games_handler.send_scores_to_rabbitmq')
    def test_game_surrender(self, rabbitmq):
        connect_to_game(WAR, self.game_id, self.user1_data)
        connect_to_game(WAR, self.game_id, self.user2_data)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        if start_game_possible(WAR, self.game_id):
            start_game(WAR, self.game_id)

        surrender(WAR, self.game_id, self.user1)

        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(game_info['status'], FINISHED)
        self.assertEqual(game_info['surrender'], True)
        self.assertTrue(self.user1 in game_info['scores']['lose'])
        self.assertTrue(self.user2 in game_info['scores']['win'])

        scores = get_finish_score(WAR, self.game_id)
        self.assertEqual(scores['reason'], SURRENDER)

    def test_pings_game_waiting(self):
        connect_to_game(WAR, self.game_id, self.user1_data)
        connect_to_game(WAR, self.game_id, self.user2_data)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        ping_game(WAR, self.game_id)
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(game_info['players']['p1']['inactive_pings'], 1)
        self.assertEqual(game_info['players']['p2']['inactive_pings'], 1)

        ping_game(WAR, self.game_id)
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(game_info['players']['p1']['inactive_pings'], 2)
        self.assertEqual(game_info['players']['p2']['inactive_pings'], 2)

        mark_active(WAR, self.game_id, self.user1, True)
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(game_info['players']['p1']['inactive_pings'], 0)
        self.assertEqual(game_info['players']['p2']['inactive_pings'], 2)

        ping_game(WAR, self.game_id)
        ping_game(WAR, self.game_id)
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(game_info['players']['p1']['inactive_pings'], 2)
        self.assertEqual(game_info['players']['p2']['inactive_pings'], 4)

        ping_game(WAR, self.game_id)
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(len(game_info['players']), 1)

    def test_try_finish_undertime(self):
        connect_to_game(WAR, self.game_id, self.user1_data)
        connect_to_game(WAR, self.game_id, self.user2_data)
        try_finish_game_by_undertime(WAR, self.game_id)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        try_finish_game_by_undertime(WAR, self.game_id)

    def test_game(self):
        connect_to_game(WAR, self.game_id, self.user1_data)
        connect_to_game(WAR, self.game_id, self.user2_data)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        if start_game_possible(WAR, self.game_id):
            start_game(WAR, self.game_id)

        while(is_game_ongoing(WAR, self.game_id)):
            user = current_username(WAR, self.game_id)
            moves = possible_moves(WAR, self.game_id, user)
            action = moves['possible_actions'][0]
            move = None
            if action == 'throw':
                move = moves['possible_moves'][0]

            make_move(WAR, self.game_id, user, action, move)

        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')

        chair_u1 = game_self_info(WAR, self.game_id, self.user1)['chair']
        chair_u2 = game_self_info(WAR, self.game_id, self.user2)['chair']
        points_u1 = game_info['players'][chair_u1]['points']
        points_u2 = game_info['players'][chair_u2]['points']

        if points_u1 > points_u2:
            self.assertTrue(self.user1 in game_info['scores']['win'])
            self.assertTrue(self.user2 in game_info['scores']['lose'])
            self.assertFalse(game_info['is_draw'])
        elif points_u2 > points_u1:
            self.assertTrue(self.user2 in game_info['scores']['win'])
            self.assertTrue(self.user1 in game_info['scores']['lose'])
            self.assertFalse(game_info['is_draw'])
        else:
            self.assertEqual(len(game_info['scores']['lose']), 0)
            self.assertEqual(len(game_info['scores']['win']), 0)
            self.assertTrue(game_info['is_draw'])

        self.assertEqual(len(game_info['stack_draw']), 0)
        self.assertEqual(game_info['status'], FINISHED)

    def test_update_rankings(self):
        connect_to_game(WAR, self.game_id, self.user1_data)
        connect_to_game(WAR, self.game_id, self.user2_data)
        mark_ready(WAR, self.game_id, self.user1, True)
        mark_ready(WAR, self.game_id, self.user2, True)

        if start_game_possible(WAR, self.game_id):
            start_game(WAR, self.game_id)
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')

        p1_ranking = game_info['players']['p1']['ranking']
        p2_ranking = game_info['players']['p2']['ranking']

        War.update_rankings(self.game_id, {
            'players': {
                1: {
                    'points': 10,
                },
                2: {
                    'points': -10,
                }
            }
        })
        game_info = redis.jsonget('games', f'.{WAR}.{self.game_id}')
        self.assertEqual(
            p1_ranking + 10, game_info['players']['p1']['ranking'])
        self.assertEqual(
            p2_ranking - 10, game_info['players']['p2']['ranking'])


class RedisUtilsTests(TestCase):
    def test_game_games_ids(self):
        game_id = create_game(WAR, WAR_BASE_CONFIG)
        self.assertNotEquals(redis_all_games_ids(WAR), [])
        delete_game(WAR, game_id)

    @patch('games.classes.game.redis.jsonget', side_effect=Exception())
    def test_game_games_ids_exception(self, jsonget):
        self.assertEquals(redis_all_games_ids(WAR), [])

    def test_all_game_types_exception(self, jsonget):
        self.assertNotEquals(redis_all_gametypes(WAR), [])

    @patch('games.classes.game.redis.jsonget', side_effect=Exception())
    def test_all_game_types_exception(self, jsonget):
        self.assertEquals(redis_all_gametypes(WAR), [])

    @patch('games.classes.game.redis.jsonget', side_effect=Exception())
    def test_redis_list_from_dict_exception(self, jsonget):
        self.assertEquals(redis_list_from_dict('smth', 'smth'), [])
