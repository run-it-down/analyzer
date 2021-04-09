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

                    earned = ss.norm.cdf(gold_earned, enums.GoldShare.MU, enums.GoldShare.SIG)
                    diff = ss.norm.cdf(p1_gold_diff["overall"], enums.GoldDiffAll.MU, enums.GoldDiffAll.SIG)
                    if earned == 0 or diff == 0 or np.isnan(earned) or np.isnan(diff):
                        continue
                    values.append([earned, diff])

        arr = np.reshape(np.array(values)[np.logical_not(np.isnan(values))], (-1, 2))
        means = KMeans(n_clusters=2, random_state=0)
        cluster_arr = means.fit(arr)
        # fit needs to be done, so we can use this model later on in other analysis steps
        pickle.dump(means, open('/analyzer/kmeans_millionaire.pkl', 'wb'))

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
                kp = ss.norm.cdf(kp, enums.KP.MU, enums.KP.SIG)
                kda = ss.expon.cdf(kda, scale=enums.KDA.MU)
                if kp == 0 or kda == 0 or np.isnan(kp) or np.isnan(kda):
                    continue
                values.append([kp, kda])
        means = KMeans(n_clusters=2, random_state=0)

        cluster_arr = means.fit(np.array(values))
        # fit needs to be done, so we can use this model later on in other analysis steps
        pickle.dump(means, open('/analyzer/kmeans_murderous.pkl', 'wb'))

        centres = means.cluster_centers_.tolist()
        resp.body = json.dumps({
            "0": centres[0],
            "1": centres[1]
        })


class FarmerType:
    def on_get(self, req, resp):
        """Calculates classification model for Farmer class."""
        logger.info("GET /model/farmer-type")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        values = []
        for game in games:
            stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            team_cs = database.select_team_cs(conn=conn, team_id=game["s1_teamid"], game_id=game["gameid"])

            e_jgl = stats.neutral_minions_killed_enemy_jungle if stats.neutral_minions_killed_enemy_jungle is not None else 0
            t_jgl = stats.neutral_minions_killed_team_jungle if stats.neutral_minions_killed_team_jungle is not None else 0

            if team_cs[0]["cs"] is None:
                continue
            cs = stats.total_minions_killed + e_jgl + t_jgl
            cs_share = analysis.base_analysis.cs_share(cs, team_cs[0]["cs"])

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
                    p1_cs_diff = analysis.base_analysis.cs_diff(frames=p1_frames,
                                                                opponent_frames=p1_opponent_frames)

                    share = ss.norm.cdf(cs_share, enums.CreepShare.MU, enums.CreepShare.SIG)
                    diff = ss.norm.cdf(p1_cs_diff["overall"], enums.CSD.MU, enums.CSD.SIG)
                    if share == 0 or diff == 0 or np.isnan(share) or np.isnan(diff):
                        continue
                    values.append([share, diff])

        means = KMeans(n_clusters=2, random_state=0)
        cluster_arr = means.fit(np.array(values))
        # fit needs to be done, so we can use this model later on in other analysis steps
        pickle.dump(means, open('/analyzer/kmeans_farmers.pkl', 'wb'))

        centres = means.cluster_centers_.tolist()
        resp.body = json.dumps({
            "0": centres[0],
            "1": centres[1]
        })


class TacticianModel:
    def on_get(self, req, resp):
        logger.info("GET /average/aggression")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        values = []
        for game in games:
            frames = database.select_game_frames(conn=conn, game_id=game["gameid"])
            kills = database.select_all_kill_timeline(conn=conn, game_id=game["gameid"])
            objectives = database.select_objectives(conn=conn, game_id=game["gameid"])

            t = analysis.classification.tactician(game["s1_participantid"], game["s1_teamid"], kills, objectives,
                                                  frames, conn)
            if np.isnan(t["worthness"]):
                continue
            if np.isnan(t["objectives"]):
                continue
            worthness = ss.norm.cdf(t["worthness"], enums.Worthness.MU, enums.Worthness.SIG)
            objectives = ss.expon.pdf(t["objectives"], scale=enums.KillObjectives.MU)
            if worthness == 0 or np.isnan(worthness) or objectives == 0 or np.isnan(objectives):
                continue
            values.append([worthness, objectives])

        means = KMeans(n_clusters=2, random_state=0)
        cluster_arr = means.fit(np.array(values))
        # fit needs to be done, so we can use this model later on in other analysis steps
        pickle.dump(means, open('/analyzer/kmeans_tactician.pkl', 'wb'))

        centres = means.cluster_centers_.tolist()
        resp.body = json.dumps({
            "0": centres[0],
            "1": centres[1]
        })
