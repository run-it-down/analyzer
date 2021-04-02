import math

import numpy as np

import util
from enums import Role, GameState


def kill_participation(participant: str, kills):
    overall_kills = 0
    summoner_kp = 0

    for kill in kills:
        if kill["killer"] == participant or participant in kill["assistingparticipantids"]:
            summoner_kp += 1
        overall_kills += 1

    try:
        return summoner_kp / overall_kills
    except ZeroDivisionError:
        return np.NaN


def game_kda(stat):
    try:
        return (stat["kills"] + stat["assists"]) / stat["deaths"]
    except ZeroDivisionError:
        return "Perfect KDA"


def avg_kda(kills, deaths, assists):
    try:
        return (kills + assists) / deaths
    except ZeroDivisionError:
        return "Perfect KDA"


def win_rate(games):
    wins_total = 0
    for game in games:
        wins_total += 1 if game["win"] == "Win" else 0
    try:
        return wins_total / len(games)
    except ZeroDivisionError:
        return 0


def determine_avg_role(games, role_key, lane_key):
    roles = []
    mapping = {
        Role.TOP: 1, Role.JGL: 2, Role.MID: 3, Role.BOT: 4, Role.SUP: 5
    }
    for game in games:
        lane = util.get_canonic_lane(lane=game[lane_key], role=game[role_key])
        if lane is not None:
            roles.append(mapping[lane])
    avg_role = np.median(np.array(roles))

    if avg_role is np.NaN:
        return "None"
    role_keys = list(mapping.keys())
    if avg_role - int(avg_role) != 0:
        return role_keys[math.floor(avg_role) - 1], role_keys[math.ceil(avg_role) - 1]
    return role_keys[int(avg_role) - 1]


def gold_diff(frames, opponent_frames):
    diff = {
        "overall": [],
        "early": [],
        "mid": [],
        "late": []
    }
    for idx, frame in enumerate(frames):
        gd = frame["totalgold"] - opponent_frames[idx]["totalgold"]
        if idx <= GameState.EARLY[1]:
            diff["early"].append(gd)
        elif GameState.MID[0] <= idx <= GameState.MID[1]:
            diff["mid"].append(gd)
        elif GameState.LATE[0] <= idx <= GameState.LATE[1]:
            diff["late"].append(gd)
        diff["overall"].append(gd)

    diff["overall"] = np.average(np.array(diff["overall"]))
    diff["early"] = np.average(np.array(diff["early"]))
    diff["mid"] = np.average(np.array(diff["mid"]))
    diff["late"] = np.average(np.array(diff["late"]))

    return diff


def gold_share(p_gold, team_gold):
    return p_gold / team_gold
