import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional
from app.api.riot_client import RiotAPIClient

class AphaeDataCollector:
    def __init__(self):
        self.client = RiotAPIClient()
        self.data_dir = Path("data/aphae")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.region = "na1"
        self.game_name = "aphae"
        self.tag_line = "raph"
        self.processed_matches_file = self.data_dir / "processed_matches.json"

    def _load_processed_matches(self) -> set:
        """Load the set of already processed match IDs."""
        if self.processed_matches_file.exists():
            with open(self.processed_matches_file, 'r') as f:
                return set(json.load(f))
        return set()

    def _save_processed_matches(self, processed_matches: set):
        """Save the set of processed match IDs."""
        with open(self.processed_matches_file, 'w') as f:
            json.dump(list(processed_matches), f)

    async def collect_match_data(self, match_id: str) -> Optional[Dict]:
        """Collect and store match data if not already processed."""
        processed_matches = self._load_processed_matches()
        
        if match_id in processed_matches:
            print(f"Match {match_id} already processed, skipping...")
            return None

        print(f"Processing match {match_id}...")
        match_data = await self.client.get_match_details(match_id, self.region)
        
        if match_data:
            # Save match data
            match_file = self.data_dir / f"match_{match_id}.json"
            with open(match_file, 'w') as f:
                json.dump(match_data, f, indent=2)
            
            # Update processed matches
            processed_matches.add(match_id)
            self._save_processed_matches(processed_matches)
            
            # Get and save timeline if available
            timeline = await self.client.get_match_timeline(match_id, self.region)
            if timeline:
                timeline_file = self.data_dir / f"timeline_{match_id}.json"
                with open(timeline_file, 'w') as f:
                    json.dump(timeline, f, indent=2)
        
        return match_data

    async def collect_all_data(self, count: int = 100):
        """Collect all available match data for aphae#raph."""
        try:
            # Get account info
            account_info = await self.client.get_account_by_riot_id(self.game_name, self.tag_line, self.region)
            puuid = account_info['puuid']
            
            # Get match history
            match_ids = await self.client.get_match_history(puuid, self.region, count)
            
            # Process each match
            for match_id in match_ids:
                await self.collect_match_data(match_id)
                
        except Exception as e:
            print(f"Error collecting data: {str(e)}")

async def main():
    collector = AphaeDataCollector()
    await collector.collect_all_data()

if __name__ == "__main__":
    asyncio.run(main()) 