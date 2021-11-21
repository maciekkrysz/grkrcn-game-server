from .game import Game
from ..redis_utils import redis
from .cards_utils import get_random_card, get_random_hand
import json

temp_json = {
    "game_parameters": {
        "max_players": 2,
        "time_per_player": 120,
        "rounds": 2,
        "is_ranked": True,
        "cards_on_hand": 3,
    }
}

# temp_json = {
#     "game_parameters": {
#         "max_players": 2,
#         "time_per_player": 120,
#         "rounds": 2,
#         "is_ranked": True,
#         "cards_on_hand": 3,
#     },
#     'players': {},
#     'status': ''
# }

# with open("games/games_configs/war.json") as jsonFile:
#     jsonObject = json.load(jsonFile)
#     jsonFile.close()


class War(Game):
    @classmethod
    def start_game(cls, game_id):
        super().start_game(game_id)
        game = cls.path_to_game(game_id)
        for player in redis.jsonget('games', f'.{game}.players'):
            redis.jsonset(
                'games', f'.{game}.players.{player}.last_action', 'take')

    @classmethod
    def possible_moves(cls, game_id, user):
        game = cls.path_to_game(game_id)
        player = cls.get_user_chair(game_id, user)
        last_action = redis.jsonget(
            'games', f'.{game}.players.{player}.last_action')
        if last_action == 'take':
            return {
                'possible_actions': 'throw',
                'possible_moves': cls.get_hand(game_id, user)
            }
        elif last_action == 'throw':
            return {
                'possible_actions': 'take',
                'possible_moves': []
            }

    @classmethod
    def make_move(cls, game_id, user, action, move=None):
        game = cls.path_to_game(game_id)
        player = cls.get_user_chair(game_id, user)
        poss_moves = cls.possible_moves(game_id, user)
        if action in poss_moves['possible_actions']:
            if action == 'take':
                cards = redis.jsonget('games', f'.{game}.stack_draw')
                random_card = get_random_card(cards)
                card_index = redis.jsonarrindex('games', f'.{game}.stack_draw', random_card)
                redis.jsonarrpop('games', f'.{game}.stack_draw', card_index)
                redis.jsonarrappend('games', f'.{game}.players.{player}.hand', random_card)
                redis.jsonset('games', f'.{game}.current_player', cls.get_next_player(game_id))

            elif action == 'throw' and move in poss_moves['possible_moves']:
                card_index = redis.jsonarrindex('games', f'.{game}.players.{player}.hand', move)
                redis.jsonarrpop('games', f'.{game}.players.{player}.hand', card_index)
                redis.jsonarrappend('games', f'.{game}.stack_throw', move)

        redis.jsonset('games', f'.{game}.players.{player}.last_action', action)


    @classmethod
    def is_game_finished(cls, game_id):
        game = cls.path_to_game(game_id)
        for player, values in redis.jsonget('games', f'.{game}.players').items():
            if len(values['hand']) != 0:
                return False
        return True
        

# if War.check_create_game(temp_json):
#     print(War.create_game(temp_json))
