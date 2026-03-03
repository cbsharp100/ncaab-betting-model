import re
from difflib import get_close_matches

def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

def match_team(user_input: str, teams: list[str]) -> str:
    """
    Matches 'Arizona' -> 'Arizona Wildcats' using simple fuzzy matching.
    """
    ui = _norm(user_input)
    norm_map = {_norm(t): t for t in teams}

    # direct contains match (fast + intuitive)
    for nt, original in norm_map.items():
        if ui == nt or ui in nt:
            return original

    # fuzzy fallback
    candidates = get_close_matches(ui, list(norm_map.keys()), n=1, cutoff=0.5)
    if not candidates:
        raise ValueError(f"Team not found: {user_input}")
    return norm_map[candidates[0]]