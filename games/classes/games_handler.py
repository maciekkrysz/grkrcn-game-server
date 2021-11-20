from .makao import Makao
from .war import War


def get_class(game_type):
    if game_type == 'war':
        return War
    elif game_type == 'makao':
        return Makao
    raise Exception('Gametype does not exist')


def create_game(game_type, user_json):
    print(user_json)
    game_class = get_class(game_type)
    if game_class.check_create_game(user_json):
        return game_class.create_game(user_json)
    raise Exception('Cannot create game')


def connect_to_game(game_type, game_id, user):
    return True
    game_class = get_class(game_type)
    if game_class.connect_to(game_id, user):
        return True
    return False


def game_self_info(game_type, game_id):
    game_self = {
        'chair': '1'
    }
    return game_self


def mark_ready(game_type, game_id, user):
    return True


def start_game_possible(game_type, game_id):
    return True


def start_game(type_game, room_name):
    pass


def game_info(game_type, game_id):
    players = {
        '1': {
            'nickname': 'p',
            'ranking': 1000,
            'ready': True,
            'active': False,
        },
        '2': None,
        '3': None,
        '4': None
    }
    return {
        'players': players,
        'state': 'waiting'  # in progress
    }


def current_state(game_type, game_id):

    players = {
        '1': {
            'cards_hand': 3,
            'time': 200,
            'points': 10,
        },
        '2': None
    }

    return {
        'players': players,
        'current_player': 1,
        'stack_throw': 12,
        'stack_draw': 4,
        'cards_top': '2C',
        'current_user': 1,
    }


def current_hand(game_type, game_id, user):
    game_class = get_class(game_type)
    # mocked
    return ['2C', '3D', '4H', '5S']


def possible_moves(game_type, game_id, user, moves_before=[]):
    game_class = get_class(game_type)
    # mocked
    return {
        'possible_actions': ['pass', 'take', 'throw'],
        'possible_moves': ['3C', '4H']
    }


def make_move(game_type, game_id, user, moves):
    game_class = get_class(game_type)
    return True
