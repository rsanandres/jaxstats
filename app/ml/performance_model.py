from typing import Dict, List, Tuple

class PerformanceModel:
    def __init__(self):
        pass

    def _calculate_basic_score(self, match_data: Dict) -> float:
        """Calculate a basic performance score based on key metrics."""
        basic_stats = match_data["basic_stats"]
        vision_stats = match_data["vision_stats"]
        damage_stats = match_data["damage_stats"]
        timeline = match_data["timeline"]
        
        # Initialize score components
        kda_score = min(basic_stats["kda"] * 10, 30)  # Max 30 points for KDA
        cs_score = min(basic_stats["cs_per_min"] * 2, 20)  # Max 20 points for CS
        vision_score = min(vision_stats["vision_score"] * 0.5, 15)  # Max 15 points for vision
        damage_score = min(damage_stats["damage_dealt"] / 1000, 20)  # Max 20 points for damage
        objective_score = min(match_data["objective_stats"]["objectives_secured"] * 5, 15)  # Max 15 points for objectives
        
        # Calculate total score
        total_score = kda_score + cs_score + vision_score + damage_score + objective_score
        
        # Penalties
        if basic_stats["deaths"] > 5:
            total_score -= (basic_stats["deaths"] - 5) * 2  # Penalty for excessive deaths
        
        if vision_stats["vision_score"] < 10:
            total_score -= 5  # Penalty for poor vision control
        
        # Ensure score is between 0 and 100
        return max(0, min(100, total_score))

    def predict_performance(self, match_data: Dict) -> Tuple[float, str]:
        """Calculate performance score and generate analysis."""
        score = self._calculate_basic_score(match_data)
        
        # Generate analysis based on score
        if score >= 80:
            analysis = "Exceptional performance! You dominated the game with excellent mechanics and decision-making."
        elif score >= 60:
            analysis = "Good performance. You made positive contributions to the team's success."
        elif score >= 40:
            analysis = "Average performance. There's room for improvement in several areas."
        else:
            analysis = "Below average performance. Focus on improving your fundamentals and decision-making."
        
        # Add specific feedback based on key metrics
        if match_data["basic_stats"]["kda"] < 2:
            analysis += " Your KDA suggests you need to work on survival and positioning."
        if match_data["vision_stats"]["vision_score"] < 20:
            analysis += " Vision control needs improvement - focus on warding and clearing enemy vision."
        if match_data["basic_stats"]["cs_per_min"] < 5:
            analysis += " Your CS per minute is low - practice last hitting and wave management."
        
        return score, analysis 