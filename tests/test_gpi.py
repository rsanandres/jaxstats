"""Tests for app.ml.gpi — GPI scoring functions."""

import pytest
from app.ml.gpi import (
    _clamp,
    score_farming,
    score_vision,
    score_aggression,
    score_fighting,
    score_survivability,
    score_objectives,
    compute_gpi,
    compute_consistency,
    compute_versatility,
    compute_full_gpi,
)


class TestClamp:
    def test_within_range(self):
        assert _clamp(50.0) == 50.0

    def test_below_min(self):
        assert _clamp(-10.0) == 0.0

    def test_above_max(self):
        assert _clamp(150.0) == 100.0

    def test_at_boundaries(self):
        assert _clamp(0.0) == 0.0
        assert _clamp(100.0) == 100.0

    def test_custom_range(self):
        assert _clamp(5.0, lo=10.0, hi=20.0) == 10.0
        assert _clamp(25.0, lo=10.0, hi=20.0) == 20.0


class TestScoreFarming:
    def test_zero_stats(self):
        assert score_farming({}) == 0.0

    def test_perfect_farming(self):
        f = {"cs_per_min": 10.0, "gold_per_min": 600, "lane_cs_10": 90}
        score = score_farming(f)
        assert score == 100.0

    def test_average_farming(self):
        f = {"cs_per_min": 6.0, "gold_per_min": 350, "lane_cs_10": 50}
        score = score_farming(f)
        assert 40 < score < 80

    def test_cs_per_min_cap(self):
        # cs_per_min above 8 should be capped
        f1 = {"cs_per_min": 8.0}
        f2 = {"cs_per_min": 20.0}
        assert score_farming(f1) == score_farming(f2)


class TestScoreVision:
    def test_zero_stats(self):
        assert score_vision({}) == 0.0

    def test_good_vision(self):
        f = {"vision_per_min": 1.5, "wards_placed": 15, "wards_killed": 8, "control_wards": 4}
        score = score_vision(f)
        assert score == 100.0

    def test_partial_vision(self):
        f = {"vision_per_min": 0.8, "wards_placed": 8, "wards_killed": 3, "control_wards": 1}
        score = score_vision(f)
        assert 20 < score < 70


class TestScoreAggression:
    def test_zero_stats(self):
        assert score_aggression({}) == 0.0

    def test_high_aggression(self):
        f = {"dmg_per_min": 900, "kill_participation": 0.8, "solo_kills": 4, "takedowns_first_x": 12}
        score = score_aggression(f)
        assert score >= 90

    def test_passive_play(self):
        f = {"dmg_per_min": 200, "kill_participation": 0.2, "solo_kills": 0, "takedowns_first_x": 1}
        score = score_aggression(f)
        assert score < 30


class TestScoreFighting:
    def test_zero_stats(self):
        assert score_fighting({}) == 0.0

    def test_strong_fighter(self):
        f = {"kda": 6.0, "team_dmg_pct": 0.35, "multikills": 3, "killing_sprees": 3}
        score = score_fighting(f)
        assert score >= 75

    def test_scores_stay_in_range(self):
        f = {"kda": 100.0, "team_dmg_pct": 1.0, "multikills": 50, "killing_sprees": 50}
        score = score_fighting(f)
        assert 0 <= score <= 100


class TestScoreSurvivability:
    def test_zero_stats(self):
        score = score_survivability({})
        # Base is 25
        assert score == 25.0

    def test_high_survivability(self):
        f = {
            "time_dead_pct": 0.05,
            "longest_living": 700,
            "survived_low_hp": 3,
            "survived_3cc": 5,
            "dmg_mitigated": 25000,
        }
        score = score_survivability(f)
        assert score >= 80

    def test_high_death_time_penalizes(self):
        low_death = score_survivability({"time_dead_pct": 0.05})
        high_death = score_survivability({"time_dead_pct": 0.30})
        assert low_death > high_death


class TestScoreObjectives:
    def test_zero_stats(self):
        assert score_objectives({}) == 0.0

    def test_objective_focused(self):
        f = {"turret_takedowns": 5, "dragon_takedowns": 4, "baron_takedowns": 2, "obj_dmg_per_min": 500}
        score = score_objectives(f)
        assert score == 100.0


class TestComputeGPI:
    def test_empty_features(self):
        gpi = compute_gpi({})
        assert "overall" in gpi
        assert "farming" in gpi
        assert "consistency" in gpi
        assert "versatility" in gpi
        # Consistency and versatility default to 50 for single match
        assert gpi["consistency"] == 50.0
        assert gpi["versatility"] == 50.0

    def test_all_skills_in_range(self):
        f = {
            "cs_per_min": 7, "gold_per_min": 400, "lane_cs_10": 60,
            "vision_per_min": 1.0, "wards_placed": 10, "wards_killed": 5, "control_wards": 3,
            "dmg_per_min": 600, "kill_participation": 0.6, "solo_kills": 2, "takedowns_first_x": 6,
            "kda": 3.5, "team_dmg_pct": 0.25, "multikills": 1, "killing_sprees": 1,
            "time_dead_pct": 0.10, "longest_living": 500, "survived_low_hp": 1, "survived_3cc": 2, "dmg_mitigated": 10000,
            "turret_takedowns": 2, "dragon_takedowns": 1, "baron_takedowns": 1, "obj_dmg_per_min": 200,
        }
        gpi = compute_gpi(f)
        for skill, score in gpi.items():
            assert 0 <= score <= 100, f"{skill} out of range: {score}"

    def test_overall_is_weighted_average(self):
        gpi = compute_gpi({
            "cs_per_min": 8, "gold_per_min": 500, "lane_cs_10": 80,
            "vision_per_min": 1.5, "wards_placed": 15, "wards_killed": 8, "control_wards": 4,
        })
        weights = {
            "farming": 0.15, "vision": 0.10, "aggression": 0.15,
            "fighting": 0.20, "survivability": 0.15, "objectives": 0.15,
            "consistency": 0.05, "versatility": 0.05,
        }
        expected = sum(gpi[k] * weights[k] for k in weights)
        assert abs(gpi["overall"] - round(expected, 1)) < 0.15


class TestComputeConsistency:
    def test_single_match_returns_50(self):
        assert compute_consistency([{"kda": 3.0}]) == 50.0

    def test_empty_returns_50(self):
        assert compute_consistency([]) == 50.0

    def test_identical_matches_high_consistency(self):
        features = [
            {"kda": 3.0, "cs_per_min": 7.0, "vision_per_min": 1.0, "dmg_per_min": 500},
            {"kda": 3.0, "cs_per_min": 7.0, "vision_per_min": 1.0, "dmg_per_min": 500},
            {"kda": 3.0, "cs_per_min": 7.0, "vision_per_min": 1.0, "dmg_per_min": 500},
        ]
        score = compute_consistency(features)
        assert score == 100.0

    def test_high_variance_low_consistency(self):
        features = [
            {"kda": 1.0, "cs_per_min": 3.0, "vision_per_min": 0.3, "dmg_per_min": 200},
            {"kda": 8.0, "cs_per_min": 10.0, "vision_per_min": 2.0, "dmg_per_min": 900},
        ]
        score = compute_consistency(features)
        assert score < 50


class TestComputeVersatility:
    def test_empty_returns_50(self):
        assert compute_versatility([]) == 50.0

    def test_one_champion_one_position(self):
        features = [
            {"champion_name": "Jinx", "position": "BOTTOM"},
            {"champion_name": "Jinx", "position": "BOTTOM"},
        ]
        score = compute_versatility(features)
        # Low versatility: 1 champ, 1 position
        assert score < 50

    def test_many_champions_many_positions(self):
        features = [
            {"champion_name": "Jinx", "position": "BOTTOM"},
            {"champion_name": "Ahri", "position": "MIDDLE"},
            {"champion_name": "Lee Sin", "position": "JUNGLE"},
            {"champion_name": "Thresh", "position": "UTILITY"},
            {"champion_name": "Garen", "position": "TOP"},
        ]
        score = compute_versatility(features)
        assert score >= 90


class TestComputeFullGPI:
    def test_empty_list(self):
        gpi = compute_full_gpi([])
        assert gpi["overall"] == 0.0
        assert gpi["farming"] == 0.0

    def test_single_match(self):
        features = [{
            "cs_per_min": 7, "gold_per_min": 400, "lane_cs_10": 60,
            "vision_per_min": 1.0, "wards_placed": 10, "wards_killed": 5, "control_wards": 3,
            "dmg_per_min": 600, "kill_participation": 0.6, "solo_kills": 2, "takedowns_first_x": 6,
            "kda": 3.5, "team_dmg_pct": 0.25, "multikills": 1, "killing_sprees": 1,
            "time_dead_pct": 0.10, "longest_living": 500, "survived_low_hp": 1, "survived_3cc": 2, "dmg_mitigated": 10000,
            "turret_takedowns": 2, "dragon_takedowns": 1, "baron_takedowns": 1, "obj_dmg_per_min": 200,
            "champion_name": "Jinx", "position": "BOTTOM",
        }]
        gpi = compute_full_gpi(features)
        for skill, score in gpi.items():
            assert 0 <= score <= 100, f"{skill} out of range: {score}"

    def test_multi_match_consistency_computed(self):
        base = {
            "kda": 3.0, "cs_per_min": 7.0, "vision_per_min": 1.0, "dmg_per_min": 500,
            "champion_name": "Jinx", "position": "BOTTOM",
        }
        features = [dict(base) for _ in range(5)]
        gpi = compute_full_gpi(features)
        # Identical matches => high consistency
        assert gpi["consistency"] >= 90
