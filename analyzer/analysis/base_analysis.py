import math

import numpy as np

import database
import model
from analyzer import util
from enums import Role, GameState, KP


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
        return np.NaN


def ss_kill_participation(participant: str, kills):
    kp = kill_participation(participant, kills)
    return (kp - KP.MU) / KP.SIG


def avg_kda(kills, deaths, assists):
    try:
        return round((kills + assists) / deaths, 2)
    except ZeroDivisionError:
        return np.NaN


def win_rate(games):
    wins_total = 0
    for game in games:
        wins_total += 1 if game["win"] == "Win" else 0
    try:
        return wins_total / len(games)
    except ZeroDivisionError:
        return np.Inf


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
    try:
        if avg_role - int(avg_role) != 0:
            return role_keys[math.floor(avg_role) - 1], role_keys[math.ceil(avg_role) - 1]
    except ValueError:
        # workaround if avg_role is np.NaN not catching np NaN
        return 'None'
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


def cs_share(p_cs, team_cs):
    return p_cs / team_cs


def cs_diff(frames, opponent_frames):
    diff = {
        "overall": [],
        "early": [],
        "mid": [],
        "late": []
    }
    for idx, frame in enumerate(frames):
        p_cs = frame["minionskilled"] + frame["jungleminionskilled"]
        o_cs = opponent_frames[idx]["minionskilled"] + opponent_frames[idx]["jungleminionskilled"]
        csd = p_cs - o_cs
        if idx <= GameState.EARLY[1]:
            diff["early"].append(csd)
        elif GameState.MID[0] <= idx <= GameState.MID[1]:
            diff["mid"].append(csd)
        elif GameState.LATE[0] <= idx <= GameState.LATE[1]:
            diff["late"].append(csd)
        diff["overall"].append(csd)

    diff["overall"] = np.average(np.array(diff["overall"]))
    diff["early"] = np.average(np.array(diff["early"]))
    diff["mid"] = np.average(np.array(diff["mid"]))
    diff["late"] = np.average(np.array(diff["late"]))

    return diff


def common_stats(
    common_games,
):
    conn = database.get_connection()
    games = 0

    dkills = 0
    nkills = 0
    heralds = 0
    inhibs = 0
    towers = 0
    bans = []
    first_blood = []
    first_tower = []
    first_inhib = []
    first_baron = []
    first_dragon = []
    first_herald = []

    for g in common_games:
        # same team
        if g[4] == g[8]:
            team = database.select_team_from_teamid_and_gameid(
                conn=conn,
                game_id=g[0],
                team_id=g[4],
            )

            print(f'{team=}')

            dkills += team[12]
            nkills += team[11]
            heralds += team[13]
            inhibs += team[10]
            towers += team[9]
            for b in team[14]:
                bans.append(b)
            first_blood.append(team[3])
            first_tower.append(team[4])
            first_inhib.append(team[5])
            first_baron.append(team[6])
            first_dragon.append(team[7])
            first_herald.append(team[8])

            games += 1

    return {
        'drakes': int(round(dkills / games, 0)),
        'nash': int(round(nkills / games, 0)),
        'heralds': int(round(heralds / games, 0)),
        'inhibis': int(round(inhibs / games, 0)),
        'towers': int(round(towers / games, 0)),
        'first_blood': True if first_blood.count(True) > first_blood.count(False) else False,
        'first_tower': True if first_tower.count(True) > first_tower.count(False) else False,
        'first_inhib': True if first_inhib.count(True) > first_inhib.count(False) else False,
        'first_baron': True if first_baron.count(True) > first_baron.count(False) else False,
        'first_dragon': True if first_dragon.count(True) > first_dragon.count(False) else False,
        'first_herald': True if first_herald.count(True) > first_herald.count(False) else False,
        'bans': max(set(bans), key=bans.count),
    }
