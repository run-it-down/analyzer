import json

import analysis
import database
import util

logger = util.Logger(__name__)


class ChampionCombinations:
    def on_get(self, req, resp):
        logger.info('GET /combinations/champions')
        params = req.params
        conn = database.get_connection()

        s1 = database.select_summoner(conn, summoner_name=params["summoner1"])
        s2 = database.select_summoner(conn, summoner_name=params["summoner2"])
        comb = analysis.combinations.team_champions(s1, s2, conn)
        resp.body = json.dumps(comb)
