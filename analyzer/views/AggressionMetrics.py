import json

import numpy as np

import analysis
import database
import util


logger = util.Logger(__name__)


class Aggression:
    def on_get(self, req, resp):
        logger.info('GET /aggression')
        params = req.params
        logger.info(f'Calculate aggression metric for {params["summoner1"]} and {params["summoner2"]}')

        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        stats = {
            summoner1.name: {
                "kp": [], "fw_kills": [], "positioning": [], "ganking": []
            },
            summoner2.name: {
                "kp": [], "fw_kills": [], "positioning": [], "ganking": []
            }
        }

        for game in common_games:
            team_kills = database.select_kill_timeline(conn=conn, game_id=game["gameid"], team_id=game["s1_teamid"])
            p1_frames = database.select_participant_frames(conn=conn, participant_id=game["s1_participantid"])
            p2_frames = database.select_participant_frames(conn=conn, participant_id=game["s2_participantid"])
            frames = database.select_game_frames(conn=conn, game_id=game["gameid"])
            kills = database.select_all_kill_timeline(conn=conn, game_id=game["gameid"])

            # Kill Participation
            stats[summoner1.name]["kp"].append(analysis.base_analysis.kill_participation(
                participant=game["s1_participantid"],
                kills=team_kills,
            ))
            stats[summoner2.name]["kp"].append(analysis.base_analysis.kill_participation(
                participant=game["s2_participantid"],
                kills=team_kills,
            ))

            # Forward Kills
            stats[summoner1.name]["fw_kills"].append(analysis.aggression.forward_kills(
                participant=game["s1_participantid"],
                kills=team_kills
            ))
            stats[summoner2.name]["fw_kills"].append(analysis.aggression.forward_kills(
                participant=game["s2_participantid"],
                kills=team_kills
            ))

            # Positioning
            stats[summoner1.name]["positioning"].append(analysis.aggression.positioning(
                team_id=game["s1_teamid"],
                frames=p1_frames
            ))
            stats[summoner2.name]["positioning"].append(analysis.aggression.positioning(
                team_id=game["s2_teamid"],
                frames=p2_frames
            ))

            # Ganking
            stats[summoner1.name]["ganking"].append(analysis.aggression.ganking(
                participant=game["s1_participantid"],
                role=util.get_canonic_lane(lane=game["s1_lane"], role=game["s1_role"]),
                frames=frames,
                kills=kills
            ))
            stats[summoner2.name]["ganking"].append(analysis.aggression.ganking(
                participant=game["s2_participantid"],
                role=util.get_canonic_lane(lane=game["s2_lane"], role=game["s2_role"]),
                frames=frames,
                kills=kills
            ))

        stats[summoner1.name]["kp"] = np.average(np.array(stats[summoner1.name]["kp"]))
        stats[summoner1.name]["fw_kills"] = np.average(np.array(stats[summoner1.name]["fw_kills"]))
        stats[summoner1.name]["positioning"] = np.average(np.array(stats[summoner1.name]["positioning"]))
        stats[summoner1.name]["ganking"] = np.average(np.array(stats[summoner1.name]["ganking"]))

        stats[summoner2.name]["kp"] = np.average(np.array(stats[summoner2.name]["kp"]))
        stats[summoner2.name]["fw_kills"] = np.average(np.array(stats[summoner2.name]["fw_kills"]))
        stats[summoner2.name]["positioning"] = np.average(np.array(stats[summoner2.name]["positioning"]))
        stats[summoner2.name]["ganking"] = np.average(np.array(stats[summoner2.name]["ganking"]))

        resp.body = json.dumps(stats)
