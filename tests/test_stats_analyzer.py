"""Tests for app.analysis.stats_analyzer."""

import pytest
from app.analysis.stats_analyzer import StatsAnalyzer
from tests.conftest import make_match_data, make_participant


class TestStatsAnalyzerParsing:
    """Test match data parsing."""

    def test_add_match_populates_matches_list(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        assert len(analyzer.matches) == 1
        assert len(analyzer.raw_matches) == 1

    def test_parsed_match_has_correct_metadata(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        match = analyzer.matches[0]
        assert match.metadata.matchId == "NA1_5000000001"
        assert len(match.metadata.participants) == 10

    def test_parsed_match_has_10_participants(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        assert len(analyzer.matches[0].info.participants) == 10

    def test_parsed_participant_fields(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        p = analyzer.matches[0].info.participants[0]
        assert p.puuid == "player1"
        assert p.championName == "Jinx"
        assert p.teamId == 100
        assert p.win is True

    def test_parsed_teams(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        teams = analyzer.matches[0].info.teams
        assert len(teams) == 2
        assert teams[0].win is True
        assert teams[1].win is False

    def test_parsed_perks(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        p = analyzer.matches[0].info.participants[0]
        assert p.perks.statPerks.offense == 5005
        assert len(p.perks.styles) == 2


class TestGetPlayerStats:
    """Test aggregated player stats."""

    def test_no_puuid_returns_empty(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        # puuid not set
        stats = analyzer.get_player_stats()
        assert stats["total_matches"] == 0

    def test_basic_stats_single_match(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        analyzer.add_match(sample_match_data)
        stats = analyzer.get_player_stats()
        assert stats["total_matches"] == 1
        assert stats["wins"] == 1
        assert stats["losses"] == 0
        assert stats["win_rate"] == 100.0

    def test_kda_calculation(self):
        match = make_match_data(participants=[
            make_participant(puuid="p1", kills=10, deaths=2, assists=6, win=True),
        ] + [make_participant(puuid=f"o{i}", win=True) for i in range(9)])
        analyzer = StatsAnalyzer()
        analyzer.puuid = "p1"
        analyzer.add_match(match)
        stats = analyzer.get_player_stats()
        # (10 + 6) / 2 = 8.0
        assert stats["kda"] == 8.0

    def test_kda_zero_deaths(self):
        match = make_match_data(participants=[
            make_participant(puuid="p1", kills=5, deaths=0, assists=3, win=True),
        ] + [make_participant(puuid=f"o{i}", win=True) for i in range(9)])
        analyzer = StatsAnalyzer()
        analyzer.puuid = "p1"
        analyzer.add_match(match)
        stats = analyzer.get_player_stats()
        # Perfect KDA: kills + assists
        assert stats["kda"] == 8

    def test_champions_played_tracking(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        stats = analyzer.get_player_stats()
        champs = stats["champions_played"]
        # Jinx appears in match 0 and 3
        assert "Jinx" in champs
        assert champs["Jinx"]["games"] == 2

    def test_positions_played_tracking(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        stats = analyzer.get_player_stats()
        positions = stats["positions_played"]
        assert "BOTTOM" in positions
        assert positions["BOTTOM"]["games"] == 5

    def test_multiple_matches_aggregation(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        stats = analyzer.get_player_stats()
        assert stats["total_matches"] == 5
        assert stats["wins"] == 3  # matches 0, 2, 4 are wins
        assert stats["losses"] == 2


class TestGetChampionStats:
    """Test per-champion stat aggregation."""

    def test_no_puuid_returns_empty(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.add_match(sample_match_data)
        assert analyzer.get_champion_stats() == {}

    def test_single_champion_stats(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        analyzer.add_match(sample_match_data)
        champ_stats = analyzer.get_champion_stats()
        assert "Jinx" in champ_stats
        jinx = champ_stats["Jinx"]
        assert jinx["games_played"] == 1
        assert jinx["wins"] == 1
        assert jinx["win_rate"] == 100.0

    def test_champion_kda_calculation(self):
        match = make_match_data(participants=[
            make_participant(puuid="p1", champion_name="Jinx", kills=10, deaths=5, assists=10, win=True),
        ] + [make_participant(puuid=f"o{i}", win=True) for i in range(9)])
        analyzer = StatsAnalyzer()
        analyzer.puuid = "p1"
        analyzer.add_match(match)
        stats = analyzer.get_champion_stats()
        # (10 + 10) / 5 = 4.0
        assert stats["Jinx"]["kda"] == 4.0

    def test_champion_averages(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        stats = analyzer.get_champion_stats()
        # Jinx played in 2 games
        jinx = stats["Jinx"]
        assert jinx["games_played"] == 2
        assert "avg_kills" in jinx
        assert "avg_deaths" in jinx
        assert "avg_damage" in jinx


class TestGetMatchDetails:
    """Test single-match detail retrieval."""

    def test_returns_none_for_unknown_match(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        analyzer.add_match(sample_match_data)
        assert analyzer.get_match_details("FAKE_MATCH") is None

    def test_returns_details_for_known_match(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        analyzer.add_match(sample_match_data)
        details = analyzer.get_match_details("NA1_5000000001")
        assert details is not None
        assert details["match_id"] == "NA1_5000000001"
        assert details["champion"] == "Jinx"
        assert details["win"] is True
        assert "analysis" in details

    def test_match_details_kda(self):
        match = make_match_data(
            match_id="NA1_100",
            participants=[
                make_participant(puuid="p1", kills=6, deaths=3, assists=9, win=True),
            ] + [make_participant(puuid=f"o{i}", win=True) for i in range(9)],
        )
        analyzer = StatsAnalyzer()
        analyzer.puuid = "p1"
        analyzer.add_match(match)
        details = analyzer.get_match_details("NA1_100")
        assert details["kda"] == 5.0  # (6 + 9) / 3


class TestGetTrendData:
    """Test performance trend computation."""

    def test_no_puuid_returns_empty(self):
        analyzer = StatsAnalyzer()
        result = analyzer.get_trend_data()
        assert result == {"matches": [], "trends": {}}

    def test_single_match_no_trends(self, sample_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        analyzer.add_match(sample_match_data)
        result = analyzer.get_trend_data()
        assert len(result["matches"]) == 1
        assert result["trends"] == {}

    def test_multiple_matches_have_trends(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        result = analyzer.get_trend_data()
        assert len(result["matches"]) == 5
        trends = result["trends"]
        assert "kda" in trends
        assert "cs_per_min" in trends
        assert trends["kda"]["direction"] in ("improving", "declining", "stable")

    def test_win_streak_detection(self):
        # 3 wins in a row at the end
        matches = []
        for i in range(5):
            win = i >= 2  # last 3 are wins
            matches.append(
                make_match_data(
                    match_id=f"NA1_60000000{i}",
                    game_start_timestamp=1700000000000 + i * 3600000,
                    participants=[
                        make_participant(puuid="p1", win=win, kills=5, deaths=2, assists=5),
                    ] + [make_participant(puuid=f"o{j}", win=win) for j in range(9)],
                )
            )
        analyzer = StatsAnalyzer()
        analyzer.puuid = "p1"
        for m in matches:
            analyzer.add_match(m)
        result = analyzer.get_trend_data()
        assert result["trends"]["streak"]["type"] == "win"
        assert result["trends"]["streak"]["count"] == 3


class TestGetAdvancedStats:
    """Test advanced stats computation."""

    def test_no_puuid_returns_empty(self):
        analyzer = StatsAnalyzer()
        assert analyzer.get_advanced_stats() == {}

    def test_returns_all_10_categories(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        advanced = analyzer.get_advanced_stats()
        assert "skillshot_accuracy" in advanced
        assert "lane_dominance" in advanced
        assert "clutch_factor" in advanced
        assert "communication" in advanced
        assert "vision_quality" in advanced
        assert "efficiency" in advanced
        assert "cross_match" in advanced

    def test_skillshot_accuracy_computed(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        ss = analyzer.get_advanced_stats()["skillshot_accuracy"]
        assert ss["average"] > 0
        assert ss["total_hits"] > 0

    def test_communication_archetype(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        comm = analyzer.get_advanced_stats()["communication"]
        assert comm["archetype"] in ("Quiet", "Shotcaller", "Danger Pinger", "Communicator")
        assert comm["pings_per_min"] >= 0

    def test_surrender_stats(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"
        for m in multiple_match_data:
            analyzer.add_match(m)
        cross = analyzer.get_advanced_stats()["cross_match"]
        assert "surrender_stats" in cross
        assert cross["surrender_stats"]["total_games"] == 5

    def test_jungle_stats_none_for_non_jungler(self, multiple_match_data):
        analyzer = StatsAnalyzer()
        analyzer.puuid = "player1"  # BOTTOM position
        for m in multiple_match_data:
            analyzer.add_match(m)
        advanced = analyzer.get_advanced_stats()
        assert advanced["counter_jungle"] is None

    def test_jungle_stats_present_for_jungler(self):
        match = make_match_data(participants=[
            make_participant(
                puuid="p1",
                team_position="JUNGLE",
                individual_position="JUNGLE",
                win=True,
                challenges_overrides={
                    "buffsStolen": 2,
                    "enemyJungleMonsterKills": 10,
                },
            ),
        ] + [make_participant(puuid=f"o{i}", win=True) for i in range(9)])
        analyzer = StatsAnalyzer()
        analyzer.puuid = "p1"
        analyzer.add_match(match)
        advanced = analyzer.get_advanced_stats()
        assert advanced["counter_jungle"] is not None
        assert advanced["counter_jungle"]["games"] == 1
