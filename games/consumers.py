import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .classes.games_handler import connect_to_game, make_move, possible_moves, current_hand, current_state


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

    async def current_hand_message(self, event):
        hand = current_hand(self.type_game, self.room_name, self.user)
        await self.send(text_data=json.dumps({
            'hand': hand
        }))

    async def current_state_message(self, event):
        state = current_state(self.type_game, self.room_name)
        await self.send(text_data=json.dumps(state))

    async def possible_moves_message(self, event):
        if 'moves_before' not in event:
            event['moves_before'] = []
        moves = possible_moves(
            self.type_game, self.room_name, self.user, event['moves_before'])
        await self.send(text_data=json.dumps({
            'possible_moves': moves
        }))

    async def make_move_message(self, event):
        moves = event['moves']
        if make_move(self.type_game, self.room_name, self.user, moves):
            await self.send(text_data='Correct')
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'current_state_message'}
            )

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
