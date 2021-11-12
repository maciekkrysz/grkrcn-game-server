import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .classes.games_handler import connect_to_game


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

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            "game_war_id_pokoju",
            {
                'type': 'chat_message',
                'message': message
            }
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
        self.user = secrets.randbelow(10) + 1
