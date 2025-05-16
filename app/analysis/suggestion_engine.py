from transformers import pipeline

# Use a lightweight, open model and force CPU for compatibility
llm = pipeline("text2text-generation", model="google/flan-t5-base", device=-1)

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
    Generate a suggestion for a match using an LLM.
    match_stats: dict of stats for the current match
    history_stats: list of dicts for previous matches (optional)
    """
    prompt = (
        "You are a League of Legends coach. Analyze the following match stats and give one or two actionable suggestions for improvement.\n"
        f"Current match stats: {format_stats_natural_language(match_stats)}\n"
    )
    if history_stats:
        prompt += "Recent matches:\n"
        for h in history_stats:
            prompt += f"- {format_stats_natural_language(h)}\n"
    prompt += "Suggestions:"

    result = llm(prompt, max_new_tokens=128, do_sample=True, temperature=0.7)
    suggestion = result[0]['generated_text'].strip()
    return suggestion 