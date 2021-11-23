import json
from typing import final
from channels.generic.websocket import AsyncWebsocketConsumer
from .classes.games_handler import connect_to_game, current_username, debug_info, get_all_players, is_game_finished, make_move, possible_moves, \
    current_hand, current_state, game_info, game_self_info, mark_ready, start_game_possible, \
    start_game, disconnect_from_game


import asyncio
PUBLIC_MESSAGES = {
    'current_state_message',
    'games_info_message',
    'chat_message',
    'active_message',
}

MESSAGES = PUBLIC_MESSAGES | {
    'ready_message',
    'games_self_info_message',
    'current_hand_message',
    'possible_moves_message',
    'make_move_message',
}


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # SAML VERIFICATION
        self.get_user_by_saml()

        self.type_game = self.scope['url_route']['kwargs']['type_game']
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'__game_{self.type_game}_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Join personal group
        await self.channel_layer.group_add(
            self.user['nickname'],
            self.channel_name
        )
        if connect_to_game(self.type_game, self.room_name, self.user):
            await self.accept()

        await self.channel_layer.group_send(
            self.user['nickname'], {
                'type': 'games_self_info_message'
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'games_info_message'
            }
        )

    async def disconnect(self, close_code):
        disconnect_from_game(
            self.type_game, self.room_name, self.user['nickname'])
        print('disconnect')
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_discard(
            self.user['nickname'],
            self.channel_name
        )

        await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'current_state_message'
            }
        )
        await self.channel_layer.group_send(
            self.room_group_name, {
                'type': 'games_info_message'
            }
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        text_data_json['type'] += '_message'

        if text_data_json['type'] not in MESSAGES:
            await self.channel_layer.group_send(
                self.user['nickname'],
                {'type': 'error_message', 'message': 'Incorrect command'}
            )
            return

        if text_data_json['type'] in PUBLIC_MESSAGES:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                text_data_json
            )
        else:
            # Send reply to sender
            await self.channel_layer.group_send(
                self.user['nickname'],
                text_data_json
            )
        print(debug_info(self.type_game, self.room_name))

    async def games_info_message(self, event):
        info = game_info(self.type_game, self.room_name)
        await self.send(text_data=json.dumps({
            'data': info,
            'type': 'games_info'
        }))

    async def games_self_info_message(self, event):
        info = game_self_info(
            self.type_game, self.room_name, self.user['nickname'])
        await self.send(text_data=json.dumps({
            'data': info,
            'type': 'games_self_info'
        }))

    async def ready_message(self, event):
        try:
            mark_ready(self.type_game, self.room_name,
                       self.user['nickname'], event['value'])
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'games_info_message'}
            )
            if start_game_possible(self.type_game, self.room_name):
                start_game(self.type_game, self.room_name)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'current_state_message'}
                )
                for player in get_all_players(self.type_game, self.room_name):
                    await self.channel_layer.group_send(
                        player,
                        {'type': 'current_hand_message'}
                    )
                current_username(self.type_game, self.room_name)
                await self.channel_layer.group_send(
                    current_username(self.type_game, self.room_name),
                    {'type': 'possible_moves_message'}
                )
        except:
            await self.channel_layer.group_send(
                self.user['nickname'],
                {'type': 'error_message', 'message': 'cannot set ready'}
            )

    async def current_hand_message(self, event):
        hand = current_hand(self.type_game, self.room_name,
                            self.user['nickname'])
        await self.send(text_data=json.dumps({
            'data': hand,
            'type': 'current_hand'
        }))

    async def current_state_message(self, event):
        state = current_state(self.type_game, self.room_name)
        await self.send(text_data=json.dumps({
            'data': state,
            'type': 'current_state'
        }))

    async def possible_moves_message(self, event):
        moves = possible_moves(
            self.type_game, self.room_name, self.user['nickname'])
        await self.send(text_data=json.dumps({
            'data': moves,
            'type': 'possible_moves'
        }))

    async def make_move_message(self, event):
        if 'move' in event:
            move = event['move']
        else:
            move = None
        try:
            action = event['action']
            if make_move(self.type_game, self.room_name, self.user['nickname'], action, move):
                await self.send(text_data='Correct')
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'current_state_message'}
                )
                for player in get_all_players(self.type_game, self.room_name):
                    await self.channel_layer.group_send(
                        player,
                        {'type': 'current_hand_message'}
                    )
                if is_game_finished(self.type_game, self.room_name):
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {'type': 'end_game_message'}
                    )
                await self.channel_layer.group_send(
                    current_username(self.type_game, self.room_name),
                    {'type': 'possible_moves_message'}
                )
            else:
                await self.send(text_data='Incorrect')
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            await self.channel_layer.group_send(
                self.user['nickname'],
                {'type': 'error_message', 'message': 'Error in move'}
            )

    async def end_game_message(self, event):
        pass

    # Receive message from room group
    async def chat_message(self, event):
        try:
            message = event['message']

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'data': {
                    'nickname': self.user['nickname'],
                    'message': message,
                },
                'type': 'chat',
            }))
        except:
            await self.channel_layer.group_send(
                self.user['nickname'],
                {'type': 'error_message', 'message': 'Error in message'}
            )

    async def test_message(self, event):
        # info = start_game(self.type_game, self.room_name)
        # print(is_game_finished(self.type_game, self.room_name))
        pass

    async def error_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'type': 'error'
        }))

    def get_user_by_saml(self):
        # TODO verify user by saml
        import secrets
        self.user = {}
        self.user['nickname'] = 'user_' + str(secrets.randbelow(4) + 1)
        # self.user['nickname'] = 'user_' + '4'
        self.user['ranking'] = 1000
        print(f'connected user: {self.user}')
