from .makao import Makao
from .war import War
from ..models import GameType, Game, Participation
from asgiref.sync import async_to_sync


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


def delete_game(game_type, game_id):
    game_class = get_class(game_type)
    game_class.delete_game(game_id)


def connect_to_game(game_type, game_id, user):
    game_class = get_class(game_type)
    if game_class.connect_to(game_id, user):
        return True
    return False


def disconnect_from_game(game_type, game_id, user):
    game_class = get_class(game_type)
    game_class.disconnect_from(game_id, user)


def game_self_info(game_type, game_id, user):
    game_class = get_class(game_type)
    game_self = {
        'chair': game_class.get_user_chair(game_id, user)
    }
    return game_self


def mark_ready(game_type, game_id, user, value):
    game_class = get_class(game_type)
    game_class.mark_ready(game_id, user, value)


def mark_active(game_type, game_id, user, value):
    game_class = get_class(game_type)
    game_class.mark_active(game_id, user, value)


def start_game_possible(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.start_game_possible(game_id)


def start_game(game_type, game_id):
    game_class = get_class(game_type)
    game_class.start_game(game_id)

    info = game_class.debug_info(game_id)
    info['game_id'] = game_id
    modeltype = GameType.objects.get_typegame_lower_nospecial(game_type)
    modelgame = Game.objects.create(game_type=modeltype, start_state=info)
    for player_id in game_class.get_players_ids(game_id):
        Participation.objects.create(user=player_id,
                                     game=modelgame,
                                     score=Participation.ScoreTypes.IN_PROGRESS)


def game_info(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.game_info(game_id)


def get_all_players(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.get_all_players(game_id)


def get_all_chairs(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.get_all_chairs(game_id)


def current_state(game_type, game_id):
    game_class = get_class(game_type)
    game_class.check_timers(game_id)
    if game_class.is_game_ongoing(game_id):
        return game_class.game_state(game_id)
    elif game_class.is_game_finished(game_id):
        return game_class.get_finish_scores(game_id)


def current_hand(game_type, game_id, user):
    game_class = get_class(game_type)
    return game_class.get_hand(game_id, user)


def current_username(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.current_username(game_id)


def possible_moves(game_type, game_id, user):
    game_class = get_class(game_type)
    return game_class.possible_moves(game_id, user)


def start_counting_timeout(game_type, game_id, user):
    game_class = get_class(game_type)
    return game_class.start_counting_timeout(game_id, user)


def make_move(game_type, game_id, user, action, move):
    game_class = get_class(game_type)
    return game_class.make_move(game_id, user, action, move)


def is_game_ongoing(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.is_game_ongoing(game_id)


def is_game_finished(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.is_game_finished(game_id)


def surrend(game_type, game_id, user):
    game_class = get_class(game_type)
    game_class.surrend(game_id, user)


def try_finish_game_by_undertime(game_type, game_id):
    game_class = get_class(game_type)
    try:
        game_class.update_times(game_id)
        game_class.finish_game_by_undertime(game_id)
    except:
        return


def get_finish_score(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.get_finish_scores(game_id)


def set_status_waiting(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.set_status_waiting(game_id)


def ping_game(game_type, game_id):
    for user in get_all_players(game_type, game_id):
        mark_active(game_type, game_id, user, False)


def add_inactive_ping(game_type, game_id, user):
    print(f'add inactive ping to {user}')
    game_class = get_class(game_type)
    game_class.add_inactive_ping(game_id, user)


def debug_info(game_type, game_id):
    game_class = get_class(game_type)
    game_class.debug_info(game_id)
