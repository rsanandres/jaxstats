"""Tests for app.api.riot_client — Riot API client."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException

# Patch env var before import
os.environ.setdefault("RIOT_API_KEY", "RGAPI-test-key-for-testing")

from app.api.riot_client import RiotAPIClient


class TestRiotAPIClientInit:
    def test_init_with_api_key(self):
        with patch.dict(os.environ, {"RIOT_API_KEY": "RGAPI-test-key"}):
            client = RiotAPIClient()
            assert client.api_key == "RGAPI-test-key"

    def test_init_without_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove RIOT_API_KEY entirely
            env = os.environ.copy()
            env.pop("RIOT_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="RIOT_API_KEY"):
                    RiotAPIClient()


class TestRegionRouting:
    def setup_method(self):
        with patch.dict(os.environ, {"RIOT_API_KEY": "RGAPI-test"}):
            self.client = RiotAPIClient()

    def test_na1_routes_to_americas(self):
        assert self.client._get_routing_value("na1") == "americas"

    def test_euw1_routes_to_europe(self):
        assert self.client._get_routing_value("euw1") == "europe"

    def test_kr_routes_to_asia(self):
        assert self.client._get_routing_value("kr") == "asia"

    def test_oc1_routes_to_sea(self):
        assert self.client._get_routing_value("oc1") == "sea"

    def test_case_insensitive(self):
        assert self.client._get_routing_value("NA1") == "americas"

    def test_invalid_region_raises(self):
        with pytest.raises(ValueError, match="Invalid region"):
            self.client._get_routing_value("invalid")


class TestMatchDataCaching:
    def setup_method(self):
        with patch.dict(os.environ, {"RIOT_API_KEY": "RGAPI-test"}):
            self.client = RiotAPIClient()

    def test_save_and_load_match_data(self, tmp_path):
        self.client.data_dir = tmp_path
        match_data = {"info": {"gameDuration": 1800}, "metadata": {"matchId": "NA1_123"}}
        self.client._save_match_data("NA1_123", match_data)
        loaded = self.client._load_match_data("NA1_123")
        assert loaded == match_data

    def test_load_nonexistent_returns_none(self, tmp_path):
        self.client.data_dir = tmp_path
        assert self.client._load_match_data("FAKE_MATCH") is None


class TestMakeRequest:
    def setup_method(self):
        with patch.dict(os.environ, {"RIOT_API_KEY": "RGAPI-test"}):
            self.client = RiotAPIClient()

    @pytest.mark.asyncio
    async def test_successful_request(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "ok"})

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await self.client._make_request("https://test.com", {"X-Riot-Token": "key"})
            assert result == {"data": "ok"}

    @pytest.mark.asyncio
    async def test_404_raises_http_exception(self):
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text = AsyncMock(return_value="Not found")

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(HTTPException) as exc_info:
                await self.client._make_request("https://test.com", {})
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_403_raises_http_exception(self):
        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.text = AsyncMock(return_value="Forbidden")

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=False),
        ))

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(HTTPException) as exc_info:
                await self.client._make_request("https://test.com", {})
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_network_error_raises_502(self):
        import aiohttp

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))

        with patch("aiohttp.ClientSession", return_value=mock_session), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await self.client._make_request("https://test.com", {})
            assert exc_info.value.status_code == 502


class TestGetMatchDetails:
    def setup_method(self):
        with patch.dict(os.environ, {"RIOT_API_KEY": "RGAPI-test"}):
            self.client = RiotAPIClient()

    @pytest.mark.asyncio
    async def test_returns_cached_data(self, tmp_path):
        self.client.data_dir = tmp_path
        cached = {"info": {"gameDuration": 1800}, "metadata": {"matchId": "NA1_123"}}
        self.client._save_match_data("NA1_123", cached)

        result = await self.client.get_match_details("NA1_123", "na1")
        assert result == cached

    @pytest.mark.asyncio
    async def test_fetches_and_caches_on_miss(self, tmp_path):
        self.client.data_dir = tmp_path
        api_data = {"info": {"gameDuration": 2000}, "metadata": {"matchId": "NA1_999"}}

        with patch.object(self.client, "_make_request", new_callable=AsyncMock, return_value=api_data):
            result = await self.client.get_match_details("NA1_999", "na1")
            assert result == api_data
            # Should now be cached
            cached = self.client._load_match_data("NA1_999")
            assert cached == api_data
