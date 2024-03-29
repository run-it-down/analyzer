import ast
import json
import math
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
        logger.info("GET /classification/millionaire")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        values = {summoner1.name: [], summoner2.name: []}
        p1_raw = []
        p2_raw = []
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

            p1_share = ss.norm.cdf(p1_gold_earned, enums.GoldShare.MU, enums.GoldShare.SIG)
            p1_gd = ss.norm.cdf(p1_gold_diff["overall"], enums.GoldDiffAll.MU, enums.GoldDiffAll.SIG)
            p2_share = ss.norm.cdf(p2_gold_earned, enums.GoldShare.MU, enums.GoldShare.SIG)
            p2_gd = ss.norm.cdf(p2_gold_diff["overall"], enums.GoldDiffAll.MU, enums.GoldDiffAll.SIG)

            values[summoner1.name].append([p1_share, p1_gd])
            values[summoner2.name].append([p2_share, p2_gd])

        model = pickle.load(open('/analyzer/kmeans_millionaire.pkl', 'rb'))

        p1_avg = np.average(values[summoner1.name], axis=0)
        p2_avg = np.average(values[summoner2.name], axis=0)

        centres = model.cluster_centers_.tolist()
        resp.body = json.dumps({
            "cluster_centre": {
                "0": centres[0],
                "1": centres[1]
            },
            summoner1.name: {
                "isClass": not bool(model.predict([p1_avg])),
                "value": p1_avg.tolist()
            },
            summoner2.name: {
                "isClass": not bool(model.predict([p2_avg])),
                "value": p2_avg.tolist()
            },
            "raw": {
                summoner1.name: p1_raw,
                summoner2.name: p2_raw
            }
        })


class MatchType:
    def on_get(self, req, resp):
        logger.info("GET /classification/match-type")
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


class MurderousDuo:
    def on_get(self, req, resp):
        logger.info("GET /classification/murderous-duo")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        murderous_stats = {
            summoner1.name: {"kp": [], "kda": []},
            summoner2.name: {"kp": [], "kda": []}
        }
        p1_raw = []
        p2_raw = []
        for game in common_games:
            team_kills = database.select_kill_timeline(conn=conn, game_id=game["gameid"], team_id=game["s1_teamid"])
            p1_stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            p2_stats = database.select_stats(conn=conn, statid=game["s2_statid"])

            p1_kp = ss.norm.cdf(analysis.base_analysis.kill_participation(
                participant=game["s1_participantid"],
                kills=team_kills,
            ), enums.KP.MU, enums.KP.VAR)
            p2_kp = ss.norm.cdf(analysis.base_analysis.kill_participation(
                participant=game["s2_participantid"],
                kills=team_kills,
            ), enums.KP.MU, enums.KP.VAR)
            p1_kda = ss.expon.cdf(analysis.base_analysis.game_kda({
                "kills": p1_stats.kills, "deaths": p1_stats.deaths, "assists": p1_stats.assists
            }), scale=enums.KDA.MU)
            p2_kda = ss.expon.cdf(analysis.base_analysis.game_kda({
                "kills": p2_stats.kills, "deaths": p2_stats.deaths, "assists": p2_stats.assists
            }), scale=enums.KDA.MU)

            if np.isnan(p1_kp) or np.isnan(p1_kda) or np.isnan(p2_kp) or np.isnan(p2_kda):
                continue

            # Kill Participation
            murderous_stats[summoner1.name]["kp"].append(p1_kp)
            murderous_stats[summoner2.name]["kp"].append(p2_kp)
            murderous_stats[summoner1.name]["kda"].append(p1_kda)
            murderous_stats[summoner2.name]["kda"].append(p2_kda)

            p1_raw.append([p1_kp, p1_kda])
            p2_raw.append([p2_kp, p2_kda])

        murderous = analysis.classification.classify_murderous_duo(
            p1_kp=np.nanmean(murderous_stats[summoner1.name]["kp"]),
            p2_kp=np.nanmean(murderous_stats[summoner2.name]["kp"]),
            p1_kda=np.nanmean(murderous_stats[summoner1.name]["kda"]),
            p2_kda=np.nanmean(murderous_stats[summoner2.name]["kda"]),
        )

        resp.body = json.dumps({
            "cluster_centre": murderous["cluster_centre"],
            summoner1.name: murderous["1"],
            summoner2.name: murderous["2"],
            "raw": {
                summoner1.name: p1_raw,
                summoner2.name: p2_raw
            }
        })


class DuoType:
    def on_get(self, req, resp):
        logger.info("GET /classification/duo-type")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        arr_spent = []
        for game in common_games:
            p1_frames = database.select_participant_frames(conn=conn, participant_id=game["s1_participantid"])
            p2_frames = database.select_participant_frames(conn=conn, participant_id=game["s2_participantid"])

            together = 0
            for idx, p1_frame in enumerate(p1_frames):
                if p1_frame["position"] is None:
                    continue
                if p2_frames[idx]["position"] is None:
                    continue
                p1_pos = ast.literal_eval(p1_frame["position"])
                p2_pos = ast.literal_eval(p2_frames[idx]["position"])
                distance = abs(math.sqrt(math.pow(p1_pos[0] - p2_pos[0], 2) + math.pow(p1_pos[1] - p2_pos[1], 2)))

                if distance <= 1000:
                    together += 1
            try:
                spent_together = together / len(p1_frames)
            except ZeroDivisionError:
                spent_together = 0
            arr_spent.append(spent_together)

        time_spent = np.average(np.array(arr_spent))
        if time_spent >= 2 / 3:
            resp.body = json.dumps({
                "pct_spent_together": time_spent,
                "type": "Lovers"
            })
        elif time_spent <= 1 / 3:
            resp.body = json.dumps({
                "pct_spent_together": time_spent,
                "type": "Singles"
            })
        else:
            resp.body = json.dumps({
                "pct_spent_together": time_spent,
                "type": "Friends"
            })


class FarmerType:
    def on_get(self, req, resp):
        logger.info("GET /classification/duo-type")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        values = {summoner1.name: {"share": [], "csd": []}, summoner2.name: {"share": [], "csd": []}}
        p1_raw = []
        p2_raw = []
        for game in common_games:
            team_cs = database.select_team_cs(conn=conn, team_id=game["s1_teamid"], game_id=game["gameid"])
            p1_stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            p2_stats = database.select_stats(conn=conn, statid=game["s2_statid"])

            # Creep Share
            p1_e_jgl = p1_stats.neutral_minions_killed_enemy_jungle if p1_stats.neutral_minions_killed_enemy_jungle is not None else 0
            p1_t_jgl = p1_stats.neutral_minions_killed_team_jungle if p1_stats.neutral_minions_killed_team_jungle is not None else 0

            p2_e_jgl = p2_stats.neutral_minions_killed_enemy_jungle if p2_stats.neutral_minions_killed_enemy_jungle is not None else 0
            p2_t_jgl = p2_stats.neutral_minions_killed_team_jungle if p2_stats.neutral_minions_killed_team_jungle is not None else 0

            if team_cs[0]["cs"] is None:
                continue
            p1_cs = p1_stats.total_minions_killed + p1_e_jgl + p1_t_jgl
            p1_cs_share = analysis.base_analysis.cs_share(p1_cs, team_cs[0]["cs"])

            p2_cs = p2_stats.total_minions_killed + p2_e_jgl + p2_t_jgl
            p2_cs_share = analysis.base_analysis.cs_share(p2_cs, team_cs[0]["cs"])

            # CS Difference
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

            p1_cs_diff = analysis.base_analysis.cs_diff(frames=p1_frames,
                                                        opponent_frames=p1_opponent_frames)
            p2_cs_diff = analysis.base_analysis.cs_diff(frames=p2_frames,
                                                        opponent_frames=p2_opponent_frames)

            if np.isnan(p1_cs_share) or np.isnan(p2_cs_share) or np.isnan(p1_cs_diff["overall"]) or np.isnan(
                    p2_cs_diff["overall"]):
                continue

            p1_css = ss.norm.cdf(p1_cs_share, enums.CreepShare.MU, enums.CreepShare.SIG)
            p2_css = ss.norm.cdf(p2_cs_share, enums.CreepShare.MU, enums.CreepShare.SIG)
            p1_csd = ss.norm.cdf(p1_cs_diff["overall"], enums.CSD.MU, enums.CSD.SIG)
            p2_csd = ss.norm.cdf(p2_cs_diff["overall"], enums.CSD.MU, enums.CSD.SIG)

            values[summoner1.name]["share"].append(p1_css)
            values[summoner2.name]["share"].append(p2_css)
            values[summoner1.name]["csd"].append(p1_csd)
            values[summoner2.name]["csd"].append(p2_csd)

            p1_raw.append([p1_css, p1_csd])
            p2_raw.append([p2_css, p2_csd])

        farmer = analysis.classification.classify_farmer_type(
            p1_cs=np.nanmean(np.array(values[summoner1.name]["share"])),
            p2_cs=np.nanmean(np.array(values[summoner2.name]["share"])),
            p1_csd=np.nanmean(np.array(values[summoner1.name]["csd"])),
            p2_csd=np.nanmean(np.array(values[summoner2.name]["csd"])),
        )

        resp.body = json.dumps({
            "cluster_centre": farmer["cluster_centre"],
            summoner1.name: farmer["1"],
            summoner2.name: farmer["2"],
            "raw": {
                summoner1.name: p1_raw,
                summoner2.name: p2_raw
            }
        })


class Tactician:
    def on_get(self, req, resp):
        logger.info("GET /classification/tactician")
        conn = database.get_connection()

        params = req.params
        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)
        values = {summoner1.name: {"worthness": [], "objectives": []},
                  summoner2.name: {"worthness": [], "objectives": []}}

        p1_raw = []
        p2_raw = []
        for game in common_games:
            frames = database.select_game_frames(conn=conn, game_id=game["gameid"])
            kills = database.select_all_kill_timeline(conn=conn, game_id=game["gameid"])
            objectives = database.select_objectives(conn=conn, game_id=game["gameid"])

            p1_t = analysis.classification.tactician(game["s1_participantid"], game["s1_teamid"], kills, objectives,
                                                     frames, conn)
            p2_t = analysis.classification.tactician(game["s2_participantid"], game["s1_teamid"], kills, objectives,
                                                     frames, conn)
            if np.isnan(p1_t["worthness"]) or np.isnan(p2_t["worthness"]) or np.isnan(p1_t["objectives"]) or np.isnan(
                    p2_t["objectives"]):
                continue

            p1_worth = ss.norm.cdf(p1_t["worthness"], enums.Worthness.MU, enums.Worthness.SIG)
            p2_worth = ss.norm.cdf(p2_t["worthness"], enums.Worthness.MU, enums.Worthness.SIG)
            p1_obj = ss.expon.cdf(p1_t["objectives"], scale=enums.KillObjectives.MU)
            p2_obj = ss.expon.cdf(p2_t["objectives"], scale=enums.KillObjectives.MU)

            values[summoner1.name]["worthness"].append(p1_worth)
            values[summoner2.name]["worthness"].append(p2_worth)
            values[summoner1.name]["objectives"].append(p1_obj)
            values[summoner2.name]["objectives"].append(p2_obj)

            p1_raw.append([p1_worth, p1_obj])
            p2_raw.append([p2_worth, p2_obj])

        tactician = analysis.classification.classify_tactician(
            p1_worth=np.nanmean(np.array(values[summoner1.name]["worthness"])),
            p2_worth=np.nanmean(np.array(values[summoner2.name]["worthness"])),
            p1_obj=np.nanmean(np.array(values[summoner1.name]["objectives"])),
            p2_obj=np.nanmean(np.array(values[summoner2.name]["objectives"])),
        )

        resp.body = json.dumps({
            "cluster_centre": tactician["cluster_centre"],
            summoner1.name: tactician["1"],
            summoner2.name: tactician["2"],
            "raw": {
                summoner1.name: p1_raw,
                summoner2.name: p2_raw
            }
        })
