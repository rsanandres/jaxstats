import os
import aiohttp
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from fastapi import HTTPException

load_dotenv()

class RiotAPIClient:
    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")
        if not self.api_key:
            raise ValueError("RIOT_API_KEY environment variable is not set")
        
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
            raise ValueError(f"Invalid region: {region}")
        return routing

    async def _make_request(self, url: str, headers: Dict[str, str]) -> Dict:
        """Make a request to the Riot API with rate limit handling."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        error_text = await response.text()
                        print(f"Resource not found. Failed URL: {url}. Response: {error_text}")
                        return None
                    elif response.status == 429:  # Rate limit exceeded
                        error_text = await response.text()
                        print(f"Rate limit exceeded. Waiting 120 seconds before retrying. Failed URL: {url}")
                        await asyncio.sleep(120)  # Wait for 2 minutes
                        return await self._make_request(url, headers)  # Retry the request
                    elif response.status == 403:
                        print(f"Skipping forbidden request: {url}")
                        return None
                    else:
                        error_text = await response.text()
                        print(f"API request failed with status {response.status}. Failed URL: {url}. Response: {error_text}")
                        return None
            except aiohttp.ClientError as e:
                print(f"Request failed: {str(e)}")
                return None

    def _save_match_data(self, match_id: str, data: Dict):
        """Save match data to a JSON file."""
        match_file = self.data_dir / f"match_{match_id}.json"
        with open(match_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_match_data(self, match_id: str) -> Optional[Dict]:
        """Load match data from a JSON file if it exists."""
        match_file = self.data_dir / f"match_{match_id}.json"
        if match_file.exists():
            with open(match_file, 'r') as f:
                return json.load(f)
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