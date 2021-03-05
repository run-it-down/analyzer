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

        p1_game_gold_diff = build_gold_diff_array(p1_id, lane_opponent_p1, conn) if lane_opponent_p1 is not None else []
        p2_game_gold_diff = build_gold_diff_array(p2_id, lane_opponent_p2, conn) if lane_opponent_p2 is not None else []

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
                gold_diff["p1"] = np.hstack((gold_diff["p1"], np.zeros((len(games), (game_diff_shape - gold_diff_shape)))))
                gold_diff["p2"] = np.hstack((gold_diff["p2"], np.zeros((len(games), (game_diff_shape - gold_diff_shape)))))
                gold_diff["p1"][idx, :] = p1_game_gold_diff
                gold_diff["p2"][idx, :] = p2_game_gold_diff
    return gold_diff


def build_gold_diff_array(participant_id: str, lane_opponent, conn):
    participant_frames = database.select_participant_frames(conn=conn, participant_id=participant_id)
    opponent_frames = database.select_participant_frames(conn=conn, participant_id=lane_opponent.participant_id)

    p1_game_diff = []
    for index in range(len(participant_frames)):
        p1_game_diff.append(participant_frames[index]["totalgold"] - opponent_frames[index]["totalgold"])

    return np.array(p1_game_diff)


def get_lane_opponent(participant_id, conn):
    participant = database.select_participant(conn, participant_id=participant_id)
    lane_opponent = database.select_opponent(
        conn, participant_id=participant_id, game_id=participant.game_id, position=(participant.lane, participant.role)
    )
    return lane_opponent


def get_canonic_lane(lane: str, role: str):
    role_mapping = {
        ("MIDDLE", "SOLO"): "MIDDLE",
        ("TOP", "SOLO"): "TOP",
        ("JUNGLE", "NONE"): "JUNGLE",
        ("BOTTOM", "DUO_CARRY"): "BOTTOM",
        ("BOTTOM", "SOLO"): "BOTTOM",
        ("BOTTOM", "DUO_SUPPORT"): "SUPPORT"
    }
    return role_mapping[(lane, role)]
