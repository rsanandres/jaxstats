"""Tests for FastAPI endpoints in app.main."""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# Ensure API key is set before importing app
os.environ.setdefault("RIOT_API_KEY", "RGAPI-test-key-for-testing")

import httpx
from app.main import app, run_analysis


@pytest.fixture
def client():
    """HTTPX async test client for ASGI apps."""
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        with patch("app.main.check_ollama_health", new_callable=AsyncMock, return_value=False):
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "riot_api_key" in data
            assert "ml_models" in data


class TestHomeEndpoint:
    @pytest.mark.asyncio
    async def test_home_returns_html(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestAnalyzeEndpointValidation:
    @pytest.mark.asyncio
    async def test_post_missing_hashtag_returns_422(self, client):
        """Pydantic validation rejects summoner names without '#'."""
        response = await client.post("/api/analyze", json={
            "summoner_name": "PlayerNoTag",
            "region": "na1",
            "match_count": 5,
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_post_valid_request_shape(self, client):
        mock_result = {
            "summoner_name": "Test",
            "summoner_level": 100,
            "profile_icon_id": 1,
            "overall_stats": {},
            "match_analyses": [],
            "champion_stats": {},
            "gpi": {},
            "trends": {},
            "trend_matches": [],
            "match_count": {"requested": 5, "retrieved": 0, "analyzed": 0, "cached": 0, "new": 0},
        }
        with patch("app.main.run_analysis", new_callable=AsyncMock, return_value=mock_result):
            response = await client.post("/api/analyze", json={
                "summoner_name": "Player#TAG",
                "region": "na1",
                "match_count": 5,
            })
            assert response.status_code == 200
            data = response.json()
            assert "summoner_name" in data
            assert "match_count" in data

    @pytest.mark.asyncio
    async def test_get_analyze_with_valid_name(self, client):
        mock_result = {
            "summoner_name": "Test",
            "summoner_level": 100,
            "profile_icon_id": 1,
            "overall_stats": {},
            "match_analyses": [],
            "champion_stats": {},
            "gpi": {},
            "trends": {},
            "trend_matches": [],
            "match_count": {"requested": 5, "retrieved": 0, "analyzed": 0, "cached": 0, "new": 0},
        }
        with patch("app.main.run_analysis", new_callable=AsyncMock, return_value=mock_result):
            response = await client.get("/api/analyze/Player%23TAG?region=na1&match_count=5")
            assert response.status_code == 200


class TestRunAnalysisValidation:
    @pytest.mark.asyncio
    async def test_rejects_missing_hashtag(self):
        with pytest.raises(ValueError, match="GameName#TAG"):
            await run_analysis("NoHashtag", "na1", 5)

    @pytest.mark.asyncio
    async def test_rejects_invalid_match_count_low(self):
        with pytest.raises(ValueError, match="Match count"):
            await run_analysis("Player#TAG", "na1", 0)

    @pytest.mark.asyncio
    async def test_rejects_invalid_match_count_high(self):
        with pytest.raises(ValueError, match="Match count"):
            await run_analysis("Player#TAG", "na1", 21)


class TestCompareEndpoint:
    @pytest.mark.asyncio
    async def test_compare_returns_both_users(self, client):
        mock_result = {
            "summoner_name": "Test",
            "summoner_level": 100,
            "profile_icon_id": 1,
            "overall_stats": {},
            "match_analyses": [],
            "champion_stats": {},
            "gpi": {},
            "trends": {},
            "trend_matches": [],
            "match_count": {"requested": 5, "retrieved": 0, "analyzed": 0, "cached": 0, "new": 0},
        }
        with patch("app.main.run_analysis", new_callable=AsyncMock, return_value=mock_result):
            response = await client.post("/api/compare", json={
                "summoner1_name": "Player1#TAG",
                "summoner1_region": "na1",
                "summoner2_name": "Player2#TAG",
                "summoner2_region": "euw1",
                "match_count": 5,
            })
            assert response.status_code == 200
            data = response.json()
            assert "user1" in data
            assert "user2" in data


class TestGPIEndpoint:
    @pytest.mark.asyncio
    async def test_gpi_missing_hashtag_returns_error(self, client):
        response = await client.get("/api/gpi/PlayerNoTag?region=na1")
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_gpi_valid_request(self, client):
        mock_account = {"puuid": "test-puuid"}
        mock_match_ids = ["NA1_1", "NA1_2"]
        mock_match_data = {
            "info": {
                "gameDuration": 1800,
                "participants": [{
                    "puuid": "test-puuid",
                    "championName": "Jinx",
                    "teamPosition": "BOTTOM",
                    "kills": 5, "deaths": 2, "assists": 8,
                    "totalMinionsKilled": 180, "neutralMinionsKilled": 20,
                    "goldEarned": 14000, "visionScore": 30,
                    "totalDamageDealtToChampions": 20000,
                    "totalDamageTaken": 15000,
                    "damageSelfMitigated": 5000,
                    "wardsPlaced": 10, "wardsKilled": 5,
                    "detectorWardsPlaced": 3,
                    "killingSprees": 1,
                    "longestTimeSpentLiving": 600,
                    "damageDealtToObjectives": 10000,
                    "totalTimeSpentDead": 100,
                    "timeCCingOthers": 10,
                    "win": True,
                    "challenges": {
                        "killParticipation": 0.65,
                        "teamDamagePercentage": 0.25,
                        "damageTakenOnTeamPercentage": 0.18,
                        "soloKills": 2,
                        "multikills": 1,
                        "turretTakedowns": 2,
                        "dragonTakedowns": 1,
                        "baronTakedowns": 0,
                        "riftHeraldTakedowns": 1,
                        "visionScorePerMinute": 1.0,
                        "skillshotsHit": 40,
                        "skillshotsDodged": 15,
                        "abilityUses": 120,
                        "enemyChampionImmobilizations": 5,
                        "saveAllyFromDeath": 0,
                        "effectiveHealAndShielding": 1000,
                        "survivedSingleDigitHpCount": 1,
                        "survivedThreeImmobilizesInFight": 0,
                        "outnumberedKills": 0,
                        "laneMinionsFirst10Minutes": 60,
                        "takedownsFirstXMinutes": 3,
                    },
                }],
            },
            "metadata": {"matchId": "NA1_1", "dataVersion": "2", "participants": ["test-puuid"]},
        }

        with patch("app.main.riot_client") as mock_riot:
            mock_riot.get_account_by_riot_id = AsyncMock(return_value=mock_account)
            mock_riot.get_match_history = AsyncMock(return_value=mock_match_ids)
            mock_riot.get_match_details = AsyncMock(return_value=mock_match_data)

            response = await client.get("/api/gpi/Player%23TAG?region=na1&match_count=2")
            assert response.status_code == 200
            data = response.json()
            assert "gpi" in data
            gpi = data["gpi"]
            assert "overall" in gpi
            assert "farming" in gpi


class TestDebugLogsEndpoint:
    @pytest.mark.asyncio
    async def test_debug_logs_returns_list(self, client):
        response = await client.get("/api/debug-logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
