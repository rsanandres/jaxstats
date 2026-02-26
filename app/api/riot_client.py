import os
import aiohttp
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from fastapi import HTTPException

# Try to load .env file from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Maximum number of retries for rate-limited or transient errors
MAX_RETRIES = 3
# Default timeout for API requests (seconds)
REQUEST_TIMEOUT = 15


class RiotAPIClient:
    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")
        if not self.api_key:
            raise ValueError(
                "RIOT_API_KEY environment variable is not set. "
                "Please set it using either:\n"
                "1. Create a .env file in the project root with RIOT_API_KEY=your_key\n"
                "2. Run 'export RIOT_API_KEY=your_key' in your terminal"
            )

        # Create data directory if it doesn't exist
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Base URLs for different routing values
        self.region_routing = {
            # Americas routing
            'na1': 'americas',  # North America
            'br1': 'americas',  # Brazil
            'la1': 'americas',  # Latin America North
            'la2': 'americas',  # Latin America South

            # Europe routing
            'euw1': 'europe',   # Europe West
            'eun1': 'europe',   # Europe Nordic & East
            'tr1': 'europe',    # Turkey
            'ru': 'europe',     # Russia

            # Asia routing
            'kr': 'asia',       # Korea
            'jp1': 'asia',      # Japan

            # SEA routing
            'oc1': 'sea',       # Oceania
            'sg2': 'sea',       # Singapore
            'tw2': 'sea',       # Taiwan
            'vn2': 'sea'        # Vietnam
        }

        self.base_urls = {
            'americas': 'https://americas.api.riotgames.com',
            'europe': 'https://europe.api.riotgames.com',
            'asia': 'https://asia.api.riotgames.com',
            'sea': 'https://sea.api.riotgames.com'
        }

    def _get_routing_value(self, region: str) -> str:
        """Get the routing value for a given region."""
        routing = self.region_routing.get(region.lower())
        if not routing:
            raise ValueError(f"Invalid region: {region}. Valid regions: {', '.join(sorted(self.region_routing.keys()))}")
        return routing

    async def _make_request(self, url: str, headers: Dict[str, str], _retry: int = 0) -> Dict:
        """Make a request to the Riot API with rate limit handling and retries.

        Retries up to MAX_RETRIES times for rate-limit (429) and server errors (500-503).
        Respects the Retry-After header when present.
        """
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()

                    error_text = await response.text()

                    if response.status == 404:
                        logger.warning("Resource not found: %s", url)
                        raise HTTPException(status_code=404, detail=f"Resource not found: {error_text}")

                    if response.status == 403:
                        logger.error("API key invalid or expired: %s", url)
                        raise HTTPException(status_code=403, detail="API key invalid or expired. Check your RIOT_API_KEY.")

                    if response.status == 429:
                        if _retry >= MAX_RETRIES:
                            logger.error("Rate limit exceeded after %d retries: %s", MAX_RETRIES, url)
                            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
                        retry_after = int(response.headers.get("Retry-After", 120))
                        logger.warning("Rate limited on %s, retrying in %ds (attempt %d/%d)", url, retry_after, _retry + 1, MAX_RETRIES)
                        await asyncio.sleep(retry_after)
                        return await self._make_request(url, headers, _retry=_retry + 1)

                    if response.status in (500, 502, 503) and _retry < MAX_RETRIES:
                        wait = 2 ** (_retry + 1)
                        logger.warning("Server error %d on %s, retrying in %ds (attempt %d/%d)", response.status, url, wait, _retry + 1, MAX_RETRIES)
                        await asyncio.sleep(wait)
                        return await self._make_request(url, headers, _retry=_retry + 1)

                    logger.error("API request failed with status %d: %s — %s", response.status, url, error_text)
                    raise HTTPException(status_code=response.status, detail=f"Riot API error ({response.status}): {error_text}")

            except aiohttp.ClientError as e:
                if _retry < MAX_RETRIES:
                    wait = 2 ** (_retry + 1)
                    logger.warning("Network error on %s: %s, retrying in %ds (attempt %d/%d)", url, e, wait, _retry + 1, MAX_RETRIES)
                    await asyncio.sleep(wait)
                    return await self._make_request(url, headers, _retry=_retry + 1)
                logger.error("Network error after %d retries on %s: %s", MAX_RETRIES, url, e)
                raise HTTPException(status_code=502, detail=f"Failed to connect to Riot API: {e}")
            except asyncio.TimeoutError:
                if _retry < MAX_RETRIES:
                    wait = 2 ** (_retry + 1)
                    logger.warning("Timeout on %s, retrying in %ds (attempt %d/%d)", url, wait, _retry + 1, MAX_RETRIES)
                    await asyncio.sleep(wait)
                    return await self._make_request(url, headers, _retry=_retry + 1)
                logger.error("Timeout after %d retries on %s", MAX_RETRIES, url)
                raise HTTPException(status_code=504, detail="Riot API request timed out. Please try again.")

    def _save_match_data(self, match_id: str, data: Dict):
        """Save match data to a JSON file."""
        match_file = self.data_dir / f"match_{match_id}.json"
        with open(match_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_match_data(self, match_id: str) -> Optional[Dict]:
        """Load match data from a JSON file if it exists."""
        match_file = self.data_dir / f"match_{match_id}.json"
        if match_file.exists():
            try:
                with open(match_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Corrupt cache file for %s, ignoring: %s", match_id, e)
                return None
        return None

    async def get_match_details(self, match_id: str, region: str) -> Optional[Dict]:
        """Get detailed information about a specific match using match-v5 endpoint."""
        # Check if we already have this match data
        cached_data = self._load_match_data(match_id)
        if cached_data:
            return cached_data

        routing = self._get_routing_value(region)
        url = f"{self.base_urls[routing]}/lol/match/v5/matches/{match_id}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        data = await self._make_request(url, headers)

        if data:
            self._save_match_data(match_id, data)
        return data

    async def get_match_history(self, puuid: str, region: str, count: int = 10) -> List[str]:
        """Get recent match history for a summoner using match-v5 endpoint."""
        routing = self._get_routing_value(region)
        url = f"{self.base_urls[routing]}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        return await self._make_request(url, headers)

    async def get_match_timeline(self, match_id: str, region: str) -> Optional[Dict]:
        """Get timeline information for a specific match using match-v5 endpoint."""
        routing = self._get_routing_value(region)
        url = f"{self.base_urls[routing]}/lol/match/v5/matches/{match_id}/timeline"
        headers = {
            "X-Riot-Token": self.api_key
        }
        return await self._make_request(url, headers)

    async def get_account_by_riot_id(self, game_name: str, tag_line: str, region: str) -> Dict:
        """Get account information using Riot ID (game name and tag line)."""
        routing = self._get_routing_value(region)
        url = f"{self.base_urls[routing]}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        return await self._make_request(url, headers)

    async def get_summoner_by_puuid(self, puuid: str, region: str) -> Dict:
        """Get summoner information by PUUID."""
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        return await self._make_request(url, headers)

    async def get_champion_mastery(self, summoner_id: str, region: str) -> List[Dict]:
        """Get champion mastery information for a summoner."""
        url = f"https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        return await self._make_request(url, headers)

    async def get_league_entries(self, summoner_id: str, region: str) -> List[Dict]:
        """Get league entries for a summoner."""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        return await self._make_request(url, headers)

    async def get_active_game(self, puuid: str, region: str) -> Optional[Dict]:
        """Get active game info using Spectator v5 API.

        Returns None (via 404) if the player is not in a game.
        """
        url = f"https://{region}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
        headers = {
            "X-Riot-Token": self.api_key
        }
        try:
            return await self._make_request(url, headers)
        except HTTPException as e:
            if e.status_code == 404:
                return None
            raise
