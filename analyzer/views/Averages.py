import json

import numpy as np
import scipy.cluster as cluster
from sklearn.cluster import KMeans
import scipy.stats as ss
import pickle

import analysis
import database
import enums
import util

logger = util.Logger(__name__)


class AverageAggression:
    def on_get(self, req, resp):
        logger.info("GET /average/aggression")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        stats = {
            "kp": [], "fw_kills": [], "positioning": [], "ganking": [], "aggression": 0
        }

        for game in games:
            team_kills = database.select_kill_timeline(conn=conn, game_id=game["gameid"], team_id=game["s1_teamid"])
            p1_frames = database.select_participant_frames(conn=conn, participant_id=game["s1_participantid"])
            frames = database.select_game_frames(conn=conn, game_id=game["gameid"])
            kills = database.select_all_kill_timeline(conn=conn, game_id=game["gameid"])

            # Kill Participation
            stats["kp"].append(analysis.base_analysis.kill_participation(
                participant=game["s1_participantid"],
                kills=team_kills,
            ))
            stats["fw_kills"].append(analysis.aggression.forward_kills(
                participant=game["s1_participantid"],
                kills=team_kills
            ))
            stats["positioning"].append(analysis.aggression.positioning(
                team_id=game["s1_teamid"],
                frames=p1_frames
            ))
            stats["ganking"].append(analysis.aggression.ganking(
                participant=game["s1_participantid"],
                role=util.get_canonic_lane(lane=game["s1_lane"], role=game["s1_role"]),
                frames=frames,
                kills=kills
            ))

        stats["kp"] = np.nanmean(np.array(stats["kp"]))
        stats["fw_kills"] = np.nanmean(np.array(stats["fw_kills"]))
        stats["positioning"] = np.nanmean(np.array(stats["positioning"]))
        stats["ganking"] = np.nanmean(np.array(stats["ganking"]))

        stats["aggression"] = analysis.aggression.aggression(stats["kp"], stats["fw_kills"], stats["positioning"],
                                                             stats["ganking"])

        resp.body = json.dumps(stats)


class AverageBasics:
    def on_get(self, req, resp):
        logger.info("GET /average/aggression")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        wr = analysis.base_analysis.win_rate(games)

        kda = {"kills": 0, "deaths": 0, "assists": 0}
        cs = 0
        gold_diff = {"overall": [], "early": [], "mid": [], "late": []}

        for game in games:
            stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            kda["kills"] += stats.kills
            kda["deaths"] += stats.deaths
            kda["assists"] += stats.assists

            cs += stats.total_minions_killed

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
                    gold_diff["overall"].append(p1_gold_diff["overall"])
                    gold_diff["early"].append(p1_gold_diff["early"])
                    gold_diff["mid"].append(p1_gold_diff["mid"])
                    gold_diff["late"].append(p1_gold_diff["late"])

        gold_diff["overall"] = np.nanmean(np.array(gold_diff["overall"]))
        gold_diff["early"] = np.nanmean(np.array(gold_diff["early"]))
        gold_diff["mid"] = np.nanmean(np.array(gold_diff["mid"]))
        gold_diff["late"] = np.nanmean(np.array(gold_diff["late"]))

        resp.body = json.dumps({
            "win_rate": wr,
            "kda": analysis.base_analysis.avg_kda(kda["kills"], kda["deaths"], kda["assists"]),
            "cs": cs / len(games),
            "gold_diff": gold_diff,
        })


class MillionaireAverage:
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


class AverageWinRate:
    def on_get(self, req, resp):
        """Calculates classification model for Millionaire class."""
        logger.info("GET /average/win-rate")
        conn = database.get_connection()

        summoners = database.select_all_summoners(conn=conn)
        rates = []

        for summoner in summoners:
            games = database.select_summoner_games(conn=conn, account_id=summoner["accountid"])
            if len(games) > 2:
                wr = analysis.base_analysis.win_rate(games)
                rates.append(wr)

        resp.body = json.dumps({
            "wr": np.nanmean(rates)
        })
