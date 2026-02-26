"""Shared fixtures for JaxStats tests."""

import pytest


def make_participant(
    puuid="player1",
    summoner_id="summ1",
    summoner_name="TestPlayer",
    champion_name="Jinx",
    champion_id=222,
    team_id=100,
    team_position="BOTTOM",
    individual_position="BOTTOM",
    win=True,
    kills=8,
    deaths=3,
    assists=10,
    total_damage_dealt_to_champions=22000,
    total_damage_taken=18000,
    gold_earned=14500,
    vision_score=35,
    time_ccing_others=12,
    total_time_spent_dead=120,
    double_kills=2,
    triple_kills=0,
    quadra_kills=0,
    penta_kills=0,
    total_minions_killed=180,
    neutral_minions_killed=20,
    total_damage_dealt=150000,
    magic_damage_dealt=5000,
    physical_damage_dealt=140000,
    true_damage_dealt=5000,
    damage_self_mitigated=8000,
    wards_placed=10,
    wards_killed=5,
    detector_wards_placed=3,
    killing_sprees=2,
    longest_time_spent_living=800,
    damage_dealt_to_objectives=12000,
    gold_spent=13000,
    game_ended_in_surrender=False,
    game_ended_in_early_surrender=False,
    challenges_overrides=None,
    **extra,
):
    """Build a realistic participant dict matching Riot API format."""
    challenges = {
        "killParticipation": 0.65,
        "teamDamagePercentage": 0.28,
        "damageTakenOnTeamPercentage": 0.20,
        "soloKills": 2,
        "multikills": 1,
        "turretTakedowns": 3,
        "dragonTakedowns": 2,
        "baronTakedowns": 1,
        "riftHeraldTakedowns": 1,
        "visionScorePerMinute": 1.1,
        "skillshotsHit": 45,
        "skillshotsDodged": 20,
        "abilityUses": 150,
        "enemyChampionImmobilizations": 8,
        "saveAllyFromDeath": 1,
        "effectiveHealAndShielding": 3000,
        "survivedSingleDigitHpCount": 2,
        "survivedThreeImmobilizesInFight": 1,
        "outnumberedKills": 1,
        "laneMinionsFirst10Minutes": 65,
        "takedownsFirstXMinutes": 5,
        "maxCsAdvantageOnLaneOpponent": 15,
        "maxLevelLeadLaneOpponent": 1,
        "turretPlatesTaken": 2,
        "earlyLaningPhaseGoldExpAdvantage": 1,
        "laningPhaseGoldExpAdvantage": 1,
        "epicMonsterSteals": 0,
        "epicMonsterStolenWithoutSmite": 0,
        "multikillsAfterAggressiveFlash": 0,
        "perfectGame": 0,
        "legendaryCount": 0,
        "controlWardTimeCoverageInRiverOrEnemyHalf": 0.15,
        "visionScoreAdvantageLaneOpponent": 3.5,
        "unseenRecalls": 1,
        "twoWardsOneSweeperCount": 2,
        "wardTakedownsBefore20M": 3,
        "buffsStolen": 0,
        "enemyJungleMonsterKills": 0,
        "moreEnemyJungleThanOpponent": 0,
        "epicMonsterKillsWithin30SecondsOfSpawn": 0,
        "jungleCsBefore10Minutes": 0,
        "initialBuffCount": 0,
        "initialCrabCount": 0,
        "scuttleCrabKills": 0,
        "killedChampTookFullTeamDamageSurvived": 0,
        "tookLargeDamageSurvived": 1,
        "completeSupportQuestInTime": 0,
    }
    if challenges_overrides:
        challenges.update(challenges_overrides)

    participant = {
        "puuid": puuid,
        "summonerId": summoner_id,
        "summonerName": summoner_name,
        "championId": champion_id,
        "championName": champion_name,
        "teamId": team_id,
        "teamPosition": team_position,
        "individualPosition": individual_position,
        "win": win,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "totalDamageDealtToChampions": total_damage_dealt_to_champions,
        "totalDamageTaken": total_damage_taken,
        "goldEarned": gold_earned,
        "visionScore": vision_score,
        "timeCCingOthers": time_ccing_others,
        "totalTimeSpentDead": total_time_spent_dead,
        "doubleKills": double_kills,
        "tripleKills": triple_kills,
        "quadraKills": quadra_kills,
        "pentaKills": penta_kills,
        "totalMinionsKilled": total_minions_killed,
        "neutralMinionsKilled": neutral_minions_killed,
        "totalDamageDealt": total_damage_dealt,
        "magicDamageDealt": magic_damage_dealt,
        "physicalDamageDealt": physical_damage_dealt,
        "trueDamageDealt": true_damage_dealt,
        "damageSelfMitigated": damage_self_mitigated,
        "wardsPlaced": wards_placed,
        "wardsKilled": wards_killed,
        "detectorWardsPlaced": detector_wards_placed,
        "killingSprees": killing_sprees,
        "longestTimeSpentLiving": longest_time_spent_living,
        "damageDealtToObjectives": damage_dealt_to_objectives,
        "goldSpent": gold_spent,
        "gameEndedInSurrender": game_ended_in_surrender,
        "gameEndedInEarlySurrender": game_ended_in_early_surrender,
        "totalDamageShieldedOnTeammates": 0,
        "totalHealsOnTeammates": 0,
        "allInPings": 2,
        "assistMePings": 3,
        "commandPings": 5,
        "dangerPings": 4,
        "enemyMissingPings": 6,
        "enemyVisionPings": 1,
        "getBackPings": 2,
        "holdPings": 0,
        "needVisionPings": 1,
        "onMyWayPings": 7,
        "pushPings": 3,
        "perks": {
            "statPerks": {"defense": 5002, "flex": 5008, "offense": 5005},
            "styles": [
                {
                    "description": "primaryStyle",
                    "selections": [
                        {"perk": 8005, "var1": 1000, "var2": 0, "var3": 0},
                        {"perk": 8008, "var1": 20, "var2": 0, "var3": 0},
                        {"perk": 9103, "var1": 10, "var2": 0, "var3": 0},
                        {"perk": 8017, "var1": 500, "var2": 0, "var3": 0},
                    ],
                    "style": 8000,
                },
                {
                    "description": "subStyle",
                    "selections": [
                        {"perk": 8139, "var1": 600, "var2": 0, "var3": 0},
                        {"perk": 8135, "var1": 2000, "var2": 0, "var3": 0},
                    ],
                    "style": 8100,
                },
            ],
        },
        "challenges": challenges,
    }
    participant.update(extra)
    return participant


def make_match_data(
    match_id="NA1_5000000001",
    game_duration=1800,
    game_start_timestamp=1700000000000,
    participants=None,
    queue_id=420,
):
    """Build a realistic match data dict matching Riot API format."""
    if participants is None:
        # Default: 10 players, player1 on team 100
        participants = []
        blue_champs = ["Jinx", "Thresh", "Ahri", "Lee Sin", "Garen"]
        red_champs = ["Caitlyn", "Lulu", "Syndra", "Elise", "Darius"]
        positions = ["BOTTOM", "UTILITY", "MIDDLE", "JUNGLE", "TOP"]

        for i, (champ, pos) in enumerate(zip(blue_champs, positions)):
            participants.append(
                make_participant(
                    puuid=f"player{i + 1}",
                    summoner_name=f"Player{i + 1}",
                    champion_name=champ,
                    team_id=100,
                    team_position=pos,
                    individual_position=pos,
                    win=True,
                    kills=5 + i,
                    deaths=2 + i,
                    assists=8 - i,
                )
            )
        for i, (champ, pos) in enumerate(zip(red_champs, positions)):
            participants.append(
                make_participant(
                    puuid=f"enemy{i + 1}",
                    summoner_name=f"Enemy{i + 1}",
                    champion_name=champ,
                    team_id=200,
                    team_position=pos,
                    individual_position=pos,
                    win=False,
                    kills=3 + i,
                    deaths=4 + i,
                    assists=5 - i,
                )
            )

    return {
        "metadata": {
            "dataVersion": "2",
            "matchId": match_id,
            "participants": [p["puuid"] for p in participants],
        },
        "info": {
            "gameId": int(match_id.split("_")[1]) if "_" in match_id else 5000000001,
            "gameCreation": game_start_timestamp - 60000,
            "gameDuration": game_duration,
            "gameEndTimestamp": game_start_timestamp + game_duration * 1000,
            "gameStartTimestamp": game_start_timestamp,
            "gameMode": "CLASSIC",
            "gameType": "MATCHED_GAME",
            "gameVersion": "14.1.1",
            "mapId": 11,
            "participants": participants,
            "teams": [
                {
                    "teamId": 100,
                    "win": True,
                    "objectives": {
                        "baron": {"first": True, "kills": 1},
                        "dragon": {"first": True, "kills": 3},
                        "tower": {"first": True, "kills": 8},
                    },
                },
                {
                    "teamId": 200,
                    "win": False,
                    "objectives": {
                        "baron": {"first": False, "kills": 0},
                        "dragon": {"first": False, "kills": 1},
                        "tower": {"first": False, "kills": 3},
                    },
                },
            ],
            "queueId": queue_id,
        },
    }


@pytest.fixture
def sample_participant():
    """A single participant dict."""
    return make_participant()


@pytest.fixture
def sample_match_data():
    """A full 10-player match dict."""
    return make_match_data()


@pytest.fixture
def multiple_match_data():
    """Multiple matches for trend / multi-match testing."""
    matches = []
    for i in range(5):
        win = i % 2 == 0  # alternating wins
        matches.append(
            make_match_data(
                match_id=f"NA1_500000000{i + 1}",
                game_duration=1800 + i * 60,
                game_start_timestamp=1700000000000 + i * 3600000,
                participants=[
                    make_participant(
                        puuid="player1",
                        champion_name=["Jinx", "Caitlyn", "Ezreal", "Jinx", "Vayne"][i],
                        team_position="BOTTOM",
                        individual_position="BOTTOM",
                        win=win,
                        kills=5 + i,
                        deaths=3 + (i % 3),
                        assists=8 - i,
                        vision_score=20 + i * 5,
                        total_damage_dealt_to_champions=15000 + i * 2000,
                        gold_earned=12000 + i * 1000,
                    )
                ]
                + [
                    make_participant(
                        puuid=f"other{j}",
                        champion_name=f"Champ{j}",
                        team_id=100 if j < 5 else 200,
                        win=win if j < 5 else not win,
                    )
                    for j in range(1, 10)
                ],
            )
        )
    return matches
