import datetime
import json
import pika

def send_to_rabbitmq(jsonbody, queue_name):
    # set to rabbitmq, port
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    print(json.dumps(obj=jsonbody))
    channel.basic_publish(
        exchange='', routing_key=queue_name, body=json.dumps(jsonbody))
    connection.close()


data = {
    "game_type": "war",
    "players":
    {
        "1":
        {
            "points": 0,
            "score": "win",
            "left": False,
            "moves": 25,
            "time_sec": 100
        },
            "2":
            {
            "points": 0,
            "score": "win",
            "left": False,
            "moves": 25,
            "time_sec": 20
        }
    }
}
# data ="{\"game_type\": \"war\", \"players\":{" \
#                      "\"1\": {\"points\": 123, \"score\": \"win\", \"left\": false, \"time_sec\": 1143, \"moves\": 25}," \
#                      "\"6\": {\"points\": 123, \"score\": \"loose\", \"left\": false, \"time_sec\": 134, \"moves\": 25}," \
#                      "\"4\": {\"points\": -100, \"score\": \"loose\", \"left\": true, \"time_sec\": 13, \"moves\": 5}}}"

send_to_rabbitmq(data, queue_name='receive_ranking_queue')


# # scores = {'scores': {'win': ['user_1'], 'lose': ['user_2']}, 'reason': 'surrender'}

# # for endtype in scores['scores'].items():
# #     for nickname in endtype[1]:
# #         print(endtype, nickname)


def format_datetime(value: datetime.datetime) -> str:
    """
    Format a datetime for this SP. Some SPs are picky about their date
    formatting, and don't support the format produced by
    :meth:`datetime.datetime.isoformat`.
    """
    return value.isoformat()


time = datetime.datetime.now()
print(time.isoformat())
print(format_datetime(time))
