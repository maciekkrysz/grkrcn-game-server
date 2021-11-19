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


def current_state(game_type, game_id):
    return {
        'hand_1': 4,
        'hand_2': 3,
        'stack_1': 15,
        'stack_2': 12,
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
    return ['3D', '5S', 'take', 'pass']


def make_move(game_type, game_id, user, moves):
    game_class = get_class(game_type)
    return True
