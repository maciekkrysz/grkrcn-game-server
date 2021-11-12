
from os import path
from django.conf import settings
from rejson import Client
import json

redis = Client(host=settings.REDIS_HOST,
               port=settings.REDIS_PORT, decode_responses=True)


def redis_list_from_dict(object_name, path_to_dict):
    try:
        dictt = redis.jsonget(object_name, path_to_dict)
        listt = []
        for k, v in dictt.items():
            listt.append({k:v})
        return listt
    except:
        return []

# def redis_get_json(key):
#     return json.loads(redis_inst.get(key).decode('utf-8'))


# def redis_set_json(key, val):
#     return redis_inst.set(key, json.dumps(val))
