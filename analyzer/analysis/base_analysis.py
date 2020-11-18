import database
import model


def get_win_rate(summoner: model.Summoner, conn):
    stat_ids = database.select_stat_from_participant(conn=conn,
                                                     summoner=summoner)
    wins_total = 0
    for stat_id in stat_ids:
        stat = database.select_stats(conn=conn,
                                     statid=stat_id)
        wins_total += int(stat.win)

    return wins_total / len(stat_ids)


def get_kda(summoner: model.Summoner, conn):
    """
    Calculate the kills and assists to deaths ratio for a given summoner.

    KDA = (sum(kills) + sum(assists)) / sum(deaths)

    :param summoner: given summoner
    :param conn: database connection
    :return: calculated kda, either >= 0 or -1 (perfect KDA)
    """
    stat_ids = database.select_stat_from_participant(conn, summoner=summoner)
    kda = {
        "kills": 0,
        "deaths": 0,
        "assists": 0
    }
    for stat_id in stat_ids:
        stat = database.select_stats(conn=conn, statid=stat_id)
        kda["kills"] += stat.kills
        kda["deaths"] += stat.deaths
        kda["assists"] += stat.assists

    try:
        return (kda["kills"] + kda["assists"]) / kda["deaths"]
    except ZeroDivisionError:
        return -1


def get_creep_score(summoner: model.Summoner, conn):
    stat_ids = database.select_stat_from_participant(conn, summoner=summoner)
    cs = {
        "avg": 0,
        "lanes": {
            "top": 0,
            "jgl": 0,
            "mid": 0,
            "adc": 0,
            "sup": 0,
        },
    }
    for stat_id in stat_ids:
        stat = database.select_stats(conn=conn, statid=stat_id)
        cs["avg"] += stat.totalMinionsKilled

    try:
        cs["avg"] = cs["avg"] / len(stat_ids)
    except ZeroDivisionError:
        cs["avg"] = -1
    return cs
