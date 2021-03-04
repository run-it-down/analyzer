import json

import database
import util
import transformer

logger = util.Logger(__name__)


class Aggression:
    def on_get(self, req, resp):
        logger.info('GET /aggression')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        gold_stats = transformer.transform_gold_diff(common_games, conn)

        resp.body = json.dumps([])
