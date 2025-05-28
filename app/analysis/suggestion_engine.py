try:
    from transformers import pipeline
    ML_AVAILABLE = True
    # Use a lightweight, open model and force CPU for compatibility
    try:
        llm = pipeline("text2text-generation", model="google/flan-t5-base", device=-1)
    except Exception as e:
        print(f"Warning: Failed to initialize ML model: {str(e)}")
        ML_AVAILABLE = False
        llm = None
except ImportError:
    ML_AVAILABLE = False
    llm = None

def format_stats_natural_language(stats: dict) -> str:
    """Format match statistics into natural language."""
    try:
        if not isinstance(stats, dict):
            raise ValueError(f"Invalid stats format. Expected dict, got {type(stats)}")
        
        required_fields = ['champion', 'position', 'win', 'kills', 'deaths', 'assists', 
                         'kda', 'damage_dealt', 'damage_taken', 'gold_earned', 
                         'vision_score', 'time_ccing_others']
        
        # Check for missing required fields
        missing_fields = [field for field in required_fields if field not in stats]
        if missing_fields:
            raise ValueError(f"Missing required fields in stats: {', '.join(missing_fields)}")
        
        return (
            f"Champion: {stats['champion']}, Position: {stats['position']}, "
            f"Win: {'Yes' if stats['win'] else 'No'}, "
            f"Kills: {stats['kills']}, Deaths: {stats['deaths']}, Assists: {stats['assists']}, "
            f"KDA: {stats['kda']}, Damage Dealt: {stats['damage_dealt']}, "
            f"Damage Taken: {stats['damage_taken']}, Gold Earned: {stats['gold_earned']}, "
            f"Vision Score: {stats['vision_score']}, Time CCing Others: {stats['time_ccing_others']}s"
        )
    except Exception as e:
        print(f"Error formatting stats: {str(e)}")
        return "Error: Invalid match statistics"

def generate_suggestion(match_stats: dict, history_stats: list = None) -> str:
    """
    Generate suggestions based on match statistics using rule-based analysis.
    match_stats: dict of stats for the current match
    history_stats: list of dicts for previous matches (optional)
    """
    try:
        if not isinstance(match_stats, dict):
            raise ValueError(f"Invalid match_stats format. Expected dict, got {type(match_stats)}")
        
        if history_stats is not None and not isinstance(history_stats, list):
            raise ValueError(f"Invalid history_stats format. Expected list, got {type(history_stats)}")
        
        suggestions = []
        
        # Analyze deaths
        deaths = match_stats.get('deaths', 0)
        if not isinstance(deaths, (int, float)):
            raise ValueError(f"Invalid deaths value. Expected number, got {type(deaths)}")
        
        if deaths > 5:
            suggestions.append("Focus on reducing deaths by playing more safely and respecting enemy cooldowns.")
        elif deaths > 3:
            suggestions.append("Consider your positioning to avoid unnecessary deaths.")
        
        # Analyze vision score
        vision_score = match_stats.get('vision_score', 0)
        if not isinstance(vision_score, (int, float)):
            raise ValueError(f"Invalid vision_score value. Expected number, got {type(vision_score)}")
        
        if vision_score < 20:
            suggestions.append("Improve vision control by placing more wards and clearing enemy vision.")
        elif vision_score < 30:
            suggestions.append("Your vision score is decent, but could be improved for better map control.")
        
        # Analyze KDA
        kda = match_stats.get('kda', 0)
        if not isinstance(kda, (int, float)):
            raise ValueError(f"Invalid kda value. Expected number, got {type(kda)}")
        
        if kda < 2:
            suggestions.append("Work on improving your KDA by focusing on positioning and teamfight participation.")
        elif kda < 3:
            suggestions.append("Your KDA is improving, but there's still room for better performance.")
        
        # Analyze damage dealt
        damage_dealt = match_stats.get('damage_dealt', 0)
        if not isinstance(damage_dealt, (int, float)):
            raise ValueError(f"Invalid damage_dealt value. Expected number, got {type(damage_dealt)}")
        
        if damage_dealt < 15000:
            suggestions.append("Focus on dealing more damage in teamfights and skirmishes.")
        
        # Analyze gold earned
        gold_earned = match_stats.get('gold_earned', 0)
        if not isinstance(gold_earned, (int, float)):
            raise ValueError(f"Invalid gold_earned value. Expected number, got {type(gold_earned)}")
        
        if gold_earned < 10000:
            suggestions.append("Work on improving your farming and objective control for better gold income.")
        
        # If we have history stats, look for trends
        if history_stats:
            try:
                recent_deaths = [h.get('deaths', 0) for h in history_stats[-3:]]
                if all(isinstance(d, (int, float)) for d in recent_deaths) and all(d > 5 for d in recent_deaths):
                    suggestions.append("You've been dying too much in recent games. Focus on survival and positioning.")
                
                recent_vision = [h.get('vision_score', 0) for h in history_stats[-3:]]
                if all(isinstance(v, (int, float)) for v in recent_vision) and all(v < 20 for v in recent_vision):
                    suggestions.append("Vision control has been consistently low. Make warding a priority.")
            except Exception as e:
                print(f"Warning: Error analyzing history stats: {str(e)}")
        
        return " ".join(suggestions) if suggestions else "Keep practicing and focus on improving your gameplay."
    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")
        return "Error: Unable to generate suggestions" 