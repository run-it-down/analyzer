import json

import analysis
import database
import numpy as np
import util

logger = util.Logger(__name__)


class WinRate:
    def on_get(self, req, resp):
        logger.info('GET /winrate')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params["summoner2"])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        wr = analysis.base_analysis.win_rate(common_games)

        resp.body = json.dumps({
            "win_rate": wr
        })


class KDA:
    def on_get(self, req, resp):
        logger.info('GET /kda')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn,
                                             summoner_name=params['summoner2'])
        common_games = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        kdas = {
            summoner1.name: {"kda": 0, "kills": 0, "deaths": 0, "assists": 0},
            summoner2.name: {"kda": 0, "kills": 0, "deaths": 0, "assists": 0},
        }
        for game in common_games:
            p1_stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            p2_stats = database.select_stats(conn=conn, statid=game["s2_statid"])

            kdas[summoner1.name]["kills"] += p1_stats.kills
            kdas[summoner1.name]["deaths"] += p1_stats.deaths
            kdas[summoner1.name]["assists"] += p1_stats.assists

            kdas[summoner2.name]["kills"] += p2_stats.kills
            kdas[summoner2.name]["deaths"] += p2_stats.deaths
            kdas[summoner2.name]["assists"] += p2_stats.assists

        kdas[summoner1.name]["kda"] = analysis.base_analysis.avg_kda(
            kills=kdas[summoner1.name]["kills"],
            deaths=kdas[summoner1.name]["deaths"],
            assists=kdas[summoner1.name]["assists"],
        )
        kdas[summoner2.name]["kda"] = analysis.base_analysis.avg_kda(
            kills=kdas[summoner2.name]["kills"],
            deaths=kdas[summoner2.name]["deaths"],
            assists=kdas[summoner2.name]["assists"],
        )

        resp.body = json.dumps(kdas)


class CreepScore:
    def on_get(self, req, resp):
        logger.info('GET /cs')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn, summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn, summoner_name=params['summoner2'])
        common_game_stats = database.select_common_game_stats(conn=conn, s1=summoner1, s2=summoner2)

        cs = {summoner1.name: 0, summoner2.name: 0}
        for game in common_game_stats:
            cs[summoner1.name] += game["s1_totalminionskilled"]
            cs[summoner2.name] += game["s2_totalminionskilled"]

        cs[summoner1.name] = cs[summoner1.name] / len(common_game_stats)
        cs[summoner2.name] = cs[summoner2.name] / len(common_game_stats)

        resp.body = json.dumps(cs)


class AverageRole:
    def on_get(self, req, resp):
        logger.info('GET /average_role')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn, summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn, summoner_name=params['summoner2'])
        common_game = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        p1_role = analysis.base_analysis.determine_avg_role(games=common_game, role_key="s1_role", lane_key="s1_lane")
        p2_role = analysis.base_analysis.determine_avg_role(games=common_game, role_key="s2_role", lane_key="s2_lane")

        resp.body = json.dumps({
            summoner1.name: p1_role,
            summoner2.name: p2_role
        })


class GoldDifference:
    def on_get(self, req, resp):
        logger.info('GET /gold-diffference')
        params = req.params
        conn = database.get_connection()

        summoner1 = database.select_summoner(conn=conn, summoner_name=params['summoner1'])
        summoner2 = database.select_summoner(conn=conn, summoner_name=params['summoner2'])
        common_game = database.select_common_games(conn=conn, s1=summoner1, s2=summoner2)

        gold_diff = {
            summoner1.name: {"overall": [], "early": [], "mid": [], "late": []},
            summoner2.name: {"overall": [], "early": [], "mid": [], "late": []}
        }
        for game in common_game:
            p1_frames = database.select_participant_frames(conn=conn, participant_id=game["s1_participantid"])
            p1_opponent = database.select_opponent(
                conn=conn,
                participant_id=game["s1_participantid"],
                game_id=game["gameid"],
                position=(game["s1_lane"], game["s1_role"])
            )
            if p1_opponent is None:
                continue
            p1_opponent_frames = database.select_participant_frames(conn=conn, participant_id=p1_opponent.participant_id)

            p2_frames = database.select_participant_frames(conn=conn, participant_id=game["s2_participantid"])
            p2_opponent = database.select_opponent(
                conn=conn,
                participant_id=game["s2_participantid"],
                game_id=game["gameid"],
                position=(game["s2_lane"], game["s2_role"])
            )
            if p2_opponent is None:
                continue
            p2_opponent_frames = database.select_participant_frames(conn=conn, participant_id=p2_opponent.participant_id)

            p1_gold_diff = analysis.base_analysis.gold_diff(frames=p1_frames, opponent_frames=p1_opponent_frames)
            p2_gold_diff = analysis.base_analysis.gold_diff(frames=p2_frames, opponent_frames=p2_opponent_frames)

            gold_diff[summoner1.name]["overall"].append(p1_gold_diff["overall"])
            gold_diff[summoner1.name]["early"].append(p1_gold_diff["early"])
            gold_diff[summoner1.name]["mid"].append(p1_gold_diff["mid"])
            gold_diff[summoner1.name]["late"].append(p1_gold_diff["late"])

            gold_diff[summoner2.name]["overall"].append(p2_gold_diff["overall"])
            gold_diff[summoner2.name]["early"].append(p2_gold_diff["early"])
            gold_diff[summoner2.name]["mid"].append(p2_gold_diff["mid"])
            gold_diff[summoner2.name]["late"].append(p2_gold_diff["late"])

        gold_diff[summoner1.name]["overall"] = np.nanmean(np.array(gold_diff[summoner1.name]["overall"]))
        gold_diff[summoner1.name]["early"] = np.nanmean(np.array(gold_diff[summoner1.name]["early"]))
        gold_diff[summoner1.name]["mid"] = np.nanmean(np.array(gold_diff[summoner1.name]["mid"]))
        gold_diff[summoner1.name]["late"] = np.nanmean(np.array(gold_diff[summoner1.name]["late"]))

        gold_diff[summoner2.name]["overall"] = np.nanmean(np.array(gold_diff[summoner2.name]["overall"]))
        gold_diff[summoner2.name]["early"] = np.nanmean(np.array(gold_diff[summoner2.name]["early"]))
        gold_diff[summoner2.name]["mid"] = np.nanmean(np.array(gold_diff[summoner2.name]["mid"]))
        gold_diff[summoner2.name]["late"] = np.nanmean(np.array(gold_diff[summoner2.name]["late"]))

        resp.body = json.dumps(gold_diff)


class AverageGame:
    def on_get(self, req, resp):
        logger.info('GET /avg-game')
        params = req.params
        conn = database.get_connection()

        average_game = {
            'summoners': [
                {
                    'summoner': params['summoner1'],
                    'kda': 0,
                    'role': None,
                },
                {
                    'summoner': params['summoner2'],
                    'kda': 0,
                    'role': None,
                }
            ],
            'common': {
                'winrate': None,
                'bans': None,
                'drakes': None,
                'nash': None,
                'heralds': None,
                'first_blood': None,
                'first_tower': None,
                'first_inhib': None,
                'first_baron': None,
                'first_dragon': None,
                'first_herald': None,
            }
        }

        summoner1 = database.select_summoner(
            conn=conn,
            summoner_name=params['summoner1'],
        )
        summoner2 = database.select_summoner(
            conn=conn,
            summoner_name=params['summoner2'],
        )
        common_games = database.select_common_games(
            conn=conn,
            s1=summoner1,
            s2=summoner2,
        )

        common_stats = analysis.base_analysis.common_stats(
            common_games=common_games,
        )
        average_game['common']['drakes'] = common_stats['drakes']
        average_game['common']['nash'] = common_stats['nash']
        average_game['common']['heralds'] = common_stats['heralds']
        average_game['common']['first_blood'] = common_stats['first_blood']
        average_game['common']['first_tower'] = common_stats['first_tower']
        average_game['common']['first_inhib'] = common_stats['first_inhib']
        average_game['common']['first_baron'] = common_stats['first_baron']
        average_game['common']['first_dragon'] = common_stats['first_dragon']
        average_game['common']['first_herald'] = common_stats['first_herald']
        average_game['common']['bans'] = database.select_champion_name_id(
            conn=conn,
            champ_id=common_stats['bans'],
        )[1]

        # roles
        average_game['summoners'][0]['role'] = analysis.base_analysis.determine_avg_role(
            games=common_games,
            role_key="s1_role",
            lane_key="s1_lane",
        )
        average_game['summoners'][1]['role'] = analysis.base_analysis.determine_avg_role(
            games=common_games,
            role_key="s2_role",
            lane_key="s2_lane",
        )

        # kda
        kdas = {
            summoner1.name: {"kda": 0, "kills": 0, "deaths": 0, "assists": 0},
            summoner2.name: {"kda": 0, "kills": 0, "deaths": 0, "assists": 0},
        }
        for game in common_games:
            p1_stats = database.select_stats(conn=conn, statid=game["s1_statid"])
            p2_stats = database.select_stats(conn=conn, statid=game["s2_statid"])

            kdas[summoner1.name]["kills"] += p1_stats.kills
            kdas[summoner1.name]["deaths"] += p1_stats.deaths
            kdas[summoner1.name]["assists"] += p1_stats.assists

            kdas[summoner2.name]["kills"] += p2_stats.kills
            kdas[summoner2.name]["deaths"] += p2_stats.deaths
            kdas[summoner2.name]["assists"] += p2_stats.assists

        average_game['summoners'][0]['kda'] = analysis.base_analysis.avg_kda(
            kills=kdas[summoner1.name]["kills"],
            deaths=kdas[summoner1.name]["deaths"],
            assists=kdas[summoner1.name]["assists"],
        )
        average_game['summoners'][1]['kda'] = analysis.base_analysis.avg_kda(
            kills=kdas[summoner2.name]["kills"],
            deaths=kdas[summoner2.name]["deaths"],
            assists=kdas[summoner2.name]["assists"],
        )

        # cs
        average_game['summoners'][0]['role'] = analysis.base_analysis.determine_avg_role(
            games=common_games,
            role_key="s1_role",
            lane_key="s1_lane",
        )
        average_game['summoners'][1]['role'] = analysis.base_analysis.determine_avg_role(
            games=common_games,
            role_key="s2_role",
            lane_key="s2_lane",
        )

        # winrate
        wr = analysis.base_analysis.win_rate(common_games)
        average_game['common']['winrate'] = f'{str(wr * 100).replace(".0", "")}%'

        resp.body = json.dumps(average_game)


class CommonGames:
    def on_get(self, req, resp):
        logger.info('GET /common-games')
        params = req.params
        conn = database.get_connection()
        summoner1 = database.select_summoner(
            conn=conn,
            summoner_name=params['summoner1'],
        )
        summoner2 = database.select_summoner(
            conn=conn,
            summoner_name=params['summoner2'],
        )
        common_games = database.select_common_games(
            conn=conn,
            s1=summoner1,
            s2=summoner2,
        )

        matches = []
        for game in common_games:
            match = database.select_general_game_info(conn=conn, game_id=game["gameid"])
            if match is not None:
                matches.append(match)

        game_info = analysis.base_analysis.aggregate_game_info(matches)

        resp.body = json.dumps(game_info)
