from .game import Game, FINISHED
from ..redis_utils import redis
from .cards_utils import get_random_card, get_random_hand, cards_prefix
import json

temp_json = {
    'game_parameters': {
        'max_players': 2,
        'time_per_player': 120,
        'rounds': 2,
        'is_ranked': True,
        'cards_on_hand': 3,
    }
}

# temp_json = {
#     'game_parameters': {
#         'max_players': 2,
#         'time_per_player': 120,
#         'rounds': 2,
#         'is_ranked': True,
#         'cards_on_hand': 3,
#     },
#     'players': {},
#     'status': ''
# }

# with open('games/games_configs/war.json') as jsonFile:
#     jsonObject = json.load(jsonFile)
#     jsonFile.close()


class War(Game):
    @classmethod
    def start_game(cls, game_id):
        super().start_game(game_id)
        game = cls.path_to_game(game_id)
        for player in redis.jsonget('games', f'.{game}.players'):
            redis.jsonset('games', f'.{game}.players.{player}.last_action',
                          'take')
        redis.jsonset('games', f'.{game}.war_event', False)
        redis.jsonset('games', f'.{game}.war_event_next_move', False)

    @classmethod
    def possible_moves(cls, game_id, user):
        game = cls.path_to_game(game_id)
        player = cls.get_user_chair(game_id, user)
        last_action = redis.jsonget('games',
                                    f'.{game}.players.{player}.last_action')
        stack_draw = redis.jsonget('games', f'.{game}.stack_draw')

        if last_action == 'take' or len(stack_draw) == 0:
            return {
                'possible_actions': ['throw'],
                'possible_moves': cls.get_hand(game_id, user),
            }
        elif last_action == 'throw':
            return {'possible_actions': ['take'], 'possible_moves': []}

    @classmethod
    def make_move(cls, game_id, user, action, move=None):
        super().make_move(game_id, user, action, move)
        game = cls.path_to_game(game_id)
        player = cls.get_user_chair(game_id, user)
        poss_moves = cls.possible_moves(game_id, user)
        if action in poss_moves['possible_actions']:
            if action == 'take':
                cards = redis.jsonget('games', f'.{game}.stack_draw')
                random_card = get_random_card(cards)
                card_index = redis.jsonarrindex('games', f'.{game}.stack_draw',
                                                random_card)
                redis.jsonarrpop('games', f'.{game}.stack_draw', card_index)
                redis.jsonarrappend('games', f'.{game}.players.{player}.hand',
                                    random_card)

            elif action == 'throw' and move in poss_moves['possible_moves']:
                if len(redis.jsonget('games', f'.{game}.stack_draw')) == 0:
                    redis.jsonset(
                        'games', f'.{game}.next_player', cls.get_next_player(game_id))
                else:
                    redis.jsonset(
                        'games', f'.{game}.next_player', cls.current_player(game_id))

                if redis.jsonget('games', f'.{game}.war_event_next_move'):
                    redis.jsonset('games', f'.{game}.war_event', True)
                else:
                    redis.jsonset('games', f'.{game}.war_event', False)

                card_index = redis.jsonarrindex(
                    'games', f'.{game}.players.{player}.hand', move)
                redis.jsonarrpop('games', f'.{game}.players.{player}.hand',
                                 card_index)
                redis.jsonarrappend('games', f'.{game}.stack_throw', move)
                players = redis.jsonget(
                    'games', f'.{game}.game_parameters.max_players')
                stack_throw = redis.jsonget('games', f'.{game}.stack_throw')
                war_event = redis.jsonget('games', f'.{game}.war_event')
                print(stack_throw)
                print('war_event', war_event)
                if len(stack_throw) % players == 0:
                    if not war_event:
                        if cls.compare_card(stack_throw[-1], stack_throw[-2]) == 1:
                            p_win = redis.jsonget(
                                'games', f'.{game}.current_player')
                        elif cls.compare_card(stack_throw[-1], stack_throw[-2]) == -1:
                            p_win = cls.get_next_player(game_id)
                        else:
                            redis.jsonset(
                                'games', f'.{game}.war_event_next_move', True)
                            redis.jsonset(
                                'games', f'.{game}.players.{player}.last_action', action)

                            redis.jsonset('games', f'.{game}.current_player',
                                          cls.get_next_player(game_id))
                            return True

                        redis.jsonnumincrby(
                            'games', f'.{game}.players.{p_win}.points', len(stack_throw))
                        redis.jsonset('games', f'.{game}.stack_throw', [])
                        redis.jsonset('games', f'.{game}.next_player', p_win)
                    else:
                        redis.jsonset(
                            'games', f'.{game}.war_event_next_move', False)
        else:
            return False
        redis.jsonset('games', f'.{game}.current_player',
                      cls.get_next_player(game_id))
        redis.jsonset('games', f'.{game}.players.{player}.last_action', action)
        return True

    @classmethod
    def game_state(cls, game_id):
        game = cls.path_to_game(game_id)
        info = super().game_state(game_id)
        if redis.jsonget('games', f'.{game}.war_event'):
            info['cards_top'] = '--'
        return info

    @classmethod
    def is_game_finished(cls, game_id):
        game = cls.path_to_game(game_id)
        if redis.jsonget('games', f'.{game}.status') == FINISHED:
            return True
        for player, values in redis.jsonget('games',
                                            f'.{game}.players').items():
            if len(values['hand']) != 0:
                return False
        return True

    @classmethod
    def check_if_draw(cls, game_id):
        game = cls.path_to_game(game_id)
        points1 = redis.jsonget('games', f'.{game}.players.p1.points')
        points2 = redis.jsonget('games', f'.{game}.players.p2.points')
        if points1 == points2 or redis.jsonget('games', f'.{game}.is_draw'):
            return True

    @classmethod
    def change_war_event(cls, game_id):
        game = cls.path_to_game(game_id)
        war_event = redis.jsonget('games', f'.{game}.war_event')
        redis.jsonset('games', f'.{game}.war_event', not war_event)

    @classmethod
    def get_next_player(cls, game_id):
        game = cls.path_to_game(game_id)
        try:
            next = redis.jsonget('games', f'.{game}.next_player')
            redis.jsondel('games', f'.{game}.next_player')
            return next
        except:
            return super().get_next_player(game_id)

    @classmethod
    def choose_losers(cls, game_id):
        game = cls.path_to_game(game_id)
        redis.jsonset('games', f'.{game}.scores.lose', [])
        points1 = redis.jsonget('games', f'.{game}.players.p1.points')
        points2 = redis.jsonget('games', f'.{game}.players.p2.points')
        if points1 < points2:
            lose = 'p1'
        else:
            lose = 'p2'
        lose_nick = redis.jsonget('games', f'.{game}.players.{lose}.nickname')
        redis.jsonarrappend('games', f'.{game}.scores.lose', lose_nick)

    @classmethod
    def get_losing_nicknames(cls, game_id):
        game = cls.path_to_game(game_id)
        losing = []
        for p in redis.jsonget('games', f'.{game}.scores.lose'):
            losing.append(p)
        return losing

    def compare_card(card1, card2):
        if card1[0] == card2[0]:
            return 0
        elif cards_prefix.index(card1[0]) > cards_prefix.index(card2[0]):
            return 1
        else:
            return -1


# if War.check_create_game(temp_json):
#     print(War.create_game(temp_json))
