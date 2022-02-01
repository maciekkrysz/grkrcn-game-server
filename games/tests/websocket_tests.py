from unittest.mock import patch
from django.test import TestCase
from django.db import connection, connections

from ..models import GameType
from ..classes.games_handler import create_game
from ..redis_utils import redis
import asyncio

from channels.testing import WebsocketCommunicator
from ..consumers import GameConsumer
from .consts import WAR, WAR_BASE_CONFIG


class GameConsumerConnectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        GameType.objects.create(
            type_name='war'
        )
        cls.user_config = WAR_BASE_CONFIG
        cls.game = WAR

        cls.player1 = WebsocketCommunicator(
            GameConsumer.as_asgi(), "/testws/")

        cls.player2 = WebsocketCommunicator(
            GameConsumer.as_asgi(), "/testws/")

    @classmethod
    async def new_game(cls):
        cls.id_game = create_game(cls.game, cls.user_config)
        cls.url_route = {
            'kwargs':
            {
                'type_game': cls.game,
                'room_id': cls.id_game,
            }
        }
        cls.player1.scope['url_route'] = cls.url_route
        cls.player2.scope['url_route'] = cls.url_route

    @classmethod
    async def del_game(cls):
        redis.jsondel('games', f'.{cls.game}.{cls.id_game}')
        connection.close()
        connections.close_all()

    # @patch('games.consumers.GameConsumer.get_user_by_saml',
    #        side_effect=[
    #            {'id': 1, 'nickname': 'User1', 'ranking': 1000},
    #            {'id': 2, 'nickname': 'User2', 'ranking': 1100},
    #            {'id': 3, 'nickname': 'User3', 'ranking': 1200},
    #            {'id': 3, 'nickname': 'User3', 'ranking': 1200}
    #        ])
    # @patch('games.consumers.request_for_ranking')
    # async def test_connect_to_websocket(self, user, rabbit_send):
    #     await self.new_game()
    #     self.assertEquals(
    #         len(redis.jsonget('games', f'.{self.game}.{self.id_game}.players')), 0)

    #     user1 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
    #     user1.scope['url_route'] = self.url_route
    #     connected, subprotocol = await user1.connect()
    #     assert connected
    #     self.assertEquals(
    #         len(redis.jsonget('games', f'.{self.game}.{self.id_game}.players')), 1)

    #     user2 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
    #     user2.scope['url_route'] = self.url_route
    #     connected, subprotocol = await user2.connect()
    #     assert connected
    #     self.assertEquals(
    #         len(redis.jsonget('games', f'.{self.game}.{self.id_game}.players')), 2)

    #     # third user when max_players = 2
    #     user3 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
    #     user3.scope['url_route'] = self.url_route
    #     connected, subprotocol = await user3.connect()
    #     self.assertEquals(
    #         len(redis.jsonget('games', f'.{self.game}.{self.id_game}.players')), 2)

    #     await user2.disconnect()
    #     self.assertEquals(
    #         len(redis.jsonget('games', f'.{self.game}.{self.id_game}.players')), 1)

    #     await user3.connect()
    #     self.assertEquals(
    #         len(redis.jsonget('games', f'.{self.game}.{self.id_game}.players')), 2)

    #     await user1.disconnect()
    #     await user3.disconnect()
    #     await self.del_game()
    #     await asyncio.sleep(3)

    @patch('games.consumers.GameConsumer.get_user_by_saml',
           side_effect=[
               {'id': 1, 'nickname': 'User1', 'ranking': 1000},
               {'id': 2, 'nickname': 'User2', 'ranking': 1100},
           ])
    @patch('games.consumers.request_for_ranking')
    async def test_simple_connection_test(self, saml, ranking):
        print('TEST_EXAMPLE')
        await self.new_game()

        user1 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user1.scope['url_route'] = self.url_route
        user2 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user2.scope['url_route'] = self.url_route
        await user1.connect()
        await user2.connect()

        await user1.disconnect()
        await user2.disconnect()
        await self.del_game()
        await asyncio.sleep(1)

    @patch('games.consumers.GameConsumer.get_user_by_saml',
           side_effect=[
               {'id': 1, 'nickname': 'User1', 'ranking': 1000},
               {'id': 2, 'nickname': 'User2', 'ranking': 1100},
           ])
    @patch('games.consumers.request_for_ranking')
    async def test_game_scores(self, saml, ranking):
        GameType.objects.create(
            type_name='Wąr',
        )
        await self.new_game()

        user1 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user1.scope['url_route'] = self.url_route
        user2 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user2.scope['url_route'] = self.url_route
        await user1.connect()
        dictionary = {
            'type': 'ready',
            'value': True,
        }
        await user2.connect()
        await user1.send_json_to(dictionary)
        await user2.send_json_to(dictionary)
        await asyncio.sleep(1)

        start_player = redis.jsonget(
            'games', f'.{self.game}.{self.id_game}.current_player')
        if start_player == 'p1':
            player1 = user1
            player2 = user2
        else:
            player1 = user2
            player2 = user1

        possible_moves = redis.jsonget(
            'games', f'.{self.game}.{self.id_game}.players.{start_player}.hand')
        await player1.send_json_to({'type': 'make_move', 'action': 'throw', 'move': possible_moves[0]})
        await player1.send_json_to({'type': 'possible_moves'})
        await asyncio.sleep(1)

        await player1.send_json_to({'type': 'surrender'})
        await asyncio.sleep(1)

        possible_moves = redis.jsonget(
            'games', f'.{self.game}.{self.id_game}.players.{start_player}.hand')
        await player1.send_json_to({'type': 'make_move', 'action': 'throw', 'move': possible_moves[0]})
        await player1.send_json_to({'type': 'make_move', 'action': 'take'})
        await player1.send_json_to({'type': 'possible_moves'})
        await asyncio.sleep(1)

        scores = redis.jsonget('games', f'.{self.game}.{self.id_game}.scores')
        loser = redis.jsonget(
            'games', f'.{self.game}.{self.id_game}.players.{start_player}.nickname')
        print(scores)
        self.assertTrue(loser not in scores['win'])
        self.assertTrue(loser in scores['lose'])
        await user1.send_json_to({'type': 'rematch'})
        await asyncio.sleep(2)

        await user2.disconnect()
        await user1.disconnect()
        await self.del_game()
        await asyncio.sleep(1)

    @patch('games.consumers.GameConsumer.get_user_by_saml',
           side_effect=[
               {'id': 1, 'nickname': 'User1', 'ranking': 1000},
               {'id': 2, 'nickname': 'User2', 'ranking': 1100},
           ])
    @patch('games.consumers.request_for_ranking')
    async def test_simple_connection_test(self, saml, ranking):
        await self.new_game()

        user1 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user1.scope['url_route'] = self.url_route
        user2 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user2.scope['url_route'] = self.url_route
        await user1.connect()
        await user2.connect()

        await user1.disconnect()
        await user2.disconnect()
        await self.del_game()
        await asyncio.sleep(3)

    @patch('games.consumers.GameConsumer.get_user_by_saml',
           side_effect=[
               {'id': 1, 'nickname': 'User1', 'ranking': 1000},
               {'id': 2, 'nickname': 'User2', 'ranking': 1100},
           ])
    @patch('games.consumers.request_for_ranking')
    async def test_game_active(self, saml, ranking):
        GameType.objects.create(
            type_name='Wąr',
        )
        await self.new_game()

        user1 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user1.scope['url_route'] = self.url_route
        user2 = WebsocketCommunicator(GameConsumer.as_asgi(), "/testws/")
        user2.scope['url_route'] = self.url_route
        await user1.connect()
        dictionary = {
            'type': 'ready',
            'value': True,
        }
        await user2.connect()
        await user1.send_json_to(dictionary)
        await user1.send_json_to({'type': 'active', 'value': False})
        await user1.send_json_to({'type': 'active', 'value': True})
        await user1.send_json_to({'type': 'chat', 'message': '1'})
        await user1.send_json_to({'type': 'error', 'value': 'message'})
        await user1.send_json_to({'type': 'send_update'})
        await user2.send_json_to(dictionary)
        await asyncio.sleep(3)

        await user2.disconnect()
        await user1.disconnect()
        await self.del_game()
        await asyncio.sleep(1)
