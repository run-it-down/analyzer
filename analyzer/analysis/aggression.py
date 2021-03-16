import math

import numpy as np

import util


logger = util.Logger(__name__)


def aggression(positions, gold_diffs, kps, kdas):
    print("Calculate Aggression")


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


def positioning(positions, player_info, state):
    state_info = {
        "early": (0, 15, 0),
        "mid": (16, 25, 4000),
        "late": (26, 100, 8000)
    }

    # np.nanmean prints a runtime warning for empty slices. does not effect execution
    early_positions = np.nanmean(positions["p1"][:, state_info["early"][0]:state_info["early"][1]], 1)
    mid_positions = np.nanmean(positions["p1"][:, state_info["mid"][0]:state_info["mid"][1]], 1)
    late_positions = np.nanmean(positions["p1"][:, state_info["late"][0]:state_info["late"][1]], 1)

    early_distances = _distances(positions=early_positions, player_info=player_info, state=state_info["early"])
    mid_distances = _distances(positions=mid_positions, player_info=player_info, state=state_info["mid"])
    late_distances = _distances(positions=late_positions, player_info=player_info, state=state_info["late"])

    for idx, distance in enumerate(early_distances):
        if distance < 0:
            if player_info[idx][2] == 100:
                print("passive blue")
            else:
                print("aggressive red")
        elif distance > 0:
            if player_info[idx][2] == 100:
                print("aggressive blue")
            else:
                print("passive red")


def _distances(positions, player_info, state):
    sqrt_2 = math.sqrt(2)

    def gradient(t, w): return 16000 + ((math.pow(-1, t / 100) * math.pow(-1, w)) * state[2])
    def scale(t, w): return sqrt_2 / (32000 - abs(gradient(t, w)))
    def distance(x, y, t, w): return (x + y - gradient(t, w)) / sqrt_2

    return np.fromiter(
        (distance(avg[0], avg[1], player_info[idx][2], player_info[idx][3]) * scale(player_info[idx][2], player_info[idx][3])
         for idx, avg in enumerate(positions)),
        positions.dtype,
        count=len(positions))
