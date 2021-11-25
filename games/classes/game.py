from abc import ABC, abstractmethod
import secrets
import json
import random
import time

from .cards_utils import get_cards_deck, get_random_hand
from ..redis_utils import redis

HASH_GAME_LEN = 4
WAITING = 'waiting'
ONGOING = 'ongoing'
FINISHED = 'finished'


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

        redis.jsonset('games', f'.{type_game}.{id}.scores', {
                      'win': [], 'lose': []})
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
            def get_seconds(time):
                multipier = 1
                seconds = 0
                for el in time.split(':')[::-1]:
                    seconds += int(el) * multipier
                    multipier *= 60
                return seconds
            if get_seconds(config_param['min']) < user_value < get_seconds(config_param['max']):
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
        if user['nickname'] in cls.get_all_players(game_id):
            chair = cls.get_user_chair(game_id, user['nickname'])
            redis.jsonset('games', f'.{game}.players.{chair}.active', True)
            redis.jsonset(
                'games', f'.{game}.players.{chair}.inactive_pings', 0)
            return True
        elif redis.jsonget('games', f'.{game}.status') == WAITING and max_players > len(players):
            if cls.get_user_chair(game_id, user):
                return True
            # if cls.is_user_in_any_game(user['nickname']):
            #     return False
            chair = cls.get_first_possible_chair(game_id)
            redis.jsonset('games', f'.{game}.players.{chair}', user)
            return True
        return False

    @classmethod
    def disconnect_from(cls, game_id, user):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        status = redis.jsonget('games', f'.{game}.status')
        if status == WAITING or status == FINISHED:
            redis.jsondel('games', f'.{game}.players.{chair}')
        elif status == ONGOING:
            redis.jsonset('games', f'.{game}.players.{chair}.active', False)

    @classmethod
    def mark_ready(cls, game_id, user, value: bool):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        if isinstance(value, bool):
            redis.jsonset('games', f'.{game}.players.{chair}.ready', value)

    @classmethod
    def mark_active(cls, game_id, user, value: bool):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        if isinstance(value, bool):
            redis.jsonset('games', f'.{game}.players.{chair}.active', value)
            if value:
                redis.jsonset(
                    'games', f'.{game}.players.{chair}.inactive_pings', 0)
            else:
                cls.add_inactive_ping(game_id, chair)

    @classmethod
    def add_inactive_ping(cls, game_id, chair):
        game = cls.path_to_game(game_id)
        redis.jsonnumincrby(
            'games', f'.{game}.players.{chair}.inactive_pings', 1)

    @classmethod
    def game_info(cls, game_id):
        game = cls.path_to_game(game_id)
        info = {}
        info['players'] = []
        players = redis.jsonget('games', f'.{game}.players')

        max_players = redis.jsonget(
            'games', f'.{game}.game_parameters.max_players')
        info['max_players'] = max_players
        for p, values in players.items():
            player = {}
            player['position'] = p
            player['nickname'] = values['nickname']
            player['ranking'] = values['ranking']
            player['ready'] = values['ready']
            player['active'] = values['active']
            info['players'].append(player)
        for i in range(len(info), max_players):
            info['players']['p' + str(i+1)] = None
        info['status'] = redis.jsonget('games', f'.{game}.status')
        print(info)
        return info

    @classmethod
    def get_all_players(cls, game_id):
        game = cls.path_to_game(game_id)
        nicknames = []
        for p, values in redis.jsonget('games', f'.{game}.players').items():
            nicknames.append(values['nickname'])
        return nicknames

    @classmethod
    def get_hand(cls, game_id, user):
        game = cls.path_to_game(game_id)
        chair = cls.get_user_chair(game_id, user)
        return redis.jsonget('games', f'.{game}.players.{chair}.hand')

    @classmethod
    def current_username(cls, game_id):
        game = cls.path_to_game(game_id)
        current_player = cls.current_player(game_id)
        for p, values in redis.jsonget('games', f'.{game}.players').items():
            if p == current_player:
                return values['nickname']

    @classmethod
    def current_player(cls, game_id):
        game = cls.path_to_game(game_id)
        if redis.jsonget('games', f'.{game}.status') == ONGOING:
            return redis.jsonget('games', f'.{game}.current_player')

    @classmethod
    def start_game_possible(cls, game_id):
        game = cls.path_to_game(game_id)
        if redis.jsonget('games', f'.{game}.status') != WAITING \
                and redis.jsonget('games', f'.{game}.status') != ONGOING:
            return False
        max_players = redis.jsonget(
            'games', f'.{game}.game_parameters.max_players')
        players = len(redis.jsonget('games', f'.{game}.players'))

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
        redis.jsonset('games', f'.{game}.status', ONGOING)
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
        redis.jsonset('games', f'.{game}.move_time', time.time())

    @classmethod
    def game_state(cls, game_id):
        game = cls.path_to_game(game_id)
        players = []
        for player, values in redis.jsonget('games', f'.{game}.players').items():
            player_info = {}
            player_info['cards_hand'] = redis.jsonarrlen(
                'games', f'.{game}.players.{player}.hand')
            player_info['time'] = redis.jsonget(
                'games', f'.{game}.players.{player}.time')
            player_info['points'] = redis.jsonget(
                'games', f'.{game}.players.{player}.points')
            player_info['position'] = player
            players.append(player_info)

        stack_draw = redis.jsonarrlen('games', f'.{game}.stack_draw')
        stack_throw = redis.jsonarrlen('games', f'.{game}.stack_throw')
        cards_top = redis.jsonget('games', f'.{game}.stack_throw')
        if cards_top:
            cards_top = cards_top[-1]
        else:
            cards_top = '--'
        current_user = cls.current_player(game_id)

        state = {
            'current_user': current_user,
            'players': players,
            'stack_draw': stack_draw,
            'stack_throw': stack_throw,
            'cards_top': cards_top,
        }
        return state

    @classmethod
    def debug_info(cls, game_id):
        game = cls.path_to_game(game_id)
        print(redis.jsonget('games', f'.{game}'))

    @classmethod
    def is_game_active(cls, game_id):
        game = cls.path_to_game(game_id)
        return redis.jsonget('games', f'.{game}.status') == ONGOING

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
    def is_user_in_any_game(cls, user):
        for game_id in redis.jsonget('games', f'.{cls.__name__.lower()}'):
            if cls.get_user_chair(game_id, user):
                return True
        return False

    @classmethod
    def is_game_ongoing(cls, game_id):
        game = cls.path_to_game(game_id)
        return redis.jsonget('games', f'.{game}.status') == ONGOING

    @classmethod
    def surrend(cls, game_id, user):
        game = cls.path_to_game(game_id)
        cls.finish_game(game_id, user)

    @classmethod
    def finish_game(cls, game_id, lose_user):
        game = cls.path_to_game(game_id)
        players = cls.get_all_players(game_id)
        players.remove(lose_user)

        redis.jsonarrappend('games', f'.{game}.scores.lose', lose_user)
        for p in players:
            redis.jsonarrappend('games', f'.{game}.scores.win', p)
        redis.jsonset('games', f'.{game}.status', FINISHED)

    @classmethod
    def get_finish_scores(cls, game_id):
        game = cls.path_to_game(game_id)
        return redis.jsonget('games', f'.{game}.scores')

    @classmethod
    def set_status_waiting(cls, game_id):
        game = cls.path_to_game(game_id)
        redis.jsonset('games', f'.{game}.status', WAITING)

    @classmethod
    def make_move(cls, game_id, user, move):
        finish_time = time.time()
        game = cls.path_to_game(game_id)
        pass

    @classmethod
    @abstractmethod
    def is_game_finished(cls, game_id):
        pass

    @classmethod
    @abstractmethod
    def possible_moves(cls, game_id):
        pass
