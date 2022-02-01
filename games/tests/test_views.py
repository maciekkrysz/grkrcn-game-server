import json
from xml.etree.ElementTree import XML, Element
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse, request
from django.test import TestCase
from django.core import management

from ..models import GameType, Game
from ..redis_utils import redis_all_games_ids
from ..views import game_info, game_lobbies, games, game_create, lobby_info, metadata, saml_view
from ..classes.games_handler import connect_to_game, delete_game
from .consts import WAR, WAR_BASE_CONFIG


class GameTypeModelTests(TestCase):
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

    def test_games_view(self):
        games_json = games({})._container[0]
        games_dict = json.loads(games_json)

        self.assertEqual(games_dict[0]['name'], 'makao')
        self.assertEqual(games_dict[1]['name'], 'war')

    def test_create_game_get(self):
        req = request.HttpRequest()
        req.method = 'GET'

        config_json = game_create(req, WAR)._container[0]
        config_json = json.loads(config_json)

        with open(f'games/games_configs/{WAR}.json') as json_file:
            self.assertEquals(config_json, json.load(json_file))

    def test_create_game_get_not_exist(self):
        req = request.HttpRequest()
        req.method = 'GET'
        self.assertEqual(type(game_create(req, 'other_')),
                         HttpResponseNotFound)

    def test_create_game_post(self):
        req = request.HttpRequest()
        req.method = 'POST'
        req._body = json.dumps(WAR_BASE_CONFIG)

        response = game_create(req, WAR)
        self.assertEqual(type(response), JsonResponse)

        response_dict = json.loads(response._container[0])

        self.assertTrue(response_dict['game_id'] in redis_all_games_ids(WAR))

        delete_game(WAR, response_dict['game_id'])

    def test_create_game_post_wrong_data(self):
        req = request.HttpRequest()
        req.method = 'POST'
        req._body = json.dumps({})

        response = game_create(req, WAR)
        self.assertEqual(type(response), HttpResponseBadRequest)

    def test_create_game_no_data(self):
        req = request.HttpRequest()

        response = game_create(req, WAR)
        self.assertEqual(type(response), JsonResponse)

    def test_saml_view(self):
        req = request.HttpRequest()
        req._body = json.dumps(
            {
                'HTTP_HOST': '0.0.0.0'
            },
        )
        req.META['HTTP_HOST'] = '0.0.0.0'
        req.META['PATH_INFO'] = '/'
        req.session = {}

        response = saml_view(req)
        self.assertEqual(type(response), JsonResponse)

    def test_saml_view_sso(self):
        req = request.HttpRequest()
        req._body = json.dumps(
            {
                'HTTP_HOST': '0.0.0.0'
            },
        )
        req.META['HTTP_HOST'] = '0.0.0.0'
        req.META['PATH_INFO'] = '/'
        req.session = {}
        req.GET = {'sso2'}

        response = saml_view(req)
        self.assertEqual(type(response), HttpResponse)
        self.assertEqual(type(response._container[0]), bytes)

    def test_metadata(self):
        req = request.HttpRequest()
        response = metadata(req)

        self.assertEqual(type(response), HttpResponse)
        self.assertEqual(type(XML(response._container[0])), Element)

    def test_game_info(self):
        req = request.HttpRequest()
        response = game_info(req, WAR)

        self.assertEqual(type(response), JsonResponse)
        self.assertEqual(json.loads(response._container[0]), {
                         'type_name': 'war', 'description': '', 'name': 'war'})

    def test_game_info_no_exist(self):
        req = request.HttpRequest()
        response = game_info(req, 'other_')

        self.assertEqual(type(response), HttpResponseNotFound)

    def test_lobby_info(self):
        req = request.HttpRequest()
        req.method = 'POST'
        req._body = json.dumps(WAR_BASE_CONFIG)

        response = game_create(req, WAR)
        game_id = json.loads(response._container[0])['game_id']

        response = lobby_info(req, WAR, game_id)
        data = json.loads(response._container[0])

        self.assertEqual(type(response), JsonResponse)
        self.assertEqual(data['game_id'], game_id)

        delete_game(WAR, game_id)

    # count lobbies with len(players) > 0
    def test_game_lobbies(self):
        req = request.HttpRequest()
        req.method = 'POST'
        req._body = json.dumps(WAR_BASE_CONFIG)

        response = game_lobbies(req, WAR)
        data = json.loads(response._container[0])
        lobbies_count = len(data['lobbies'])

        response = game_create(req, WAR)
        game_id = json.loads(response._container[0])['game_id']

        response = game_lobbies(req, WAR)
        data = json.loads(response._container[0])
        self.assertEqual(len(data['lobbies']), lobbies_count)

        connect_to_game(
            WAR, game_id, {'nickname': 'user1', 'id': 1, 'ranking': 100})

        response = game_lobbies(req, WAR)
        data = json.loads(response._container[0])
        self.assertEqual(len(data['lobbies']), lobbies_count + 1)

        delete_game(WAR, game_id)

        response = game_lobbies(req, WAR)
        data = json.loads(response._container[0])
        self.assertEqual(len(data['lobbies']), lobbies_count)
