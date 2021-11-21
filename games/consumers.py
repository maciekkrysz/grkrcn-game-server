import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .classes.games_handler import connect_to_game, debug_info, is_game_finished, make_move, possible_moves, \
    current_hand, current_state, game_info, game_self_info, mark_ready, start_game_possible, \
    start_game, disconnect_from_game


PUBLIC_MESSAGES = {
    'current_state_message',
    # 'ready_message',
    'games_info_message',
}


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # SAML VERIFICATION
        self.get_user_by_saml()

        self.type_game = self.scope['url_route']['kwargs']['type_game']
        self.room_name = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.type_game}_{self.room_name}'

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
            self.room_group_name, {
                'type': 'games_info_message'
            }
        )
        await self.channel_layer.group_send(
            self.user['nickname'], {
                'type': 'games_self_info_message'
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
        print('receive1')
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
        print('receive2')
        print(text_data_json['type'])
        print(debug_info(self.type_game, self.room_name))

    async def games_info_message(self, event):
        info = game_info(self.type_game, self.room_name)
        await self.send(text_data=json.dumps({
            'info': info,
            'type': 'games_info'
        }))

    async def games_self_info_message(self, event):
        info = game_self_info(
            self.type_game, self.room_name, self.user['nickname'])
        await self.send(text_data=json.dumps({
            'hand': info,
            'type': 'games_self_info'
        }))

    async def ready_message(self, event):
        print('tutaj')
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

    async def current_hand_message(self, event):
        hand = current_hand(self.type_game, self.room_name,
                            self.user['nickname'])
        await self.send(text_data=json.dumps({
            'hand': hand,
            'type': 'current_hand'
        }))

    async def current_state_message(self, event):
        state = current_state(self.type_game, self.room_name)
        await self.send(text_data=json.dumps({
            'state': state,
            'type': 'current_state'
        }))

    async def possible_moves_message(self, event):
        moves = possible_moves(
            self.type_game, self.room_name, self.user['nickname'])
        await self.send(text_data=json.dumps({
            'possible_moves': moves,
            'type': 'possible_moves'
        }))

    async def make_move_message(self, event):
        action = event['action']
        if 'move' in event:
            move = event['move']
        else:
            move = None
        if make_move(self.type_game, self.room_name, self.user['nickname'], action, move):
            await self.send(text_data='Correct')
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'current_state_message'}
            )
            # if end_game
        else:
            await self.send(text_data='Incorrect')

    async def end_game_message(self, event):
        pass

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def test_message(self, event):
        # info = start_game(self.type_game, self.room_name)
        # print(is_game_finished(self.type_game, self.room_name))
        pass

    def get_user_by_saml(self):
        # TODO verify user by saml
        import secrets
        self.user = {}
        self.user['nickname'] = 'user_' + str(secrets.randbelow(4) + 1)
        # self.user['nickname'] = 'user_' + '4'
        self.user['ranking'] = 1000
        print(f'connected user: {self.user}')
