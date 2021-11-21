from abc import ABC, abstractmethod
import secrets
import json
import random
from .cards_utils import get_cards_deck, get_random_hand
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
    def path_to_game(cls, game_id):
        return cls.__name__.lower() + '.' + game_id

    @classmethod
    def create_game(cls, user_json):
        type_game = cls.__name__.lower()
        # Redis identifier can only begin with a letter, a dollar sign or an underscore
        id = 'g' + secrets.token_hex(HASH_GAME_LEN)
        while redis.jsontype('games', f'.{type_game}.{id}'):
            id = 'g' + secrets.token_hex(HASH_GAME_LEN)

        user_json['players'] = {}
        user_json['status'] = 'waiting'
        # user_json['id'] = id

        # Create redis instance games: {type_game: {}} if does not exist
        redis.jsonset('games', '.', {}, nx=True)
        redis.jsonset('games', f'.{type_game}', {}, nx=True)

        # Add game to games
        redis.jsonset('games', f'.{type_game}.{id}', user_json)
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
    def get_first_possible_chair(cls, game_id):
        game = cls.path_to_game(game_id)
        chairs = redis.jsonget('games', f'.{game}.players').keys()
        for i in range(redis.jsonget('games', f'.{game}.game_parameters.max_players')):
            if 'p' + str(i+1) not in chairs:
                return 'p' + str(i+1)

    @classmethod
    def get_user_chair(cls, game_id, user):
        game = cls.path_to_game(game_id)
        for chair, values in redis.jsonget('games', f'.{game}.players').items():
            if values['nickname'] == user:
                return chair
        return None

    @classmethod
    def connect_to(cls, game_id, user):
        game = cls.path_to_game(game_id)
        # user = {nickname, ranking}
        user['ready'] = False
        user['active'] = True
        max_players = redis.jsonget(
            'games', f'.{game}.game_parameters.max_players')
        players = redis.jsonget('games', f'.{game}.players')

        if redis.jsonget('games', f'.{game}.status') == 'waiting' and max_players > len(players):
            chair = cls.get_first_possible_chair(game_id)
            redis.jsonset('games', f'.{game}.players.{chair}', user)
            return True
        elif redis.jsonget('games', f'.{game}.status') == 'ongoing':
            chair = cls.get_user_chair(game_id, user['nickname'])
            if chair:
                redis.jsonset('games', f'.{game}.players.{chair}.active', True)
                return True
        return False

    @classmethod
    def disconnect_from(cls, game_id, user):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        if redis.jsonget('games', f'.{game}.status') == 'waiting':
            redis.jsondel('games', f'.{game}.players.{chair}')
        elif redis.jsonget('games', f'.{game}.status') == 'ongoing':
            redis.jsonset('games', f'.{game}.players.{chair}.active', False)

    @classmethod
    def mark_ready(cls, game_id, user, value: bool):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        print('marking')
        print(chair)
        print(redis.jsonget('games', f'.{game}.players'))
        redis.jsonset('games', f'.{game}.players.{chair}.ready', value)

    @classmethod
    def game_info(cls, game_id):
        game = cls.path_to_game(game_id)
        info = {}
        players = redis.jsonget('games', f'.{game}.players')
        print(players)
        max_players = redis.jsonget(
            'games', f'.{game}.game_parameters.max_players')
        for p, values in players.items():
            info[p] = {}
            info[p]['nickname'] = values['nickname']
            info[p]['ranking'] = values['ranking']
            info[p]['ready'] = values['ready']
            info[p]['active'] = values['active']
        for i in range(len(info), max_players):
            info['p' + str(i+1)] = None
        info['status'] = redis.jsonget('games', f'.{game}.status')
        return info

    @classmethod
    def get_hand(cls, game_id, user):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        return redis.jsonget('games', f'.{game}.players.{chair}.hand')

    @classmethod
    def current_player(cls, game_id):
        game = cls.path_to_game(game_id)
        return redis.jsonget('games', f'.{game}.current_player')

    @classmethod
    def start_game_possible(cls, game_id):
        game = cls.path_to_game(game_id)
        max_players = redis.jsonget(
            'games', f'.{game}.game_parameters.max_players')
        players = len(redis.jsonget('games', f'.{game}.players'))
        print('max', 'players')
        print(max_players, players)
        if max_players == players:
            for values in redis.jsonget('games', f'.{game}.players').values():
                if values['ready'] == False:
                    return False
        else:
            return False
        return True

    @classmethod
    def start_game(cls, game_id):
        game = cls.path_to_game(game_id)
        redis.jsonset('games', f'.{game}.status', 'ongoing')
        card_deck = get_cards_deck()
        for player in redis.jsonget('games', f'.{game}.players'):
            card_deck, cards = get_random_hand(card_deck, redis.jsonget(
                'games', f'.{game}.game_parameters.cards_on_hand'))
            redis.jsonset('games', f'.{game}.players.{player}.hand', cards)
            time = redis.jsonget(
                'games', f'.{game}.game_parameters.time_per_player')
            redis.jsonset('games', f'.{game}.players.{player}.time', time)
            redis.jsonset('games', f'.{game}.players.{player}.points', 0)

        starting_player = random.choice(
            list(redis.jsonget('games', f'.{game}.players').keys()))
        redis.jsonset('games', f'.{game}.starting_player', starting_player)
        redis.jsonset('games', f'.{game}.current_player', starting_player)

        redis.jsonset('games', f'.{game}.stack_draw', card_deck)
        redis.jsonset('games', f'.{game}.stack_throw', [])

    @classmethod
    def game_state(cls, game_id):
        game = cls.path_to_game(game_id)
        players = {}
        for player, values in redis.jsonget('games', f'.{game}.players').items():
            player_info = {}
            player_info['cards_hand'] = redis.jsonarrlen(
                'games', f'.{game}.players.{player}.hand')
            player_info['time'] = redis.jsonget(
                'games', f'.{game}.players.{player}.time')
            player_info['points'] = redis.jsonget(
                'games', f'.{game}.players.{player}.points')
            players[player] = player_info

        stack_draw = redis.jsonarrlen('games', f'.{game}.stack_draw')
        stack_throw = redis.jsonarrlen('games', f'.{game}.stack_throw')
        cards_top = redis.jsonget('games', f'.{game}.stack_throw')
        if cards_top:
            cards_top = cards_top[-1]
        else:
            cards_top = '--'
        current_user = cls.current_player(game_id)

        state = {
            'players': players,
            'stack_draw': stack_draw,
            'stack_throw': stack_throw,
            'cards_top': cards_top,
            'current_user': current_user,
        }
        return state

    @classmethod
    def debug_info(cls, game_id):
        game = cls.path_to_game(game_id)
        print(redis.jsonget('games', f'.{game}'))

    @classmethod
    def is_game_active(cls, game_id):
        game = cls.path_to_game(game_id)
        return redis.jsonget('games', f'.{game}.status') == 'ongoing'

    @classmethod
    def get_next_player(cls, game_id):
        game = cls.path_to_game(game_id)
        players = list(redis.jsonget('games', f'.{game}.players').keys())
        curr_player = redis.jsonget('games', f'.{game}.current_player')
        return_player = players[0]
        for p in players[::-1]:
            if curr_player == p:
                return return_player
            return_player = p

    @classmethod
    @abstractmethod
    def is_game_finished(cls, game_id):
        pass

    @classmethod
    @abstractmethod
    def make_move(cls, game_id, user, move):
        pass

    @classmethod
    @abstractmethod
    def possible_moves(cls, game_id):
        pass