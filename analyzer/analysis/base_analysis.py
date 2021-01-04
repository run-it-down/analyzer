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
        "total": 0,
        "totalGames": len(stat_ids),
        "lanes": {
            "top": {
                "avg": 0, "total": 0, "totalGames": 0,
            },
            "jgl": {
                "avg": 0, "total": 0, "totalGames": 0,
            },
            "mid": {
                "avg": 0, "total": 0, "totalGames": 0,
            },
            "adc": {
                "avg": 0, "total": 0, "totalGames": 0,
            },
            "sup": {
                "avg": 0, "total": 0, "totalGames": 0,
            },
        },
    }
    for stat_id in stat_ids:
        stat = database.select_stats(conn=conn, statid=stat_id)
        participant = database.select_participant_from_stat(conn=conn, stat=stat)
        cs["total"] += stat.total_minions_killed

        if participant.lane == "TOP":
            cs["lanes"]["top"]["total"] += stat.total_minions_killed
            cs["lanes"]["top"]["totalGames"] += 1
        elif participant.lane == "JUNGLE":
            cs["lanes"]["jgl"]["total"] += stat.total_minions_killed
            cs["lanes"]["jgl"]["totalGames"] += 1
        elif participant.lane == "MID" or participant.lane == "MIDDLE":
            cs["lanes"]["mid"]["total"] += stat.total_minions_killed
            cs["lanes"]["mid"]["totalGames"] += 1
        elif participant.lane == "BOT" or participant.lane == "BOTTOM" or participant.role == "DUO_CARRY":
            cs["lanes"]["adc"]["total"] += stat.total_minions_killed
            cs["lanes"]["adc"]["totalGames"] += 1
        elif participant.lane == "BOT" or participant.lane == "BOTTOM" or participant.role == "DUO_SUPPORT":
            cs["lanes"]["sup"]["total"] += stat.total_minions_killed
            cs["lanes"]["sup"]["totalGames"] += 1

    try:
        cs["avg"] = cs["total"] / cs["totalGames"]
    except ZeroDivisionError:
        cs["avg"] = -1

    for lane in cs["lanes"].keys():
        try:
            cs["lanes"][lane]["avg"] = cs["lanes"][lane]["total"] / cs["lanes"][lane]["totalGames"]
        except ZeroDivisionError:
            cs["lanes"][lane]["avg"] = -1

    return cs
