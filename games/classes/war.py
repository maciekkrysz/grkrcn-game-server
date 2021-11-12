from .game import Game
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
    def possible_moves(game_id, player):
        pass


# if War.check_create_game(temp_json):
#     print(War.create_game(temp_json))
