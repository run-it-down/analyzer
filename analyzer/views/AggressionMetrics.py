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
        gold_diff = analysis.base_analysis.get_gold_diff_state(gold_stats)

        def win_to_int(win: str): return 1 if win == 'Win' else 0

        positions = transformer.transform_positions(common_games, conn)
        p1_positioning = analysis.aggression.positioning(positions["p1"],
                                                         [(game["s1_role"], game["s1_lane"], game["s1_teamid"],
                                                           win_to_int(game["win"])) for game in common_games])
        p2_positioning = analysis.aggression.positioning(positions["p2"],
                                                         [(game["s2_role"], game["s2_lane"], game["s2_teamid"],
                                                           win_to_int(game["win"])) for game in common_games])
        positioning = {"p1": p1_positioning, "p2": p2_positioning}

        kill_timeline = transformer.transform_kill_timeline(common_games, conn)
        kp_per_state = analysis.aggression.kp_per_state(kill_timeline)

        cs_diffs = transformer.transform_cs_diff(games=common_games, conn=conn)
        csd_per_state = analysis.base_analysis.get_cs_diff_state(cs_diffs=cs_diffs)

        kda_per_state = transformer.transform_kda_timeline(common_games, conn)
        norm_kda_per_state = {
            "p1": {
                "early": util.normalize_arr(kda_per_state["p1"]["early"]),
                "mid": util.normalize_arr(kda_per_state["p1"]["mid"]),
                "late": util.normalize_arr(kda_per_state["p1"]["late"]),
            },
            "p2": {
                "early": util.normalize_arr(kda_per_state["p2"]["early"]),
                "mid": util.normalize_arr(kda_per_state["p2"]["mid"]),
                "late": util.normalize_arr(kda_per_state["p2"]["late"]),
            }
        }

        aggression = analysis.aggression.aggression(gold_diff=gold_diff, position_ratio=positioning, kps=kp_per_state,
                                                    csds=csd_per_state, kda=norm_kda_per_state)

        resp.body = json.dumps(aggression)
