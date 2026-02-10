"""Match analysis suggestion engine using Ollama (llama3).

Provides AI coaching suggestions based on match performance data.
Falls back to rule-based suggestions if Ollama is unavailable.
"""

import logging
from typing import Dict, List, Optional

from ..llm.ollama_client import generate_analysis

logger = logging.getLogger(__name__)


def format_stats_natural_language(stats: dict) -> str:
    return (
        f"Champion: {stats.get('champion', 'Unknown')}, Position: {stats.get('position', 'Unknown')}, "
        f"Win: {'Yes' if stats.get('win') else 'No'}, "
        f"Kills: {stats.get('kills', 0)}, Deaths: {stats.get('deaths', 0)}, Assists: {stats.get('assists', 0)}, "
        f"KDA: {stats.get('kda', 0)}, Damage Dealt: {stats.get('damage_dealt', 0)}, "
        f"Damage Taken: {stats.get('damage_taken', 0)}, Gold Earned: {stats.get('gold_earned', 0)}, "
        f"Vision Score: {stats.get('vision_score', 0)}, Time CCing Others: {stats.get('time_ccing_others', 0)}s"
    )


def _build_prompt(match_stats: dict, ml_scores: dict = None, history_stats: list = None) -> str:
    """Build the coaching prompt for Ollama."""
    prompt = (
        "You are an expert League of Legends coach. Analyze the following match performance "
        "and give 2-3 specific, actionable coaching suggestions. Be concise and direct.\n\n"
        f"Match stats: {format_stats_natural_language(match_stats)}\n"
    )

    if ml_scores:
        gpi = ml_scores.get("gpi", {})
        prompt += (
            f"\nPerformance score: {ml_scores.get('performance_score', 'N/A')}/100\n"
            f"Predicted tier: {ml_scores.get('predicted_tier', 'N/A')}\n"
            f"GPI skills — Farming: {gpi.get('farming', 'N/A')}, Vision: {gpi.get('vision', 'N/A')}, "
            f"Aggression: {gpi.get('aggression', 'N/A')}, Fighting: {gpi.get('fighting', 'N/A')}, "
            f"Survivability: {gpi.get('survivability', 'N/A')}, Objectives: {gpi.get('objectives', 'N/A')}\n"
        )

    if history_stats:
        prompt += "\nRecent match history:\n"
        for h in history_stats[-5:]:
            prompt += f"- {format_stats_natural_language(h)}\n"

    prompt += "\nCoaching suggestions:"
    return prompt


def _rule_based_suggestions(match_stats: dict) -> str:
    """Fallback rule-based suggestions when Ollama is unavailable."""
    suggestions = []
    deaths = match_stats.get("deaths", 0)
    vision = match_stats.get("vision_score", 0)
    kda = match_stats.get("kda", 0)
    damage = match_stats.get("damage_dealt", 0)

    if deaths > 5:
        suggestions.append("Focus on reducing deaths — play safer around enemy cooldowns and respect fog of war.")
    if vision < 15:
        suggestions.append("Improve vision control — aim for more wards and sweeper usage throughout the game.")
    if kda < 2:
        suggestions.append("Work on KDA by choosing better fight timing and positioning in teamfights.")
    if damage < 12000:
        suggestions.append("Look for more opportunities to deal damage — poke in lane and contribute in skirmishes.")

    return " ".join(suggestions) if suggestions else "Solid game — keep refining your mechanics and decision-making."


async def generate_suggestion_async(
    match_stats: dict,
    ml_scores: dict = None,
    history_stats: list = None
) -> str:
    """Generate AI coaching suggestion using Ollama (async).

    Falls back to rule-based suggestions if Ollama is unavailable.
    """
    try:
        prompt = _build_prompt(match_stats, ml_scores, history_stats)
        result = await generate_analysis(prompt)
        if result:
            return result
    except Exception as e:
        logger.warning(f"Ollama suggestion failed: {e}")

    return _rule_based_suggestions(match_stats)


def generate_suggestion(match_stats: dict, history_stats: list = None) -> str:
    """Synchronous suggestion (rule-based fallback for backwards compatibility).

    Used by stats_analyzer.get_match_details() which is sync.
    The async version is preferred for new code.
    """
    return _rule_based_suggestions(match_stats)
