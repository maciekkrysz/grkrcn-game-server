from abc import ABC, abstractmethod
import secrets
import json
from ..redis_utils import redis

HASH_GAME_LEN = 4


class Game(ABC):
    @classmethod
    def get_config_json(cls):
        with open(f'games/games_configs/{cls.__name__}.json', 'r') as jsonFile:
            jsonObject = json.load(jsonFile)
            jsonFile.close()
        return jsonObject

    @classmethod
    def create_game(cls, user_json):
        type_game = cls.__name__.lower()
        # Redis identifier can only begin with a letter, a dollar sign or an underscore
        id = 'g' + secrets.token_hex(HASH_GAME_LEN)
        while redis.jsontype('available_games', f'.{type_game}.{id}') \
                or redis.jsontype('ongoing_games', f'.{type_game}.{id}'):
            id = 'g' + secrets.token_hex(HASH_GAME_LEN)

        user_json['players'] = {}
        user_json['status'] = 'waiting'
        # user_json['id'] = id

        # Create redis instance available_games: {type_game: {}} if does not exist
        redis.jsonset('available_games', '.', {}, nx=True)
        redis.jsonset('available_games', f'.{type_game}', {}, nx=True)

        # Add game to available_games
        redis.jsonset('available_games', f'.{type_game}.{id}', user_json)
        return id

    @classmethod
    def check_create_game(cls, user_json) -> bool:
        config_json = cls.get_config_json()
        for k in config_json.keys():
            if k != 'game_params':
                cls.check_param(
                    user_json['game_parameters'][k], config_json[k])

        for elem in config_json['game_params']:
            k = elem['param_name']
            cls.check_param(user_json['game_parameters']
                            [k], elem['param_setup'])
        return True

    def check_param(user_value, config_param):
        param_type = config_param['type']
        if param_type == 'int':
            user_value = int(user_value)
            if user_value >= config_param['min'] and user_value <= config_param['max']:
                return True
        elif param_type == 'bool':
            user_value = bool(user_value)
            return True
        elif param_type == 'time':
            return True
        else:
            raise Exception('Parameter type has no implemented checking')
        raise Exception(f'{param_type} parameter is incorrect')

    @classmethod
    def connect_to(cls, game_id, user):
        pass

    @abstractmethod
    def make_move(self, **kwargs):
        pass

    @abstractmethod
    def possible_moves(self):
        pass

    @abstractmethod
    def current_player(self):
        pass

    @abstractmethod
    def start_game(self):
        pass
