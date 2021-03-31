import math


class GameState:
    EARLY = (0, 10)
    MID = (11, 20)
    LATE = (21, 100)


class Constants:
    DIST_EPS = 1000
    TIME = 60000
    FIGHT_RADIUS = 1500


class FightType:
    TEAM_FIGHT = 0
    GANK = 1
    SOLO = 2


class Map:
    WIDTH = 14870
    HEIGHT = 14980
    CENTER = (7435, 7490)
    HALF_DIST = 10553.64


class Role:
    TOP = "TOP"
    JGL = "JUNGLE"
    MID = "MIDDLE"
    BOT = "BOTTOM"
    SUP = "SUPPORT"


class KP:
    MU = 0.37978395687423944
    VAR = 0.1
    SIG = math.sqrt(VAR)


class FWK:
    MU = 0.14572601361611762
    VAR = 0.015588149363684151
    SIG = math.sqrt(VAR)


class POS:
    MU = 0.38481458653172423
    VAR = 0.0054917803057248395
    SIG = math.sqrt(VAR)


class Ganking:
    MU = 0.5900199271514704
    VAR = 0.035544521958908885
    SIG = math.sqrt(VAR)
