"""Ollama client for AI-powered match analysis suggestions."""

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://100.91.76.71:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = 30.0


async def check_ollama_health() -> bool:
    """Check if the Ollama instance is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def generate_analysis(prompt: str) -> Optional[str]:
    """Send a prompt to Ollama and return the response text.

    Returns None if Ollama is unreachable or errors out.
    """
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 256,
                    }
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
            else:
                logger.warning(f"Ollama returned status {resp.status_code}")
                return None
    except httpx.TimeoutException:
        logger.warning("Ollama request timed out")
        return None
    except Exception as e:
        logger.warning(f"Ollama error: {e}")
        return None
