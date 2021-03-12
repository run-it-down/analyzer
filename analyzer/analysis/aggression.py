import numpy as np

import model


def aggression(gold_):
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
