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
    game_class = get_class(game_type)
    if game_class.connect_to(game_id, user):
        pass
    pass
