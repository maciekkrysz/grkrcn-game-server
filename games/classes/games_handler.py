import json
from django.utils.functional import partition
from .makao import Makao
from .war import War
from ..models import GameType, Game, Participation, Move
from asgiref.sync import async_to_sync
from ..rabbimq.sender import send_ranking_request, send_game_data


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


def get_all_user_ids(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.get_all_user_ids(game_id)


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


def current_user_id(game_type, game_id):
    username = current_username(game_type, game_id)
    game_class = get_class(game_type)
    return game_class.get_id_from_nickname(game_id, username)


def possible_moves(game_type, game_id, user):
    game_class = get_class(game_type)
    return game_class.possible_moves(game_id, user)


def start_counting_timeout(game_type, game_id, user):
    game_class = get_class(game_type)
    return game_class.start_counting_timeout(game_id, user)


def make_move(game_type, game_id, user, action, move):
    game_class = get_class(game_type)
    id = game_class.get_id_from_nickname(game_id, user)

    if game_class.make_move(game_id, user, action, move):
        if move is None:
            move = ''
        modeltype = GameType.objects.get_typegame_lower_nospecial(game_type)
        modelpartic = Participation.objects.get_by_userid_gametype(
            id, modeltype).last()
        Move.objects.create(participation=modelpartic,
                            action=action, move=move)
        return True
    if game_class.is_game_finished(game_id):
        game_class.try_finish_game(game_id)
    return False


def is_game_ongoing(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.is_game_ongoing(game_id)


def is_game_finished(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.is_game_finished(game_id)


def surrender(game_type, game_id, user):
    game_class = get_class(game_type)
    game_class.surrender(game_id, user)


def try_finish_game_by_undertime(game_type, game_id):
    game_class = get_class(game_type)
    try:
        game_class.update_times(game_id)
        game_class.finish_game_by_undertime(game_id)
    except:
        return


def get_finish_score(game_type, game_id):
    game_class = get_class(game_type)
    scores = game_class.get_finish_scores(game_id)
    send_scores_to_rabbitmq(game_type, game_id, scores)
    return scores


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


def was_scores_sent(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.was_scores_sent(game_id)


def any_update_in_game(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.any_update_in_game(game_id)


def any_userscores_to_send(game_type, game_id):
    game_class = get_class(game_type)
    return game_class.any_userscores_to_send(game_id)


def send_scores_to_rabbitmq(game_type, game_id, scores):
    game_class = get_class(game_type)
    jsondata = {
        'game_type': game_type,
        'players': {}
    }
    try:
        if not was_scores_sent(game_type, game_id):
            for endtype in scores['scores'].items():
                for nickname in endtype[1]:
                    userid = game_class.get_id_from_nickname(game_id, nickname)
                    jsondata['players'][userid] = game_class.get_user_score(
                        game_id, nickname)
                    jsondata['players'][userid]['score'] = endtype[0]
                    if jsondata['players'][userid]['score'] == 'lose':
                        jsondata['players'][userid]['points'] = -5
            send_game_data(jsondata)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")


def request_for_ranking(game_type, game_id, players_id):
    jsondata = {
        'game_type': game_type,
        'game_id': game_id,
        'players': players_id
    }
    print(jsondata)
    send_ranking_request(jsondata)


def debug_info(game_type, game_id):
    game_class = get_class(game_type)
    game_class.debug_info(game_id)
