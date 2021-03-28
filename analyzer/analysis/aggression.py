import ast
import math

import numpy as np

from enums import GameState, Constants, Role, Map
import util

logger = util.Logger(__name__)
# epsilon - "neutral" region
EPSILON = 1000


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
                aggressive.append(distance / 8000)
                passive.append(0)
            elif distance < 0 - Constants.DIST_EPS:
                passive.append(abs(distance) / 8000)
                aggressive.append(0)
        else:
            if distance < 0 - Constants.DIST_EPS:
                aggressive.append(abs(distance) / 8000)
                passive.append(0)
            elif distance > 0 + Constants.DIST_EPS:
                passive.append(distance / 8000)
                aggressive.append(0)

    return np.average(np.array(aggressive)) + np.average(np.array(passive))


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
            if not _detect_team_fight(kill_time, kill_position, affected_frames):
                if role == Role.TOP:
                    gradient = 6712 / 6431
                    b = -1
                    c = 5120.93
                elif role == Role.MID:
                    gradient = Map.CENTER[1] / Map.CENTER[0]
                    b = -1
                    c = 0
                elif role == Role.BOT or role == Role.SUP:
                    gradient = 6743 / 6408
                    b = -1
                    c = -5797.71
                else:
                    # either JGL or unknown role (default: increase)
                    ganks += 1
                    break
                dist = _distance(kill_position[0], kill_position[1], gradient=gradient, b=b, c=c)

                if abs(dist) <= 1000:
                    ganks += 1

    try:
        return ganks / overall
    except ZeroDivisionError:
        return 0


def _detect_team_fight(kill_time, kill_position, time_frames):
    people = 0

    time_diff = (round(kill_time) - kill_time)
    radius = Constants.FIGHT_RADIUS + Constants.FIGHT_RADIUS * time_diff * 10
    for time_frame in time_frames:
        if time_frame["timestamp"] % round(kill_time) * 60000 < 60000:
            if time_frame["position"] is None:
                break
            position = ast.literal_eval(time_frame["position"])
            circle_dist = pow(position[0] - kill_position[0], 2) + pow(position[1] - kill_position[1], 2)
            if circle_dist < pow(radius, 2):
                people += 1

    if people >= 7:
        return True
    else:
        return False


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


def _distance(x, y, gradient, b=1, c=1):
    norm = math.sqrt(pow(gradient, 2) + pow(b, 2))
    return (gradient * x + b * y + c) / norm
