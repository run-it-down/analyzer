import json
import pickle

import numpy as np
import scipy.stats as ss
from sklearn.cluster import KMeans

import analysis
import database
import enums
import util

logger = util.Logger(__name__)


class MillionaireModel:
    def on_get(self, req, resp):
        """Calculates classification model for Millionaire class."""
        logger.info("GET /average/aggression")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        values = []

        for game in games:
            stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            team_gold = database.select_team_gold(conn=conn, team_id=game["s1_teamid"], game_id=game["gameid"])

            gold_earned = analysis.base_analysis.gold_share(stats.gold_earned, team_gold=team_gold[0]["gold"])

            p1_frames = database.select_participant_frames(conn=conn, participant_id=game["s1_participantid"])
            p1_opponent = database.select_opponent(
                conn=conn,
                participant_id=game["s1_participantid"],
                game_id=game["gameid"],
                position=(game["s1_lane"], game["s1_role"])
            )
            if p1_opponent is not None:
                p1_opponent_frames = database.select_participant_frames(conn=conn,
                                                                        participant_id=p1_opponent.participant_id)
                if len(p1_opponent_frames) > 0:
                    p1_gold_diff = analysis.base_analysis.gold_diff(frames=p1_frames,
                                                                    opponent_frames=p1_opponent_frames)

                    values.append([ss.norm.cdf(gold_earned, enums.GoldShare.MU, enums.GoldShare.SIG),
                                   ss.norm.cdf(p1_gold_diff["overall"], enums.GoldDiffAll.MU, enums.GoldDiffAll.SIG)])

        arr = np.reshape(np.array(values)[np.logical_not(np.isnan(values))], (-1, 2))
        means = KMeans(n_clusters=2, random_state=0)
        cluster_arr = means.fit(arr)
        # fit needs to be done, so we can use this model later on in other analysis steps
        pickle.dump(means, open('./kmeans_millionaire.pkl', 'wb'))

        centres = means.cluster_centers_.tolist()
        resp.body = json.dumps({
            "0": centres[0],
            "1": centres[1]
        })


class MurderousDuoModel:
    def on_get(self, req, resp):
        """Calculates classification model for Millionaire class."""
        logger.info("GET /average/aggression")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        values = []
        for game in games:
            stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            team_kills = database.select_kill_timeline(conn=conn, game_id=game["gameid"], team_id=game["s1_teamid"])

            kp = analysis.base_analysis.ss_kill_participation(game["s1_participantid"], team_kills)
            kda = analysis.base_analysis.game_kda({
                "kills": stats.kills, "deaths": stats.deaths, "assists": stats.assists
            })

            if not np.isnan(kp) and not np.isnan(kda):
                print(kp, kda)
                values.append([ss.norm.cdf(kp, enums.KP.MU, enums.KP.SIG), ss.expon.cdf(kda, scale=enums.KDA.MU)])
        means = KMeans(n_clusters=2, random_state=0)

        cluster_arr = means.fit(np.array(values))
        # fit needs to be done, so we can use this model later on in other analysis steps
        pickle.dump(means, open('./kmeans_murderous.pkl', 'wb'))

        centres = means.cluster_centers_.tolist()
        resp.body = json.dumps({
            "0": centres[0],
            "1": centres[1]
        })
