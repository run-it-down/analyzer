""" Calculate metrics which correlate to 'combinations'. """
from collections import defaultdict

import database
import model


def team_champions(s1: model.Summoner, s2: model.Summoner, conn):
    """
    Calculate win rates of champion combinations, when summoner 1 and 2 were on the same team

    :param s1: summoner 1
    :param s2: summoner 2
    :param conn: database connection
    :return: array of champion combinations and their win rate
    """
    # initialize dictionary
    champ_matrix = defaultdict(lambda: {'wins': 0, 'total': 0, 'avg': 0.0})
    win_value = {'Win': 1, 'Fail': 0}

    # get statistics for common games of summoner 1 and summoner 2
    game_stats = database.select_common_game_stats(conn=conn, s1=s1, s2=s2)
    # iterate over every 2nd entry aka each game and aggregate wins and total games

    for game_stat in game_stats:
        p1_champion = database.select_champion_name_id(champ_id=game_stat["s1_champion"], conn=conn)
        p2_champion = database.select_champion_name_id(champ_id=game_stat["s2_champion"], conn=conn)

        champ_set = (p1_champion['name'], p2_champion['name'])
        champ_matrix[champ_set]['total'] += 1
        champ_matrix[champ_set]['wins'] += win_value[game_stat['win']]

    # calculate win rate and reformat to array of dictionaries
    result = []
    for champ_comb, comb_stats in champ_matrix.items():
        combo = {
            "summoner1": champ_comb[0],
            "summoner2": champ_comb[1],
            "wins": comb_stats['wins'],
            "total": comb_stats['total'],
            "win_rate": 0.0
        }
        try:
            combo['win_rate'] = combo['wins'] / combo['total']
        except ZeroDivisionError:
            # just a precaution, although this should never happen
            combo['win_rate'] = -1.
        result.append(combo)
    # sort result after win rate (descending)
    return sorted(result, key=lambda k: k['win_rate'], reverse=True)
