import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .classes.games_handler import connect_to_game, make_move, possible_moves, \
    current_hand, current_state, game_info, game_self_info, mark_ready, start_game_possible, \
    start_game


public_messages = {
    'current_state_message',
    'ready_message',
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
            self.user,
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
            self.room_group_name, {
                'type': 'games_self_info_message'
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.channel_layer.group_discard(
            self.user,
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
        if 'secret' not in text_data_json:
            text_data_json['secret'] = False

        if text_data_json['secret']:
            # Send reply to sender
            await self.channel_layer.group_send(
                self.user,
                text_data_json
            )
        else:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                text_data_json
            )

    async def games_info_message(self, event):
        info = game_info(self.type_game, self.room_name)
        await self.send(text_data=json.dumps({
            'hand': info,
            'type': 'games_info'
        }))

    async def games_self_info_message(self, event):
        info = game_self_info(self.type_game, self.room_name)
        await self.send(text_data=json.dumps({
            'hand': info,
            'type': 'games_self_info'
        }))

    async def ready_message(self, event):
        mark_ready(self.type_game, self.room_name, self.user)
        if start_game_possible(self.type_game, self.room_name):
            start_game(self.type_game, self.room_name)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'current_state_message'}
            )

    async def current_hand_message(self, event):
        hand = current_hand(self.type_game, self.room_name, self.user)
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
            self.type_game, self.room_name, self.user)
        await self.send(text_data=json.dumps({
            'possible_moves': moves,
            'type': 'possible_moves'
        }))

    async def make_move_message(self, event):
        moves = event['moves']
        print(moves)
        if make_move(self.type_game, self.room_name, self.user, moves):
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

    def get_user_by_saml(self):
        # TODO verify user by saml
        import secrets
        self.user = 'user_' + str(secrets.randbelow(10) + 1)
        print(f'connected user: {self.user}')
