import ast
import math

import numpy as np
import scipy.stats as stats
from scipy.integrate import quad

from enums import GameState, Constants, Role, Map, KP, FightType, FWK, POS, Ganking
import util

logger = util.Logger(__name__)
# epsilon - "neutral" region
EPSILON = 1000


def aggression(kp, fw_kills, pos, ganking):
    kp_val = stats.norm.cdf(kp, KP.MU, KP.SIG)
    fwk_val = stats.expon.cdf(fw_kills, scale=FWK.MU)
    pos_val = stats.norm.cdf(pos, POS.MU, POS.SIG)
    gank_val = stats.expon.cdf(ganking, scale=Ganking.MU)

    aggro = (kp_val + fwk_val + pos_val + gank_val) / 4
    return util.normalize(aggro, -2, 2)


def positioning(team_id, frames):
    aggressive = []
    passive = []

    for frame in frames:
        if frame["position"] is None:
            break
        position = ast.literal_eval(frame["position"])
        distance = _distance(position[0], position[1], Map.HEIGHT / Map.WIDTH, c=-Map.HEIGHT)

        if team_id == 100:
            if distance > 0 + Constants.DIST_EPS:
                aggressive.append(distance / Map.HALF_DIST)
                passive.append(0)
            elif distance < 0 - Constants.DIST_EPS:
                passive.append(abs(distance) / Map.HALF_DIST)
                aggressive.append(0)
        else:
            if distance < 0 - Constants.DIST_EPS:
                aggressive.append(abs(distance) / Map.HALF_DIST)
                passive.append(0)
            elif distance > 0 + Constants.DIST_EPS:
                passive.append(distance / Map.HALF_DIST)
                aggressive.append(0)

    return (np.average(np.array(aggressive)) + (1 - np.average(np.array(passive)))) / 2


def ss_positioning(team_id, frames):
    pos = positioning(team_id, frames)
    return (pos - POS.MU) / POS.SIG


def ganking(participant, role, frames, kills):
    overall = 0
    ganks = 0
    for kill in kills:
        if kill["killer"] == participant or kill["victim"] == participant \
                or participant in kill["assistingparticipantids"]:
            kill_position = ast.literal_eval(kill["position"])
            kill_time = kill["timestamp"] / Constants.TIME

            affected_frames = frames[10 * round(kill_time):10 * round(kill_time) + 9]
            overall += 1
            if _detect_fight_type(kill_time, kill_position, affected_frames) == FightType.GANK:
                if role == Role.TOP:
                    gradient = 6712 / 6431
                    b = -1
                    c = 5120.93
                    d = 1
                elif role == Role.MID:
                    gradient = Map.CENTER[1] / Map.CENTER[0]
                    b = -1
                    c = 0
                    d= 0
                elif role == Role.BOT or role == Role.SUP:
                    gradient = 6743 / 6408
                    b = -1
                    c = -5797.71
                    d = -1
                else:
                    # either JGL or unknown role (default: increase)
                    ganks += 1
                    break
                dist = _distance(kill_position[0], kill_position[1], gradient=gradient, b=b, c=c)

                if role == Role.MID:
                    if abs(dist) >= 1000:
                        ganks += 1
                else:
                    if dist * d >= 1000:
                        ganks += 1

    logger.info(f"{ganks}, {overall}, {len(kills)}")
    try:
        return ganks / overall
    except ZeroDivisionError:
        return 0


def ss_ganking(participant, role, frames, kills):
    gank = ganking(participant, role, frames, kills)
    return (gank - Ganking.MU) / Ganking.SIG


def _detect_fight_type(kill_time, kill_position, time_frames):
    people = 0

    time_diff = abs((round(kill_time) - kill_time))
    radius = Constants.FIGHT_RADIUS + Constants.FIGHT_RADIUS * time_diff
    for time_frame in time_frames:
        if time_frame["timestamp"] % (round(kill_time) * 60000) < 60000:
            if time_frame["position"] is None:
                break
            position = ast.literal_eval(time_frame["position"])
            circle_dist = pow(position[0] - kill_position[0], 2) + pow(position[1] - kill_position[1], 2)
            if circle_dist < pow(radius, 2):
                people += 1

    if people <= 3:
        return FightType.SOLO
    if 3 < people < 7:
        return FightType.GANK
    if people >= 7:
        return FightType.TEAM_FIGHT
    else:
        return None


def forward_kills(participant, kills):
    overall_kills = 0
    fw_kills = 0

    for kill in kills:
        if kill["killer"] == participant or participant in kill["assistingparticipantids"]:
            position = ast.literal_eval(kill["position"])
            distance = _distance(position[0], position[1], Map.HEIGHT / Map.WIDTH, c=-Map.HEIGHT)

            if kill["teamid"] == 100:
                if distance > 0 + Constants.DIST_EPS:
                    fw_kills += 1
            else:
                if distance < 0 - Constants.DIST_EPS:
                    fw_kills += 1
        overall_kills += 1

    try:
        return fw_kills / overall_kills
    except ZeroDivisionError:
        return 0


def ss_forward_kills(participant, kills):
    fw_kill = forward_kills(participant, kills)
    return (fw_kill - FWK.MU) / FWK.SIG


def _distance(x, y, gradient, b=1, c=1):
    norm = math.sqrt(pow(gradient, 2) + pow(b, 2))
    return (gradient * x + b * y + c) / norm
