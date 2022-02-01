from games.classes.game import ONGOING


WAR = 'war'
MAKAO = 'makao'
WAR_BASE_CONFIG = {
    'game_parameters':
    {
        'time_per_player': 120,
        'max_players': 2,
        'rounds': 1,
        'is_ranked': True,
        'cards_on_hand': 3,
    }
}
GAMES_CONFIG_PATH = 'games/games_configs/'
FINISHED = 'finished'
ONGOING = 'ongoing'
WAITING = 'waiting'
SURRENDER = 'surrender'