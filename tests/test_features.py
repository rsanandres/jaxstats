"""Tests for app.ml.features — feature extraction."""

import pytest
from app.ml.features import (
    safe_get,
    extract_participant_features,
    extract_all_participants,
    GPI_FEATURE_SETS,
    MATCH_SCORE_FEATURES,
    TIER_ORDER,
)
from tests.conftest import make_participant, make_match_data


class TestSafeGet:
    def test_single_key(self):
        assert safe_get({"a": 1}, "a") == 1

    def test_nested_keys(self):
        assert safe_get({"a": {"b": {"c": 42}}}, "a", "b", "c") == 42

    def test_missing_key_returns_default(self):
        assert safe_get({"a": 1}, "b", default=99) == 99

    def test_none_value_returns_default(self):
        assert safe_get({"a": None}, "a", default=0) == 0

    def test_non_dict_intermediate(self):
        assert safe_get({"a": "not_dict"}, "a", "b", default=0) == 0

    def test_empty_dict(self):
        assert safe_get({}, "a", default=5) == 5


class TestExtractParticipantFeatures:
    def test_returns_all_expected_keys(self, sample_participant):
        features = extract_participant_features(sample_participant, 1800)
        expected_keys = [
            "kills", "deaths", "assists", "kda", "win",
            "cs", "cs_per_min", "gold_per_min", "gold_earned", "lane_cs_10",
            "vision_score", "vision_per_min", "wards_placed", "wards_killed", "control_wards",
            "dmg_per_min", "dmg_dealt", "kill_participation", "solo_kills", "takedowns_first_x",
            "team_dmg_pct", "multikills", "killing_sprees", "skillshots_hit", "ability_uses",
            "dmg_taken", "dmg_mitigated", "dmg_taken_pct", "time_dead_pct", "longest_living",
            "survived_low_hp", "survived_3cc",
            "turret_takedowns", "dragon_takedowns", "baron_takedowns",
            "rift_herald_takedowns", "obj_dmg_per_min",
            "cc_score", "immobilizations", "save_ally", "heal_shield",
            "outnumbered_kills", "skillshots_dodged",
        ]
        for key in expected_keys:
            assert key in features, f"Missing feature: {key}"

    def test_kda_calculation(self):
        p = make_participant(kills=10, deaths=5, assists=10)
        features = extract_participant_features(p, 1800)
        assert features["kda"] == 4.0  # (10 + 10) / 5

    def test_kda_zero_deaths(self):
        p = make_participant(kills=5, deaths=0, assists=3)
        features = extract_participant_features(p, 1800)
        assert features["kda"] == 8.0  # (5 + 3) / 1

    def test_cs_per_min(self):
        p = make_participant(total_minions_killed=150, neutral_minions_killed=30)
        features = extract_participant_features(p, 1800)  # 30 min
        assert features["cs"] == 180
        assert features["cs_per_min"] == 6.0

    def test_dmg_per_min(self):
        p = make_participant(total_damage_dealt_to_champions=30000)
        features = extract_participant_features(p, 1800)  # 30 min
        assert features["dmg_per_min"] == 1000.0

    def test_time_dead_pct(self):
        p = make_participant(total_time_spent_dead=180)
        features = extract_participant_features(p, 1800)
        assert features["time_dead_pct"] == 0.1

    def test_win_feature_is_float(self):
        p_win = make_participant(win=True)
        p_loss = make_participant(win=False)
        assert extract_participant_features(p_win, 1800)["win"] == 1.0
        assert extract_participant_features(p_loss, 1800)["win"] == 0.0

    def test_zero_duration_no_crash(self):
        p = make_participant()
        features = extract_participant_features(p, 0)
        # Should use max(0/60, 1) = 1 minute
        assert features["cs_per_min"] > 0

    def test_challenges_extraction(self):
        p = make_participant(challenges_overrides={
            "killParticipation": 0.75,
            "soloKills": 5,
            "turretTakedowns": 4,
        })
        features = extract_participant_features(p, 1800)
        assert features["kill_participation"] == 0.75
        assert features["solo_kills"] == 5
        assert features["turret_takedowns"] == 4


class TestExtractAllParticipants:
    def test_extracts_all_10_participants(self, sample_match_data):
        results = extract_all_participants(sample_match_data)
        assert len(results) == 10

    def test_each_has_metadata_fields(self, sample_match_data):
        results = extract_all_participants(sample_match_data)
        for r in results:
            assert "game_duration_min" in r
            assert "champion_name" in r
            assert "position" in r
            assert "puuid" in r

    def test_game_duration_min_correct(self, sample_match_data):
        results = extract_all_participants(sample_match_data)
        # 1800 seconds = 30 minutes
        assert results[0]["game_duration_min"] == 30.0


class TestFeatureConstants:
    def test_match_score_features_are_strings(self):
        for f in MATCH_SCORE_FEATURES:
            assert isinstance(f, str)

    def test_tier_order_has_10_tiers(self):
        assert len(TIER_ORDER) == 10
        assert TIER_ORDER[0] == "IRON"
        assert TIER_ORDER[-1] == "CHALLENGER"

    def test_gpi_feature_sets_has_8_skills(self):
        expected_skills = [
            "farming", "vision", "aggression", "fighting",
            "survivability", "objectives", "consistency", "versatility",
        ]
        for skill in expected_skills:
            assert skill in GPI_FEATURE_SETS
