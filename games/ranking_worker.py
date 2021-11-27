import pika
import os
import json
from rejson import Client

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')

redis = Client(host=REDIS_HOST,
               port=REDIS_PORT, decode_responses=True)


def callback_receive_rankings(ch, method, properties, body):
    """
    {
        'game_type': 'war',
        'game_id': 'ga1231',
        'players': {
            'id': {
                'nick': 'ktos',
                'ranking': 1200,
            }
        }
    }
    """
    body = json.loads(body)
    game_path = body['game_type'] + '.' + str(body['game_id'])
    print(f"Received {body}")
    for player_id in body['players'].keys():
        player = body['players'][player_id]
        for chair in redis.jsonget('games', f'.{game_path}.players').keys():
            if redis.jsonget('games', f'.{game_path}.players.{chair}.id') == int(player_id):
                redis.jsonset('games',
                              f'.{game_path}.players.{chair}.nickname_show', player['nickname'])
                redis.jsonset('games',
                              f'.{game_path}.players.{chair}.ranking', player['rank'])


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
print('Waiting for messages')

channel.basic_qos(prefetch_count=1)
channel.queue_declare(queue='send_user_data_queue', durable=True)

channel.basic_consume(queue='send_user_data_queue',
                      on_message_callback=callback_receive_rankings, auto_ack=True)
channel.start_consuming()
