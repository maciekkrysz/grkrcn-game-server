import pika
import json

# set to rabbitmq, port
# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='localhost'))


def send_ranking_request(jsonbody):
    """
    jsonbody = {
        'game_type': war,
        'game_id': game_id,
        'players': [id1, id2]
    }
    """
    send_to_rabbitmq(jsonbody, queue_name='receive_user_data_queue')


def send_game_data(jsonbody):
    """
    {
    "game_type": "war",
    "players":
        {
            "nickname":
            {
                "points": 0,
                "score": "win",
                "left": False,
                "moves": 25,
                "time_sec": 100
            },
            "nickname":
            {
                "points": 0,
                "score": "win",
                "left": False,
                "moves": 25,
                "time_sec": 100
            }
        }
    }
    """
    send_to_rabbitmq(jsonbody, queue_name='receive_ranking_queue')


def send_to_rabbitmq(jsonbody, queue_name):
    # set to rabbitmq, port
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    print(json.dumps(obj=jsonbody))
    channel.basic_publish(
        exchange='', routing_key=queue_name, body=json.dumps(obj=jsonbody))
    connection.close()
