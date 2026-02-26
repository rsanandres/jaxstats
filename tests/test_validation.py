"""Tests for input validation in app.main."""

import os
import pytest

os.environ.setdefault("RIOT_API_KEY", "RGAPI-test-key-for-testing")

from pydantic import ValidationError
from app.main import (
    SummonerRequest,
    CompareRequest,
    WatchlistAddRequest,
    _validate_summoner_name,
    _validate_region,
)


class TestValidateSummonerName:
    def test_valid_name(self):
        assert _validate_summoner_name("Player#NA1") == "Player#NA1"

    def test_strips_whitespace(self):
        assert _validate_summoner_name("  Player#NA1  ") == "Player#NA1"

    def test_missing_hashtag_raises(self):
        with pytest.raises(ValueError, match="GameName#TAG"):
            _validate_summoner_name("PlayerNoTag")

    def test_empty_game_name_raises(self):
        with pytest.raises(ValueError, match="game name"):
            _validate_summoner_name("#TAG")

    def test_empty_tag_raises(self):
        with pytest.raises(ValueError, match="tag line"):
            _validate_summoner_name("Player#")

    def test_long_game_name_raises(self):
        with pytest.raises(ValueError, match="16 characters"):
            _validate_summoner_name("A" * 17 + "#NA1")

    def test_long_tag_raises(self):
        with pytest.raises(ValueError, match="5 characters"):
            _validate_summoner_name("Player#TOOLONG")

    def test_max_length_game_name_ok(self):
        result = _validate_summoner_name("A" * 16 + "#NA1")
        assert "#" in result

    def test_max_length_tag_ok(self):
        result = _validate_summoner_name("Player#ABCDE")
        assert result == "Player#ABCDE"


class TestValidateRegion:
    def test_valid_regions(self):
        for region in ["na1", "euw1", "eun1", "kr", "jp1", "br1", "oc1"]:
            assert _validate_region(region) == region

    def test_case_insensitive(self):
        assert _validate_region("NA1") == "na1"
        assert _validate_region("EUW1") == "euw1"

    def test_strips_whitespace(self):
        assert _validate_region("  na1  ") == "na1"

    def test_invalid_region_raises(self):
        with pytest.raises(ValueError, match="Invalid region"):
            _validate_region("invalid")

    def test_empty_region_raises(self):
        with pytest.raises(ValueError, match="Invalid region"):
            _validate_region("")


class TestSummonerRequestValidation:
    def test_valid_request(self):
        req = SummonerRequest(summoner_name="Player#NA1", region="na1", match_count=5)
        assert req.summoner_name == "Player#NA1"
        assert req.region == "na1"

    def test_missing_hashtag_rejected(self):
        with pytest.raises(ValidationError):
            SummonerRequest(summoner_name="NoTag", region="na1")

    def test_invalid_region_rejected(self):
        with pytest.raises(ValidationError):
            SummonerRequest(summoner_name="Player#NA1", region="invalid")

    def test_match_count_too_low(self):
        with pytest.raises(ValidationError):
            SummonerRequest(summoner_name="Player#NA1", region="na1", match_count=0)

    def test_match_count_too_high(self):
        with pytest.raises(ValidationError):
            SummonerRequest(summoner_name="Player#NA1", region="na1", match_count=21)

    def test_match_count_defaults_to_5(self):
        req = SummonerRequest(summoner_name="Player#NA1", region="na1")
        assert req.match_count == 5


class TestCompareRequestValidation:
    def test_valid_request(self):
        req = CompareRequest(
            summoner1_name="Player1#NA1",
            summoner1_region="na1",
            summoner2_name="Player2#EUW",
            summoner2_region="euw1",
        )
        assert req.summoner1_name == "Player1#NA1"

    def test_invalid_summoner1_rejected(self):
        with pytest.raises(ValidationError):
            CompareRequest(
                summoner1_name="NoTag",
                summoner1_region="na1",
                summoner2_name="Player2#EUW",
                summoner2_region="euw1",
            )

    def test_invalid_summoner2_rejected(self):
        with pytest.raises(ValidationError):
            CompareRequest(
                summoner1_name="Player1#NA1",
                summoner1_region="na1",
                summoner2_name="NoTag",
                summoner2_region="euw1",
            )

    def test_invalid_region_rejected(self):
        with pytest.raises(ValidationError):
            CompareRequest(
                summoner1_name="Player1#NA1",
                summoner1_region="bad",
                summoner2_name="Player2#EUW",
                summoner2_region="euw1",
            )


class TestWatchlistAddRequestValidation:
    def test_valid_request(self):
        req = WatchlistAddRequest(name="Player#NA1", region="na1")
        assert req.name == "Player#NA1"

    def test_invalid_name_rejected(self):
        with pytest.raises(ValidationError):
            WatchlistAddRequest(name="NoTag", region="na1")

    def test_invalid_region_rejected(self):
        with pytest.raises(ValidationError):
            WatchlistAddRequest(name="Player#NA1", region="bad")

    def test_match_count_validation(self):
        with pytest.raises(ValidationError):
            WatchlistAddRequest(name="Player#NA1", region="na1", match_count=0)
