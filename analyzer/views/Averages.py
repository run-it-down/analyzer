import json
import time

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
            "kp": [], "fw_kills": [], "positioning": [], "ganking": []
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

        resp.body = json.dumps(stats)
