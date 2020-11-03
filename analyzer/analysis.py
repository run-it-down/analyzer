try:
    import database
    import model
except ModuleNotFoundError:
    print('common package not in python path')


def get_winrate(summoner: model.Summoner,
                conn,
                ):
    stat_ids = database.select_stat_from_participant(conn=conn,
                                                     summoner=summoner,
                                                     )
    wins_total = 0
    for stat_id in stat_ids:
        stat = database.select_stats(conn=conn,
                                     statid=stat_id)
        wins_total += int(stat.win)

    return wins_total / len(stat_ids)
