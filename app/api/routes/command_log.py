from fastapi import APIRouter
from pathlib import Path

router = APIRouter()

LOG_FILE = Path("/tmp/command_log.txt")

@router.get("/command-log")
def get_command_log():
    if LOG_FILE.exists():
        return {"log": LOG_FILE.read_text()}
    return {"log": ""} 