import json

import analysis
import database
import util

logger = util.Logger(__name__)


class WinRate:
    def on_get(self, req, resp):
        logger.info('GET /winrate')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)
        wr = analysis.base_analysis.get_win_rate(common_games=common_games, conn=conn)

        resp.body = json.dumps({
            "win_rate": wr
        })


class KDA:
    def on_get(self, req, resp):
        logger.info('GET /kda')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner2'])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)
        kda = analysis.base_analysis.get_kda(common_games, conn=conn)

        resp.body = json.dumps({
            "games": len(common_games),
            "summoner1": {
                "name": summoner1.name,
                "kda": kda["summoner1"]
            },
            "summoner2": {
                "name": summoner2.name,
                "kda": kda["summoner2"]
            }
        })


class CreepScore:
    def on_get(self, req, resp):
        logger.info('GET /cs')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn, summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn, summoner_name=params['summoner2'])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)
        cs = analysis.base_analysis.get_creep_score(conn=conn, common_games=common_games)

        cs["summoner1"]["name"] = summoner1.name
        cs["summoner2"]["name"] = summoner2.name
        resp.body = json.dumps(cs)
