import ast

import numpy as np

import database


def transform_gold_diff(games, conn):
    """
    Returns a dictionary, which contains numpy arrays for gold differentials in each game (per minute).
    :param games:
    :param conn:
    :return:
    """
    gold_diff = {
        "p1": np.zeros(shape=(len(games), 15)),
        "p2": np.zeros(shape=(len(games), 15))
    }
    for idx, game in enumerate(games):
        p1_id, p2_id = game["s1_participantid"], game["s2_participantid"]
        lane_opponent_p1, lane_opponent_p2 = get_lane_opponent(participant_id=p1_id, conn=conn), get_lane_opponent(
            participant_id=p2_id, conn=conn)

        if lane_opponent_p1 is None:
            continue
        if lane_opponent_p2 is None:
            continue

        p1_game_gold_diff = build_gold_diff_array(p1_id, lane_opponent_p1, conn)
        p2_game_gold_diff = build_gold_diff_array(p2_id, lane_opponent_p2, conn)

        # Assumption: P1 and P2 Timeline have the same length -> therefore the same dimensions
        game_diff_shape, gold_diff_shape = None, None
        if type(p1_game_gold_diff) is not list:
            game_diff_shape = p1_game_gold_diff.shape[0]
            gold_diff_shape = gold_diff["p1"].shape[1]
        if type(p2_game_gold_diff) is not list:
            game_diff_shape = p2_game_gold_diff.shape[0]
            gold_diff_shape = gold_diff["p2"].shape[1]

        if game_diff_shape and gold_diff_shape:
            if game_diff_shape < gold_diff_shape:
                gold_diff["p1"][idx, :game_diff_shape] = p1_game_gold_diff
                gold_diff["p2"][idx, :game_diff_shape] = p2_game_gold_diff
            else:
                np_zeros = np.zeros([len(games), (game_diff_shape - gold_diff_shape)])
                np_zeros[:] = np.nan
                # If shape of game array is bigger than current shape -> reshape current array to fit all elements
                gold_diff["p1"] = np.hstack(
                    (gold_diff["p1"], np_zeros))
                gold_diff["p2"] = np.hstack(
                    (gold_diff["p2"], np_zeros))
                gold_diff["p1"][idx, :] = p1_game_gold_diff
                gold_diff["p2"][idx, :] = p2_game_gold_diff
    return gold_diff


def transform_positions(games, conn):
    """
    Returns a dictionary containing numpy arrays filled with positional data for both players.
    :param games:
    :param conn:
    :return:
    """
    # use minimum time of 15 (early surrender)
    # Side can be determined by using the first position in each game
    shape = [len(games), 15, 2]
    positions = {
        "p1": np.zeros(shape=shape),
        "p2": np.zeros(shape=shape)
    }
    for idx, game in enumerate(games):
        p1_id, p2_id = game["s1_participantid"], game["s2_participantid"]
        p1_frames = database.select_positions(conn, p1_id)
        p2_frames = database.select_positions(conn, p2_id)

        p1_game_positions, p2_game_positions = [], []
        for index in range(len(p1_frames)):
            p1_position = p1_frames[index]["position"]
            p2_position = p2_frames[index]["position"]
            if p1_position:
                pos = ast.literal_eval(p1_position)
                p1_game_positions.append(pos)
            if p2_position:
                pos = ast.literal_eval(p2_position)
                p2_game_positions.append(pos)

        # Assumption: P1 and P2 arrays have the same dimensions
        p1_position_array, p2_position_array = np.array(p1_game_positions), np.array(p2_game_positions)
        game_position_shape, overall_position_shape = p1_position_array.shape[0], positions["p1"].shape[1]
        if game_position_shape < overall_position_shape:
            positions["p1"][idx, :game_position_shape] = p1_position_array
            positions["p2"][idx, :game_position_shape] = p2_position_array
        else:
            # If shape of game array is bigger than current shape -> reshape current array to fit all elements
            np_zeros = np.zeros([len(games), (game_position_shape - overall_position_shape), 2])
            np_zeros[:] = np.nan
            positions["p1"] = np.hstack(
                (positions["p1"], np_zeros))
            positions["p1"][idx] = positions["p1"][idx].reshape((game_position_shape, 2))
            positions["p1"][idx, :] = p1_position_array
            positions["p2"] = np.hstack(
                (positions["p2"], np_zeros))
            positions["p2"][idx] = positions["p2"][idx].reshape((game_position_shape, 2))
            positions["p2"][idx, :] = p1_position_array

    return positions


def transform_kills(games, conn):
    # kills, deaths, assists
    kill_information = {
        "overall": [],
        "p1": [],
        "p2": []
    }
    for idx, game in enumerate(games):
        s1_id, s2_id = game["s1_statid"], game["s2_statid"]
        p1_stats = database.select_stats(conn, s1_id)
        p2_stats = database.select_stats(conn, s2_id)

        kill_information["overall"].append(database.select_overall_kill_information(
            conn=conn,
            game_id=game["gameid"],
            team_id=game["s1_teamid"]
        ))
        kill_information["p1"].append(np.array([p1_stats.kills, p1_stats.deaths, p1_stats.assists]))
        kill_information["p2"].append(np.array([p2_stats.kills, p2_stats.deaths, p2_stats.assists]))

    kill_information["overall"] = np.array(kill_information["overall"])
    kill_information["p1"] = np.array(kill_information["p1"])
    kill_information["p2"] = np.array(kill_information["p2"])

    return kill_information


def transform_kill_timeline(games, conn):
    kill_timeline = {
        "overall": {"early": [], "mid": [], "late": []},
        "p1": {"early": [], "mid": [], "late": []},
        "p2": {"early": [], "mid": [], "late": []}
    }
    conversion_factor = 60 * 1000  # ms to m
    for idx, game in enumerate(games):
        p1_id, p2_id = game["s1_participantid"], game["s2_participantid"]
        game_kill_timeline = database.select_kill_timeline(conn, game_id=game["gameid"], team_id=game["s1_teamid"])

        kill_timeline_game = {
            "overall": {"early": [], "mid": [], "late": []},
            "p1": {"early": [], "mid": [], "late": []},
            "p2": {"early": [], "mid": [], "late": []}
        }
        for kill in game_kill_timeline:
            participant, game_state = None, None
            kill_time = kill["timestamp"] / conversion_factor

            if kill["killer"] == p1_id:
                participant = "p1"
            elif kill["killer"] == p2_id:
                participant = "p2"

            if kill_time <= 15:
                game_state = "early"
            elif kill_time <= 25:
                game_state = "mid"
            else:
                game_state = "late"

            kill_timeline_game["overall"][game_state].append(np.array(kill_time))
            if participant:
                kill_timeline_game[participant][game_state].append(np.array(kill_time))

        for key in kill_timeline["overall"].keys():
            kill_timeline["overall"][key].append(np.array(kill_timeline_game["overall"][key]))
        for key in kill_timeline["p1"].keys():
            kill_timeline["p1"][key].append(np.array(kill_timeline_game["p1"][key]))
        for key in kill_timeline["p2"].keys():
            kill_timeline["p2"][key].append(np.array(kill_timeline_game["p2"][key]))

    return kill_timeline


def transform_kda_timeline(games, conn):
    kda_timeline = {
        "p1": {"early": [], "mid": [], "late": []},
        "p2": {"early": [], "mid": [], "late": []}
    }
    conversion_factor = 60 * 1000  # ms to m
    for idx, game in enumerate(games):
        p1_id, p2_id = game["s1_participantid"], game["s2_participantid"]
        p1_kda = {"early": [0, 0, 0], "mid": [0, 0, 0], "late": [0, 0, 0]}
        p2_kda = {"early": [0, 0, 0], "mid": [0, 0, 0], "late": [0, 0, 0]}
        game_kill_timeline = database.select_all_kill_timeline(conn, game_id=game["gameid"])

        for kill in game_kill_timeline:
            kill_time = kill["timestamp"] / conversion_factor

            if kill_time <= 15:
                game_state = "early"
            elif kill_time <= 25:
                game_state = "mid"
            else:
                game_state = "late"

            if kill["killer"] == p1_id:
                p1_kda[game_state][0] += 1
            elif kill["killer"] == p2_id:
                p2_kda[game_state][0] += 1

            if kill["victim"] == p1_id:
                p1_kda[game_state][1] += 1
            elif kill["victim"] == p2_id:
                p2_kda[game_state][1] += 1

            if p1_id in kill["assistingparticipantids"]:
                p1_kda[game_state][2] += 1
            elif p2_id in kill["assistingparticipantids"]:
                p2_kda[game_state][2] += 1

        for key in kda_timeline["p1"].keys():
            try:
                kda = (p1_kda[key][0] + p1_kda[key][2]) / p1_kda[key][1]
            except ZeroDivisionError:
                kda = 0
            kda_timeline["p1"][key].append(kda)
        for key in kda_timeline["p2"].keys():
            try:
                kda = (p2_kda[key][0] + p2_kda[key][2]) / p2_kda[key][1]
            except ZeroDivisionError:
                kda = 0
            kda_timeline["p2"][key].append(kda)

    return kda_timeline


def transform_cs_diff(games, conn):
    cs_diff = {
        "p1": np.zeros(shape=(len(games), 15)),
        "p2": np.zeros(shape=(len(games), 15))
    }
    for idx, game in enumerate(games):
        p1_id, p2_id = game["s1_participantid"], game["s2_participantid"]
        lane_opponent_p1, lane_opponent_p2 = get_lane_opponent(participant_id=p1_id, conn=conn), get_lane_opponent(
            participant_id=p2_id, conn=conn)

        if lane_opponent_p1 is None:
            continue
        if lane_opponent_p2 is None:
            continue

        p1_cs_diff = _build_cs_diff_array(p1_id, lane_opponent_p1, conn)
        p2_cs_diff = _build_cs_diff_array(p2_id, lane_opponent_p2, conn)

        game_diff_shape, csd_shape = None, None
        if type(p1_cs_diff) is not list:
            game_diff_shape = p1_cs_diff.shape[0]
            csd_shape = cs_diff["p1"].shape[1]
        if type(p2_cs_diff) is not list:
            game_diff_shape = p2_cs_diff.shape[0]
            csd_shape = cs_diff["p2"].shape[1]

        if game_diff_shape and csd_shape:
            if game_diff_shape < csd_shape:
                cs_diff["p1"][idx, :game_diff_shape] = p1_cs_diff
                cs_diff["p2"][idx, :game_diff_shape] = p2_cs_diff
            else:
                np_zeros = np.zeros([len(games), (game_diff_shape - csd_shape)])
                np_zeros[:] = np.nan
                # If shape of game array is bigger than current shape -> reshape current array to fit all elements
                cs_diff["p1"] = np.hstack((cs_diff["p1"], np_zeros))
                cs_diff["p2"] = np.hstack((cs_diff["p2"], np_zeros))
                cs_diff["p1"][idx, :] = p1_cs_diff
                cs_diff["p2"][idx, :] = p2_cs_diff

    cs_diff["p1"] = np.array(cs_diff["p1"])
    cs_diff["p2"] = np.array(cs_diff["p2"])
    return cs_diff


def build_gold_diff_array(participant_id: str, lane_opponent, conn):
    participant_frames = database.select_participant_frames(conn=conn, participant_id=participant_id)
    opponent_frames = database.select_participant_frames(conn=conn, participant_id=lane_opponent.participant_id)

    p1_game_diff = []
    for index in range(len(participant_frames)):
        p1_game_diff.append(participant_frames[index]["totalgold"] - opponent_frames[index]["totalgold"])

    return np.array(p1_game_diff)


def _build_cs_diff_array(participant_id: str, lane_opponent, conn):
    participant_frames = database.select_participant_frames(conn=conn, participant_id=participant_id)
    opponent_frames = database.select_participant_frames(conn=conn, participant_id=lane_opponent.participant_id)

    cs_diff = []
    for index in range(len(participant_frames)):
        cs_diff.append(participant_frames[index]["minionskilled"] - opponent_frames[index]["minionskilled"])
    return np.array(cs_diff)


def get_lane_opponent(participant_id, conn):
    participant = database.select_participant(conn, participant_id=participant_id)
    lane_opponent = database.select_opponent(
        conn, participant_id=participant_id, game_id=participant.game_id, position=(participant.lane, participant.role)
    )
    return lane_opponent
