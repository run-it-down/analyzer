import dataclasses
from dataclasses_json import dataclass_json
import typing


@dataclasses.dataclass
class Summoner:
    account_id: str
    profile_icon_id: int
    revision_date: int
    name: str
    id: str
    puuid: str
    summoner_level: int


@dataclasses.dataclass
class MatchReference:
    game_id: int
    role: str
    season: int
    platform_id: str
    champion: int
    queue: int
    lane: str
    timestamp: int


@dataclasses.dataclass
class Matchlist:
    start_index: int
    #  	There is a known issue that this field doesn't correctly return the total number of games
    #  	that match the parameters of the request. Please paginate using beginIndex until you reach
    #  	the end of a player's matchlist.
    # total_games: int
    end_index: int
    match_references: typing.List[MatchReference]


@dataclasses.dataclass
class Champion:
    id: int
    name: str


@dataclasses.dataclass
class Team:
    team_id: str
    win: str
    first_blood: int
    first_tower: int
    first_inhibitor: int
    first_baron: int
    first_dragon: int
    first_rift_herald: int
    tower_kills: int
    inhibitor_kills: int
    baron_kills: int
    dragon_kills: int
    vilemaw_kills: int
    rift_herald_kills: int
    dominion_victory_score: int
    bans: typing.List[int]


@dataclasses.dataclass
class Timeline:
    timeline_id: str
    creepsPerMinDeltas: dict
    xpPerMinDeltas: dict
    goldPerMinDeltas: dict
    csDiffPerMinDeltas: dict
    xpDiffPerMinDeltas: dict
    damageTakenPerMinDeltas: dict
    damageTakenDiffPerMinDeltas: dict


@dataclass_json
@dataclasses.dataclass
class Stat:
    stat_id: str
    win: bool
    items: typing.List[int]
    kills: int
    deaths: int
    assists: int
    largestKillingSpree: int
    largestMultiKill: int
    killingSprees: int
    longestTimeSpentLiving: int
    doubleKills: int
    tripleKills: int
    quadraKills: int
    pentaKills: int
    unrealKills: int
    totalDamageDealt: int
    magicDamageDealt: int
    physicalDamageDealt: int
    trueDamageDealt: int
    largestCriticalStrike: int
    totalDamageDealtToChampions: int
    magicDamageDealtToChampions: int
    physicalDamageDealtToChampions: int
    trueDamageDealtToChampions: int
    totalHeal: int
    totalUnitsHealed: int
    damageSelfMitigated: int
    damageDealtToObjectives: int
    damageDealtToTurrets: int
    visionScore: int
    timeCCingOthers: int
    totalDamageTaken: int
    magicalDamageTaken: int
    physicalDamageTaken: int
    trueDamageTaken: int
    goldEarned: int
    goldSpent: int
    turretKills: int
    inhibitorKills: int
    totalMinionsKilled: int
    neutralMinionsKilledTeamJungle: int
    neutralMinionsKilledEnemyJungle: int
    totalTimeCrowdControlDealt: int
    champLevel: int
    visionWardsBoughtInGame: int
    sightWardsBoughtInGame: int
    wardsPlaced: int
    wardsKilled: int
    firstBloodKill: bool
    firstBloodAssist: bool
    firstTowerKill: bool
    firstTowerAssist: bool
    firstInhibitorKill: bool
    firstInhibitorAssist: bool
    combatPlayerScore: int
    objectivePlayerScore: int
    totalPlayerScore: int
    totalScoreRank: int
    playerScore0: int
    playerScore1: int
    playerScore2: int
    playerScore3: int
    playerScore4: int
    playerScore5: int
    playerScore6: int
    playerScore7: int
    playerScore8: int
    playerScore9: int
    perk0: int
    perk0Var1: int
    perk0Var2: int
    perk0Var3: int
    perk1: int
    perk1Var1: int
    perk1Var2: int
    perk1Var3: int
    perk2: int
    perk2Var1: int
    perk2Var2: int
    perk2Var3: int
    perk3: int
    perk3Var1: int
    perk3Var2: int
    perk3Var3: int
    perk4: int
    perk4Var1: int
    perk4Var2: int
    perk4Var3: int
    perk5: int
    perk5Var1: int
    perk5Var2: int
    perk5Var3: int
    perkPrimaryStyle: int
    perkSubStyle: int
    statPerk0: int
    statPerk1: int
    statPerk2: int


@dataclasses.dataclass
class Participant:
    participant_id: str
    team_id: str
    account_id: str
    champion_id: int
    spell1_id: int
    spell2_id: int
    stat: Stat
    timeline: Timeline


@dataclasses.dataclass
class Match:
    game_id: str
    platform_id: str
    game_creation: int
    game_duration: int
    queue_id: int
    map_id: int
    season_id: int
    game_version: str
    game_mode: str
    game_type: str
    teams: typing.List[Team]
    participants: typing.List[Participant]
