import ast
import pickle

import numpy as np

import database
from enums import Constants, Objectives


def classify_murderous_duo(p1_kp, p2_kp, p1_kda, p2_kda):
    model = pickle.load(open('/analyzer/kmeans_murderous.pkl', 'rb'))
    centres = model.cluster_centers_.tolist()
    prediction = model.predict([[p1_kp, p1_kda], [p2_kp, p2_kda]])

    return {
        "cluster_centre": {
            "0": centres[0],
            "1": centres[1]
        },
        "1": {
            "isClass": bool(prediction[0]),
            "value": [p1_kp, p1_kda]
        },
        "2": {
            "isClass": bool(prediction[1]),
            "value": [p2_kp, p2_kp]
        }
    }


def classify_farmer_type(p1_cs, p2_cs, p1_csd, p2_csd):
    model = pickle.load(open('/analyzer/kmeans_farmers.pkl', 'rb'))
    centres = model.cluster_centers_.tolist()
    prediction = model.predict([[p1_cs, p1_csd], [p2_cs, p2_csd]])

    return {
        "cluster_centre": {
            "0": centres[0],
            "1": centres[1]
        },
        "1": {
            "isClass": bool(prediction[0]),
            "value": [p1_cs, p1_csd]
        },
        "2": {
            "isClass": bool(prediction[1]),
            "value": [p2_cs, p2_csd]
        }
    }


def classify_tactician(p1_worth, p2_worth, p1_obj, p2_obj):
    model = pickle.load(open('./kmeans_tactician.pkl', 'rb'))
    centres = model.cluster_centers_.tolist()
    prediction = model.predict([[p1_worth, p1_obj], [p2_worth, p2_obj]])

    return {
        "cluster_centre": {
            "0": centres[1],
            "1": centres[0]
        },
        "1": {
            "isClass": not bool(prediction[0]),
            "value": [p1_worth, p1_obj]
        },
        "2": {
            "isClass": not bool(prediction[1]),
            "value": [p2_worth, p2_obj]
        }
    }


def _follow_kills(idx, kill_frames, kill_time, kill_position):
    b = True
    counter = idx + 1
    f_kills = []
    while b:
        if counter > len(kill_frames) - 1:
            break
        position = ast.literal_eval(kill_frames[counter]["position"])
        i_kill_time = kill_frames[counter]["timestamp"] / 60000
        time_diff = abs(kill_time - i_kill_time)

        if time_diff >= 1:
            break

        radius = Constants.FIGHT_RADIUS + Constants.FIGHT_RADIUS * time_diff

        circle_dist = pow(position[0] - kill_position[0], 2) + pow(position[1] - kill_position[1], 2)
        if circle_dist < pow(radius, 2):
            f_kills.append(kill_frames[counter])
            counter += 1
        else:
            b = False
    return f_kills


def tactician(participant, team_id, kill_frames, objective_frames, position_frames, conn):
    skip_frames = 0
    worthness = []
    objectives = []

    for idx, kill in enumerate(kill_frames):
        if skip_frames > 0:
            skip_frames -= 1
            continue

        if kill["killer"] == participant or kill["victim"] == participant \
                or participant in kill["assistingparticipantids"]:
            kill_position = ast.literal_eval(kill["position"])
            kill_time = kill["timestamp"] / Constants.TIME

            fight_kills = [kill]

            follow_kills = _follow_kills(idx, kill_frames, kill_time, kill_position)
            for follow_kill in follow_kills:
                fight_kills.append(follow_kill)
            skip_frames += len(follow_kills)

            members = {
                "blue": {"overall": 0, "alive": 0, "dead": 0},
                "red": {"overall": 0, "alive": 0, "dead": 0}
            }
            objectives_game = 0
            for fight_kill in fight_kills:
                fight_kill_time = fight_kill["timestamp"] / 60000
                affected_frames = position_frames[10 * round(fight_kill_time):10 * round(fight_kill_time) + 9]
                fight_members = _count_fight_members(fight_kill, affected_frames, conn)
                members["blue"]["overall"] = max(fight_members["blue"]["overall"], members["blue"]["overall"])
                members["blue"]["alive"] = max(fight_members["blue"]["overall"], members["blue"]["alive"])
                members["blue"]["dead"] = max(fight_members["blue"]["overall"], members["blue"]["dead"])
                members["red"]["overall"] = max(fight_members["red"]["overall"], members["red"]["overall"])
                members["red"]["alive"] = max(fight_members["blue"]["overall"], members["red"]["alive"])
                members["red"]["dead"] = max(fight_members["blue"]["overall"], members["red"]["dead"])

                objectives_game += check_objectives(fight_kill, objective_frames)

            objectives.append(objectives_game)
            worthness.append(is_worth_fight(members, team_id))

    return {
        "worthness": np.nanmean(np.array(worthness)),
        "objectives": np.nanmean(np.array(objectives))
    }


def check_objectives(kill, objective_frames):
    kill_time = kill["timestamp"] / 60000
    objectives = 0

    for objective_frame in objective_frames:
        objective_time = objective_frame["timestamp"] / 60000
        if kill_time < objective_time < kill_time + 2:
            objective_type = objective_frame["type"]
            if objective_type == 'ELITE_MONSTER_KILL':
                monster_type = objective_frame["monstertype"]
                monster_subtype = objective_frame["monstersubtype"]
                if monster_type == 'DRAGON':
                    if monster_subtype != 'ELDER_DRAGON':
                        monster_type = 'ELEMENTAL_DRAGON'
                objectives += _objective_value(objective_type, monster_type)
            elif objective_type == 'BUILDING_KILL':
                building_type = objective_frame['towertype']
                objectives += _objective_value(objective_type, building_type)
        else:
            break
    return objectives


def _objective_value(obj_type, obj_subtype):
    if obj_type == 'ELITE_MONSTER_KILL':
        if obj_subtype == 'ELEMENTAL_DRAGON':
            return Objectives.EliteMonster.ELEMENTAL_DRAGON
        elif obj_subtype == 'RIFTHERALD':
            return Objectives.EliteMonster.RIFT_HERALD
        elif obj_subtype == 'ELDER_DRAGON':
            return Objectives.EliteMonster.ELDER_DRAGON
        elif obj_subtype == 'BARON_NASHOR':
            return Objectives.EliteMonster.BARON_NASHOR
    elif obj_type == 'BUILDING_KILL':
        if obj_subtype == 'OUTER_TURRET':
            return Objectives.Building.OUTER_TURRET
        elif obj_subtype == 'INNER_TURRET':
            return Objectives.Building.INNER_TURRET
        elif obj_subtype == 'BASE_TURRET':
            return Objectives.Building.BASE_TURRET
        elif obj_subtype == 'NEXUS_TURRET':
            return Objectives.Building.NEXUS_TURRET


def is_worth_fight(members, team_id):
    """
    Determine if a fight was worth or not based on people alive/dead/overall.

    :param members
    :param team_id
    :return: "worthness" (-2: not worth at all, -1: not worth, 0: neutral, 1: worth, 2: extremely worth)
    """
    p_team = "blue" if team_id == 100 else "red"
    op_team = "red" if team_id == 100 else "blue"

    numbers_advantage = False
    lost = False

    if members[p_team]["overall"] > members[op_team]["overall"]:
        numbers_advantage = True
    if members[p_team]["dead"] > members[op_team]["dead"]:
        lost = True

    if members[p_team]["overall"] == members[op_team]["overall"] and members[p_team]["dead"] == members[op_team]["dead"]:
        return 0

    if numbers_advantage and lost:
        return -2
    elif numbers_advantage and not lost:
        return 1
    elif not numbers_advantage and lost:
        return -1
    elif not numbers_advantage and not lost:
        return 2


def _count_fight_members(kill, time_frames, conn):
    members = {
        "blue": {"overall": 0, "alive": 0, "dead": 0},
        "red": {"overall": 0, "alive": 0, "dead": 0}
    }

    kill_time = kill["timestamp"] / 60000
    if kill["position"] is None:
        return members
    kill_position = ast.literal_eval(kill["position"])
    time_diff = abs((round(kill_time) - kill_time))
    radius = Constants.FIGHT_RADIUS + Constants.FIGHT_RADIUS * time_diff
    for time_frame in time_frames:
        if time_frame["timestamp"] % (round(kill_time) * 60000) < 60000:
            if time_frame["position"] is None:
                break
            frame_participant = time_frame["participantid"]
            team = database.select_participant_team(conn=conn, participant_id=frame_participant)
            key = "blue" if team[0]["teamid"] == 100 else "red"

            if frame_participant == kill["killer"] or frame_participant in kill["assistingparticipantids"]:
                members[key]["overall"] += 1
                members[key]["alive"] += 1
                continue
            elif frame_participant == kill["victim"]:
                members[key]["overall"] += 1
                members[key]["dead"] += 1
                continue

            position = ast.literal_eval(time_frame["position"])
            circle_dist = pow(position[0] - kill_position[0], 2) + pow(position[1] - kill_position[1], 2)
            if circle_dist < pow(radius, 2):
                members[key]["overall"] += 1
                members[key]["alive"] += 1

    return members
