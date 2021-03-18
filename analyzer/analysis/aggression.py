import math

import numpy as np

from enums import GameState
import util

logger = util.Logger(__name__)


def aggression(gold_diff, position_ratio, kps, csds, kda):
    # print(gold_diff["p1"], len(position_ratio["p1"]), len(kps), len(csds))
    game_length = len(gold_diff["p1"]["early"])

    aggression_players = {"p1": {}, "p2": {}}
    states = ("early", "mid", "late")

    for state in states:
        aggression_players["p1"][state] = _state_aggression(gold_diff=gold_diff["p1"][state],
                                                            position_ratio=position_ratio["p1"][state],
                                                            kps=kps["p1"][state], csds=csds["p1"][state],
                                                            kda=kda["p1"][state])
        aggression_players["p2"][state] = _state_aggression(gold_diff=gold_diff["p2"][state],
                                                            position_ratio=position_ratio["p2"][state],
                                                            kps=kps["p2"][state], csds=csds["p2"][state],
                                                            kda=kda["p2"][state])

    means = {"p1": {}, "p2": {}}
    for state in states:
        means["p1"][state] = np.nanmedian(aggression_players["p1"][state])
        means["p2"][state] = np.nanmedian(aggression_players["p2"][state])

    # plane equation E: x + y + z = 1; epsilon = 0.05 -> neutral room
    p1_aggression_min = means["p1"]["early"] + means["p1"]["mid"] + means["p1"]["late"] - 0.9
    p2_aggression_min = means["p2"]["early"] + means["p2"]["mid"] + means["p2"]["late"] - 0.9

    p1_aggression_max = means["p1"]["early"] + 1.05 * means["p1"]["mid"] + means["p1"]["late"] - 1.1
    p2_aggression_max = means["p2"]["early"] + 1.05 * means["p2"]["mid"] + means["p2"]["late"] - 1.1

    if p1_aggression_min < 0:
        aggression_players["p1"]["type"] = {
            "name": "passive",
            "value": (means["p1"]["early"], means["p1"]["mid"], means["p1"]["late"])
        }
    else:
        if p1_aggression_max <= 0:
            aggression_players["p1"]["type"] = {
                "name": "balanced",
                "value": (means["p1"]["early"], means["p1"]["mid"], means["p1"]["late"])
            }
        else:pr
            aggression_players["p1"]["type"] = {
                "name": "aggressive",
                "value": (means["p1"]["early"], means["p1"]["mid"], means["p1"]["late"])
            }

    if p2_aggression_min < 0:
        aggression_players["p2"]["type"] = {
            "name": "passive",
            "value": (means["p2"]["early"], means["p2"]["mid"], means["p2"]["late"])
        }
    else:
        if p2_aggression_max <= 0:
            aggression_players["p2"]["type"] = {
                "name": "balanced",
                "value": (means["p2"]["early"], means["p2"]["mid"], means["p2"]["late"])
            }
        else:
            aggression_players["p2"]["type"] = {
                "name": "aggressive",
                "value": (means["p2"]["early"], means["p2"]["mid"], means["p2"]["late"])
            }

    return aggression_players


def _state_aggression(gold_diff, position_ratio, kps, csds, kda):
    position_ratio = np.divide((position_ratio + 1), 2)

    def pos_kills(pos, kp, kda): return (1 / 2 * (kp + kda)) / (1 + (1 - pos))

    state_aggression = np.fromiter(
        (1 / 2 * (pos_kills(position_ratio[idx], kps[idx], kda[idx]) + csds[idx]) * 1 / (1 + (1 - gold_diff[idx]))
         for idx, gd in enumerate(gold_diff)),
        gold_diff.dtype,
        count=len(gold_diff)
    )
    return state_aggression.tolist()


def kp_per_state(kill_timeline: dict):
    overall_kills: dict = kill_timeline["overall"]
    p1_kills = kill_timeline["p1"]
    p2_kills = kill_timeline["p2"]

    p1_kp = {"early": [], "mid": [], "late": []}
    p2_kp = {"early": [], "mid": [], "late": []}

    for state, overall_kills in overall_kills.items():
        for idx, kills in enumerate(overall_kills):
            try:
                p1_kp[state].append(len(p1_kills[state][idx]) / len(kills))
            except ZeroDivisionError:
                p1_kp[state].append(0)
            try:
                p2_kp[state].append(len(p2_kills[state][idx]) / len(kills))
            except ZeroDivisionError:
                p2_kp[state].append(0)

    return {
        "p1": {
            "early": np.array(p1_kp["early"]),
            "mid": np.array(p1_kp["mid"]),
            "late": np.array(p1_kp["late"])
        },
        "p2": {
            "early": np.array(p2_kp["early"]),
            "mid": np.array(p2_kp["mid"]),
            "late": np.array(p2_kp["late"])
        }
    }


def avg_kp_per_state(kp_state: dict):
    return {
        "p1": {
            "early": np.average(kp_state["p1"]["early"]),
            "mid": np.average(kp_state["p1"]["mid"]),
            "late": np.average(kp_state["p1"]["late"])
        },
        "p2": {
            "early": np.average(kp_state["p2"]["early"]),
            "mid": np.average(kp_state["p2"]["mid"]),
            "late": np.average(kp_state["p2"]["late"])
        }
    }


def positioning(positions, player_info):
    shift = {"early": 0, "mid": 4000, "late": 8000}

    # np.nanmean prints a runtime warning for empty slices. does not effect execution
    early_positions = np.nanmean(positions[:, GameState.EARLY[0]:GameState.EARLY[1]], 1)
    mid_positions = np.nanmean(positions[:, GameState.MID[0]:GameState.MID[1]], 1)
    late_positions = np.nanmean(positions[:, GameState.LATE[0]:GameState.LATE[1]], 1)

    early_distances = _distance_ratios(positions=early_positions, player_info=player_info, shift=shift["early"])
    mid_distances = _distance_ratios(positions=mid_positions, player_info=player_info, shift=shift["mid"])
    late_distances = _distance_ratios(positions=late_positions, player_info=player_info, shift=shift["late"])

    return {
        "early": early_distances,
        "mid": mid_distances,
        "late": late_distances
    }


def _distance_ratios(positions, player_info, shift):
    sqrt_2 = math.sqrt(2)

    def gradient(t, w): return 16000 + ((math.pow(-1, t / 100) * math.pow(-1, w)) * shift)

    def scale(t, w): return sqrt_2 / (32000 - abs(gradient(t, w)))

    def distance(x, y, t, w): return (x + y - gradient(t, w)) / sqrt_2

    return np.fromiter(
        (distance(avg[0], avg[1], player_info[idx][2], player_info[idx][3]) * scale(player_info[idx][2],
                                                                                    player_info[idx][3])
         for idx, avg in enumerate(positions)),
        positions.dtype,
        count=len(positions))
