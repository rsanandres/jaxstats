def format_stats_natural_language(stats):
    return (
        f"Champion: {stats.get('champion', 'Unknown')}, Position: {stats.get('position', 'Unknown')}, "
        f"Win: {'Yes' if stats.get('win') else 'No'}, "
        f"Kills: {stats.get('kills', 0)}, Deaths: {stats.get('deaths', 0)}, Assists: {stats.get('assists', 0)}, "
        f"KDA: {stats.get('kda', 0)}, Damage Dealt: {stats.get('damage_dealt', 0)}, "
        f"Damage Taken: {stats.get('damage_taken', 0)}, Gold Earned: {stats.get('gold_earned', 0)}, "
        f"Vision Score: {stats.get('vision_score', 0)}, Time CCing Others: {stats.get('time_ccing_others', 0)}s"
    )

def generate_suggestion(match_stats: dict, history_stats: list = None) -> str:
    """Placeholder — will be replaced by Ollama in Phase 3."""
    return "Analysis will be available once the AI engine is connected."
