import pika
import logging
from ..redis_utils import redis


def callback_receive_rankings(ch, method, properties, body):
    body = body.decode()
    logging.log(logging.INFO, f"Received {body}")
    
    pass


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()

channel.basic_qos(prefetch_count=1)
channel.queue_declare(queue='send_user_data_queue', durable=True)

channel.basic_consume(queue='send_user_data_queue',
                      on_message_callback=callback_receive_rankings, auto_ack=True)
channel.start_consuming()
