import json
import pickle

import numpy as np
import scipy.stats as ss

import analysis
import database
import enums
import util

logger = util.Logger(__name__)


class Millionaire:
    def on_get(self, req, resp):
        logger.info("GET /average/aggression")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        values = {summoner1.name: [], summoner2.name: []}
        for game in common_games:
            p1_stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            p2_stats = database.select_stats(conn=conn, statid=game["s2_statid"])
            team_gold = database.select_team_gold(conn=conn, team_id=game["s1_teamid"], game_id=game["gameid"])

            p1_gold_earned = analysis.base_analysis.gold_share(p1_stats.gold_earned, team_gold=team_gold[0]["gold"])
            p2_gold_earned = analysis.base_analysis.gold_share(p2_stats.gold_earned, team_gold=team_gold[0]["gold"])

            p1_opponent = database.select_opponent(
                conn=conn,
                participant_id=game["s1_participantid"],
                game_id=game["gameid"],
                position=(game["s1_lane"], game["s1_role"])
            )
            p2_opponent = database.select_opponent(
                conn=conn,
                participant_id=game["s2_participantid"],
                game_id=game["gameid"],
                position=(game["s2_lane"], game["s2_role"])
            )
            if p1_opponent is None:
                continue
            if p2_opponent is None:
                continue
            p1_frames = database.select_participant_frames(conn=conn, participant_id=game["s1_participantid"])
            p1_opponent_frames = database.select_participant_frames(conn=conn,
                                                                    participant_id=p1_opponent.participant_id)
            p2_frames = database.select_participant_frames(conn=conn, participant_id=game["s2_participantid"])
            p2_opponent_frames = database.select_participant_frames(conn=conn,
                                                                    participant_id=p2_opponent.participant_id)
            p1_gold_diff = analysis.base_analysis.gold_diff(frames=p1_frames, opponent_frames=p1_opponent_frames)
            p2_gold_diff = analysis.base_analysis.gold_diff(frames=p2_frames, opponent_frames=p2_opponent_frames)

            values[summoner1.name].append(
                [ss.norm.cdf(p1_gold_earned, enums.GoldShare.MU, enums.GoldShare.SIG),
                 ss.norm.cdf(p1_gold_diff["overall"], enums.GoldDiffAll.MU, enums.GoldDiffAll.SIG)])
            values[summoner2.name].append(
                [ss.norm.cdf(p2_gold_earned, enums.GoldShare.MU, enums.GoldShare.SIG),
                 ss.norm.cdf(p2_gold_diff["overall"], enums.GoldDiffAll.MU, enums.GoldDiffAll.SIG)])

        model = pickle.load(open('./kmeans_millionaire.pkl', 'rb'))

        p1_avg = np.average(values[summoner1.name], axis=0)
        p2_avg = np.average(values[summoner2.name], axis=0)

        centres = model.cluster_centers_.tolist()
        resp.body = json.dumps({
            "cluster_centre": {
                "0": centres[0],
                "1": centres[1]
            },
            summoner1.name: {
                "isClass": bool(model.predict([p1_avg])),
                "value": p1_avg.tolist()
            },
            summoner2.name: {
                "isClass": bool(model.predict([p2_avg])),
                "value": p2_avg.tolist()
            }
        })


class MatchType:
    def on_get(self, req, resp):
        logger.info("GET /average/aggression")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        wr = analysis.base_analysis.win_rate(games=common_games)
        if wr >= enums.WinRate.MU + enums.WinRate.SIG:
            resp.body = json.dumps({
                "type": "Perfect Match"
            })
        elif wr <= enums.WinRate.MU - enums.WinRate.SIG:
            resp.body = json.dumps({
                "type": "Mismatch"
            })
        else:
            resp.body = json.dumps({
                "type": "Average Fit"
            })
