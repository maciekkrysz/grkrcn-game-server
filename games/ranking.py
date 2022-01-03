WIN = 1
DRAW = 0.5
LOSE = 0

def expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def elo(rank_start, exp_score, score, k):
    return rank_start + k * (score - exp_score)


def calculate_elo(player_rank:int, opponent_ranks:list, score:int, k:int):
    """
    p_rank = 1300
    oppon = [1100, 1200]
    print(calculate_elo(p_rank, oppon, 2, 10)) # 1306.0018807354916
    """
    exp_score = 0
    for opp_rank in opponent_ranks:
        exp_score += expected_score(player_rank, opp_rank)
    
    return elo(player_rank, exp_score, score, k)


