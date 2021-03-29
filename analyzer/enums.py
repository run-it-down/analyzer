class GameState:
    EARLY = (0, 10)
    MID = (11, 20)
    LATE = (21, 100)


class Constants:
    DIST_EPS = 1000
    TIME = 60000
    FIGHT_RADIUS = 100


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
