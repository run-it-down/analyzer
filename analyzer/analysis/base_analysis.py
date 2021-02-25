import database


def get_win_rate(common_games, conn):
    wins_total = 0
    for game in common_games:
        stat = database.select_stats(conn=conn, statid=game[3])
        wins_total += int(stat.win)

    return wins_total / len(common_games)


def get_kda(common_games, conn):
    """
    Calculate the kills and assists to deaths ratio for a given summoner.

    KDA = (sum(kills) + sum(assists)) / sum(deaths)

    :param common_games:
    :param conn: database connection
    :return: calculated kda, either >= 0 or -1 (perfect KDA)
    """
    kda_object = {
        "summoner1": {
            "kills": 0,
            "deaths": 0,
            "assists": 0
        },
        "summoner2": {
            "kills": 0,
            "deaths": 0,
            "assists": 0
        }
    }

    for game in common_games:
        stat_summoner1 = database.select_stats(conn=conn, statid=game[3])
        stat_summoner2 = database.select_stats(conn=conn, statid=game[6])
        kda_object["summoner1"]["kills"] += stat_summoner1.kills
        kda_object["summoner1"]["deaths"] += stat_summoner1.deaths
        kda_object["summoner1"]["assists"] += stat_summoner1.assists
        kda_object["summoner2"]["kills"] += stat_summoner2.kills
        kda_object["summoner2"]["deaths"] += stat_summoner2.deaths
        kda_object["summoner2"]["assists"] += stat_summoner2.assists

    kda = {}
    try:
        kda["summoner1"] = (kda_object["summoner1"]["kills"] + kda_object["summoner1"]["assists"]) / \
                           kda_object["summoner1"]["deaths"]
    except ZeroDivisionError:
        kda_object["summoner1"] = -1

    try:
        kda["summoner2"] = (kda_object["summoner2"]["kills"] + kda_object["summoner2"]["assists"]) / \
                           kda_object["summoner2"]["deaths"]
    except ZeroDivisionError:
        kda["summoner2"] = -1

    return kda


def get_creep_score(common_games, conn):
    cs = {
        "summoner1": {
            "avg": 0.,
            "lanes": {"TOP": 0, "JUNGLE": 0, "MIDDLE": 0, "ADC": 0, "SUPPORT": 0}
        },
        "summoner2": {
            "avg": 0.,
            "lanes": {"TOP": 0, "JUNGLE": 0, "MIDDLE": 0, "ADC": 0, "SUPPORT": 0}
        }
    }
    counter = {
        "summoner1": {"TOP": 1, "JUNGLE": 1, "MIDDLE": 1, "ADC": 1, "SUPPORT": 1},
        "summoner2": {"TOP": 1, "JUNGLE": 1, "MIDDLE": 1, "ADC": 1, "SUPPORT": 1}
    }

    for index, game in enumerate(common_games):
        stat_summoner1 = database.select_stats(conn=conn, statid=game[3])
        stat_summoner2 = database.select_stats(conn=conn, statid=game[6])
        participant1 = database.select_participant(conn=conn, participant_id=game[2])
        participant2 = database.select_participant(conn=conn, participant_id=game[5])

        cs["summoner1"]["avg"] += (stat_summoner1.total_minions_killed - cs["summoner1"]["avg"]) / (index + 1)
        cs["summoner2"]["avg"] += (stat_summoner2.total_minions_killed - cs["summoner2"]["avg"]) / (index + 1)

        lane = participant1.lane
        if participant1.lane in ("BOTTOM", "NONE"):
            if participant1.role == "DUO_SUPPORT":
                lane = "SUPPORT"
            else:
                lane = "ADC"
        cs["summoner1"]["lanes"][lane] += (stat_summoner1.total_minions_killed - cs["summoner1"]["lanes"][lane]) / counter["summoner1"][lane]

        lane = participant2.lane
        if participant2.lane in ("BOTTOM", "NONE"):
            if participant2.role == "DUO_SUPPORT":
                lane = "SUPPORT"
            else:
                lane = "ADC"
        cs["summoner2"]["lanes"][lane] += (stat_summoner2.total_minions_killed - cs["summoner2"]["lanes"][lane]) / counter["summoner2"][lane]

    return cs
