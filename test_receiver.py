import json
import os
import pika
import logging


# connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('RABBIT_HOST')))
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()
channel.queue_declare(queue='send_user_data_queue', durable=True)
channel.queue_declare(queue='receive_user_data_queue', durable=True)


logging.basicConfig(level=logging.INFO)
logging.log(logging.INFO, 'Waiting for messages')


def callback_game_data(ch, method, properties, body):
    print(body)
    body = body.decode()
    logging.log(logging.ERROR, f"Received {body}")
    print(body)


def callback_receive(ch, method, properties, body):
    body = body.decode()
    logging.log(logging.INFO, f"Received in receive {body}")


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='send_user_data_queue',
                      on_message_callback=callback_game_data, auto_ack=True)
channel.basic_consume(queue='receive_user_data_queue',
                      on_message_callback=callback_receive, auto_ack=True)
channel.start_consuming()
