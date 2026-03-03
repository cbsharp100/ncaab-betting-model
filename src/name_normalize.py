# src/name_normalize.py
import re

def team_key_basic(s: str) -> str:
    """
    Normalize names for matching NET vs Elo team labels.
    Key improvements:
      - standardize punctuation/spacing
      - convert token 'state' -> 'st' (NET usually uses St.)
      - normalize St. John's -> st johns
    """
    s = str(s).lower().strip()

    # standardize a few common patterns first
    s = s.replace("&", " and ")
    s = s.replace("st.", "st ")   # keep "st" form (NET usually uses St.)
    s = s.replace("saint", "st")  # optional: treat saint as st for matching

    # remove punctuation
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # --- critical: NET uses "St" for "State" almost everywhere ---
    # convert the token "state" to "st"
    s = re.sub(r"\bstate\b", "st", s)

    # normalize "john s" -> "johns" (from St. John's)
    s = re.sub(r"\bjohn\s+s\b", "johns", s)

    # collapse spaces again
    s = re.sub(r"\s+", " ", s).strip()
    return s