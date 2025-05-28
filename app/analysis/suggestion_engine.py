try:
    from transformers import pipeline
    ML_AVAILABLE = True
    # Use a lightweight, open model and force CPU for compatibility
    llm = pipeline("text2text-generation", model="google/flan-t5-base", device=-1)
except ImportError:
    ML_AVAILABLE = False
    llm = None

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
    """
    Generate suggestions based on match statistics using rule-based analysis.
    match_stats: dict of stats for the current match
    history_stats: list of dicts for previous matches (optional)
    """
    suggestions = []
    
    # Analyze deaths
    deaths = match_stats.get('deaths', 0)
    if deaths > 5:
        suggestions.append("Focus on reducing deaths by playing more safely and respecting enemy cooldowns.")
    elif deaths > 3:
        suggestions.append("Consider your positioning to avoid unnecessary deaths.")
    
    # Analyze vision score
    vision_score = match_stats.get('vision_score', 0)
    if vision_score < 20:
        suggestions.append("Improve vision control by placing more wards and clearing enemy vision.")
    elif vision_score < 30:
        suggestions.append("Your vision score is decent, but could be improved for better map control.")
    
    # Analyze KDA
    kda = match_stats.get('kda', 0)
    if kda < 2:
        suggestions.append("Work on improving your KDA by focusing on positioning and teamfight participation.")
    elif kda < 3:
        suggestions.append("Your KDA is improving, but there's still room for better performance.")
    
    # Analyze damage dealt
    damage_dealt = match_stats.get('damage_dealt', 0)
    if damage_dealt < 15000:
        suggestions.append("Focus on dealing more damage in teamfights and skirmishes.")
    
    # Analyze gold earned
    gold_earned = match_stats.get('gold_earned', 0)
    if gold_earned < 10000:
        suggestions.append("Work on improving your farming and objective control for better gold income.")
    
    # If we have history stats, look for trends
    if history_stats:
        recent_deaths = [h.get('deaths', 0) for h in history_stats[-3:]]
        if all(d > 5 for d in recent_deaths):
            suggestions.append("You've been dying too much in recent games. Focus on survival and positioning.")
        
        recent_vision = [h.get('vision_score', 0) for h in history_stats[-3:]]
        if all(v < 20 for v in recent_vision):
            suggestions.append("Vision control has been consistently low. Make warding a priority.")
    
    return " ".join(suggestions) if suggestions else "Keep practicing and focus on improving your gameplay." 