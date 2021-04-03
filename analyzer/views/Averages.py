import json

import numpy as np

import analysis
import database
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


class AverageCs:
    def on_get(self, req, resp):
        logger.info("GET /average/aggression")
        conn = database.get_connection()
        games = database.select_all_games(conn=conn)

        shares = []
        cs_diff = {"overall": [], "early": [], "mid": [], "late": []}

        for game in games:
            stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            team_cs = database.select_team_cs(conn=conn, team_id=game["s1_teamid"], game_id=game["gameid"])

            e_jgl = stats.neutral_minions_killed_enemy_jungle if stats.neutral_minions_killed_enemy_jungle is not None else 0
            t_jgl = stats.neutral_minions_killed_team_jungle if stats.neutral_minions_killed_team_jungle is not None else 0

            cs = stats.total_minions_killed + e_jgl + t_jgl
            if team_cs[0]["cs"] is None:
                continue
            cs_share = analysis.base_analysis.cs_share(cs, team_cs[0]["cs"])
            shares.append(cs_share)

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
                    cs_diff["overall"].append(p1_cs_diff["overall"])
                    cs_diff["early"].append(p1_cs_diff["early"])
                    cs_diff["mid"].append(p1_cs_diff["mid"])
                    cs_diff["late"].append(p1_cs_diff["late"])

        resp.body = json.dumps({
            "cs_share": np.nanmean(shares),
            "cs_diff": {
                "overall": np.nanmean(cs_diff["overall"]),
                "early": np.nanmean(cs_diff["early"]),
                "mid": np.nanmean(cs_diff["mid"]),
                "late": np.nanmean(cs_diff["late"]),
            }
        })
