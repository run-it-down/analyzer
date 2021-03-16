import json

import analysis
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
        average_gold_diff = analysis.base_analysis.get_gold_difference(gold_stats)

        def win_to_int(win: str): return 1 if win == 'Win' else 0

        positions = transformer.transform_positions(common_games, conn)
        analysis.aggression.positioning(positions,
                                        [(game["s1_role"], game["s1_lane"], game["s1_teamid"], win_to_int(game["win"]))
                                         for game in common_games],
                                        "late")

        kill_information = transformer.transform_kills(common_games, conn)
        kp = analysis.base_analysis.get_kp_per_game(kill_information)
        kp_avg = analysis.base_analysis.get_average_kp(kp)

        kill_timeline = transformer.transform_kill_timeline(common_games, conn)
        kp_per_state = analysis.aggression.kp_per_state(kill_timeline)
        avg_kp_per_state = analysis.aggression.avg_kp_per_state(kp_per_state)

        resp.body = json.dumps(average_gold_diff)
