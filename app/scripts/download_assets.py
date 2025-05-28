import os
import requests
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URLs for assets
DRAGON_URL = "https://ddragon.leagueoflegends.com/cdn/13.24.1/data/en_US/champion.json"
CHAMPION_ICON_URL = "https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/{}.png"
MAP_URL = "https://raw.githubusercontent.com/CommunityDragon/Data/master/maps/map11.png"

# Asset directories
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static" / "replay"
MAPS_DIR = STATIC_DIR / "maps"
CHAMPIONS_DIR = STATIC_DIR / "champions"
ICONS_DIR = STATIC_DIR / "icons"

def create_directories():
    """Create necessary directories for assets."""
    for directory in [MAPS_DIR, CHAMPIONS_DIR, ICONS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def download_map():
    """Download the Summoner's Rift map image."""
    try:
        response = requests.get(MAP_URL)
        response.raise_for_status()
        
        map_path = MAPS_DIR / "summoners_rift.png"
        with open(map_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Downloaded map to: {map_path}")
    except Exception as e:
        logger.error(f"Error downloading map: {e}")

def download_champion_icons():
    """Download champion icons."""
    try:
        # Get champion list
        response = requests.get(DRAGON_URL)
        response.raise_for_status()
        champions = response.json()["data"]
        
        # Download each champion icon
        for champion_name in champions.keys():
            icon_url = CHAMPION_ICON_URL.format(champion_name)
            response = requests.get(icon_url)
            response.raise_for_status()
            
            icon_path = CHAMPIONS_DIR / f"{champion_name.lower()}.png"
            with open(icon_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Downloaded champion icon: {champion_name}")
    except Exception as e:
        logger.error(f"Error downloading champion icons: {e}")

def create_objective_icons():
    """Create simple objective icons."""
    objectives = {
        "dragon": "#ff0000",
        "baron": "#800080",
        "herald": "#00ff00",
        "elder": "#ffa500"
    }
    
    for objective, color in objectives.items():
        icon_path = ICONS_DIR / f"{objective}.png"
        # Create a simple colored circle for each objective
        # This is a placeholder - you should replace these with proper icons
        logger.info(f"Created objective icon: {objective}")

def main():
    """Main function to download all assets."""
    logger.info("Starting asset download...")
    create_directories()
    download_map()
    download_champion_icons()
    create_objective_icons()
    logger.info("Asset download complete!")

if __name__ == "__main__":
    main() 