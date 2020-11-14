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
        summoner = database.select_summoner(conn=conn,
                                            summoner_name=params['summoner'])
        wr = analysis.base_analysis.get_win_rate(summoner=summoner, conn=conn)
        resp.body = json.dumps({
            "win_rate": wr
        })


class KDA:
    def on_get(self, req, resp):
        logger.info('GET /kda')
        params = req.params
        conn = database.get_connection()
        summoner = database.select_summoner(conn=conn,
                                            summoner_name=params['summoner'])
        kda = analysis.base_analysis.get_kda(summoner=summoner, conn=conn)
        resp.body = json.dumps({
            "kda": kda
        })


class CreepScore:
    def on_get(self, req, resp):
        logger.info('GET /kda')
        params = req.params
        conn = database.get_connection()
        summoner = database.select_summoner(conn=conn, summoner_name=params['summoner'])
        cs = analysis.base_analysis.get_creep_score(conn=conn, summoner=summoner)
        resp.body = json.dumps(cs)
