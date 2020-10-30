import os

import psycopg2

import model


def get_connection(
        database=os.getenv('DB'),
        user=os.getenv('DBUSER'),
        password=os.getenv('DBPASSWD'),
        host=os.getenv('DBHOST'),
        port=int(os.getenv('DBPORT')),
):
    return psycopg2.connect(
        database=database,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def kill_connection(conn):
    try:
        conn.close()
    except psycopg2.Error:
        pass


def _execute(
    conn,
    statement: str,
    values: tuple,
    print_exception: bool = True,
):
    cur = conn.cursor()
    try:
        cur.execute(statement, values)
    except psycopg2.Error as e:
        if print_exception:
            print(e)
        cur.execute("rollback")
        conn.commit()
    return cur


def select_summoner(conn,
                    summoner_name: str,
                    ):
    statement = "SELECT * FROM summoners " \
                "WHERE name = %s"
    values = (summoner_name,)

    cur = _execute(
        conn=conn,
        statement=statement,
        values=values,
    )

    conn.commit()
    res = cur.fetchone()
    return model.Summoner(
        account_id=res[0],
        profile_icon_id=res[1],
        revision_date=res[2],
        name=res[3],
        id=res[4],
        puuid=res[5],
        summoner_level=res[6],
    )


def select_stat_from_participant(conn,
                                 summoner: model.Summoner,
                                 ):
    statement = "SELECT statid FROM participants " \
                "WHERE accountid = %s"
    values = (summoner.account_id,)

    cur = _execute(
        conn=conn,
        statement=statement,
        values=values,
    )

    return cur.fetchall()


def select_stats(conn,
                 statid: str,
                 ):
    statement = "SELECT * FROM stats " \
                "WHERE statid = %s"
    values = (statid,)

    cur = _execute(
        conn=conn,
        statement=statement,
        values=values,
    )

    stat_raw = cur.fetchone()

    return model.Stat(
        stat_id=stat_raw[0],
        win=stat_raw[1],
        items=stat_raw[2],
        kills=stat_raw[3],
        deaths=stat_raw[4],
        assists=stat_raw[5],
        largestKillingSpree=stat_raw[6],
        largestMultiKill=stat_raw[7],
        killingSprees=stat_raw[8],
        longestTimeSpentLiving=stat_raw[9],
        doubleKills=stat_raw[10],
        tripleKills=stat_raw[11],
        quadraKills=stat_raw[12],
        pentaKills=stat_raw[13],
        unrealKills=stat_raw[14],
        totalDamageDealt=stat_raw[15],
        magicDamageDealt=stat_raw[16],
        physicalDamageDealt=stat_raw[17],
        trueDamageDealt=stat_raw[18],
        largestCriticalStrike=stat_raw[19],
        totalDamageDealtToChampions=stat_raw[20],
        magicDamageDealtToChampions=stat_raw[21],
        physicalDamageDealtToChampions=stat_raw[22],
        trueDamageDealtToChampions=stat_raw[23],
        totalHeal=stat_raw[24],
        totalUnitsHealed=stat_raw[25],
        damageSelfMitigated=stat_raw[26],
        damageDealtToObjectives=stat_raw[27],
        damageDealtToTurrets=stat_raw[28],
        visionScore=stat_raw[29],
        timeCCingOthers=stat_raw[30],
        totalDamageTaken=stat_raw[31],
        magicalDamageTaken=stat_raw[32],
        physicalDamageTaken=stat_raw[33],
        trueDamageTaken=stat_raw[34],
        goldEarned=stat_raw[35],
        goldSpent=stat_raw[36],
        turretKills=stat_raw[37],
        inhibitorKills=stat_raw[38],
        totalMinionsKilled=stat_raw[39],
        neutralMinionsKilledTeamJungle=stat_raw[40],
        neutralMinionsKilledEnemyJungle=stat_raw[41],
        totalTimeCrowdControlDealt=stat_raw[42],
        champLevel=stat_raw[43],
        visionWardsBoughtInGame=stat_raw[44],
        sightWardsBoughtInGame=stat_raw[45],
        wardsPlaced=stat_raw[46],
        wardsKilled=stat_raw[47],
        firstBloodKill=stat_raw[48],
        firstBloodAssist=stat_raw[49],
        firstTowerKill=stat_raw[50],
        firstTowerAssist=stat_raw[51],
        firstInhibitorKill=stat_raw[52],
        firstInhibitorAssist=stat_raw[53],
        combatPlayerScore=stat_raw[54],
        objectivePlayerScore=stat_raw[55],
        totalPlayerScore=stat_raw[56],
        totalScoreRank=stat_raw[57],
        playerScore0=stat_raw[58],
        playerScore1=stat_raw[59],
        playerScore2=stat_raw[60],
        playerScore3=stat_raw[61],
        playerScore4=stat_raw[62],
        playerScore5=stat_raw[63],
        playerScore6=stat_raw[64],
        playerScore7=stat_raw[65],
        playerScore8=stat_raw[66],
        playerScore9=stat_raw[67],
        perk0=stat_raw[68],
        perk0Var1=stat_raw[69],
        perk0Var2=stat_raw[70],
        perk0Var3=stat_raw[71],
        perk1=stat_raw[72],
        perk1Var1=stat_raw[73],
        perk1Var2=stat_raw[74],
        perk1Var3=stat_raw[75],
        perk2=stat_raw[76],
        perk2Var1=stat_raw[77],
        perk2Var2=stat_raw[78],
        perk2Var3=stat_raw[79],
        perk3=stat_raw[80],
        perk3Var1=stat_raw[81],
        perk3Var2=stat_raw[82],
        perk3Var3=stat_raw[83],
        perk4=stat_raw[84],
        perk4Var1=stat_raw[85],
        perk4Var2=stat_raw[86],
        perk4Var3=stat_raw[87],
        perk5=stat_raw[88],
        perk5Var1=stat_raw[89],
        perk5Var2=stat_raw[90],
        perk5Var3=stat_raw[91],
        perkPrimaryStyle=stat_raw[92],
        perkSubStyle=stat_raw[93],
        statPerk0=stat_raw[94],
        statPerk1=stat_raw[95],
        statPerk2=stat_raw[96],
    )
