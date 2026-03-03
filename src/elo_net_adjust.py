# src/elo_net_adjust.py
import pandas as pd
from difflib import get_close_matches
from typing import Optional

from src.name_normalize import team_key_basic

ELO_BASE = 1500.0
NET_SCALE = 1000.0  # how strong NET influences prior


ALIASES = {
    # major schools
    "uconn": "connecticut",
    "st johns": "st johns",
    "st john s": "st johns",
    "saint johns": "st johns",

    # UNC system
    "unc wilmington": "north carolina wilmington",
    "uncw": "north carolina wilmington",

    # directional states
    "northern iowa": "northern iowa",
    "southern illinois": "southern illinois",
    "illinois chicago": "illinois chicago",

    # cal state schools
    "cal state fullerton": "cs fullerton",
    "cal state northridge": "cs northridge",

    # common abbreviations
    "fdu": "fairleigh dickinson",
    "nku": "northern kentucky",
    "siu": "southern illinois",
}


STOP_WORDS = {
    # These words can be part of the school name, so don't trim past them
    "state", "st", "saint", "college", "university", "tech", "a", "and", "m"
}


def apply_alias(k: str) -> str:
    return ALIASES.get(k, k)


def best_net_rank_for_elo_team(elo_team: str, net_key_to_rank: dict) -> Optional[float]:
    """
    Match Elo team (often includes mascot) to NET team (usually school only)
    Strategy:
      1) normalize key
      2) try exact
      3) trim tail tokens until match (removes mascot words safely)
      4) fuzzy fallback
    """
    net_keys = list(net_key_to_rank.keys())

    ek = apply_alias(team_key_basic(elo_team))

    # exact
    if ek in net_key_to_rank:
        return float(net_key_to_rank[ek])

    parts = ek.split()

    # trim from end until match
    while len(parts) >= 1:
        cand = " ".join(parts)
        cand = apply_alias(cand)

        if cand in net_key_to_rank:
            return float(net_key_to_rank[cand])

        parts = parts[:-1]

    # fuzzy fallback (helps weird punctuation/spacing)
    m = get_close_matches(ek, net_keys, n=1, cutoff=0.78)
    if m:
        return float(net_key_to_rank[m[0]])

    return None


def net_rank_to_elo_prior(rank: int, n_teams: int) -> float:
    score = (n_teams - rank) / (n_teams - 1)  # best ~1, worst ~0
    return ELO_BASE + (score - 0.5) * NET_SCALE


def compute_games_played(games_csv: str = "data/processed/current_season_games.csv") -> pd.DataFrame:
    g = pd.read_csv(games_csv)

    # Try common column names; adjust if yours differ
    home_col = "home_team"
    away_col = "away_team"
    if home_col not in g.columns or away_col not in g.columns:
        raise RuntimeError(f"current_season_games.csv missing {home_col}/{away_col}. Columns: {g.columns.tolist()}")

    gp = pd.concat([g[home_col], g[away_col]]).value_counts().reset_index()
    gp.columns = ["team", "games_played"]
    return gp


def blend_elo_with_net(
    elo_csv: str = "data/processed/team_ratings.csv",
    net_csv: str = "data/processed/net_rankings.csv",
    games_csv: str = "data/processed/current_season_games.csv",
    out_csv: str = "data/processed/team_ratings_net.csv",
) -> pd.DataFrame:
    elo = pd.read_csv(elo_csv)
    net = pd.read_csv(net_csv)

    if "team" not in elo.columns or "elo" not in elo.columns:
        raise RuntimeError(f"ELO file must have columns team, elo. Got: {elo.columns.tolist()}")
    if "team" not in net.columns or "rank" not in net.columns:
        raise RuntimeError(f"NET file must have columns team, rank. Got: {net.columns.tolist()}")

    # NET key -> rank map
    net["net_key"] = net["team"].apply(lambda x: apply_alias(team_key_basic(x)))
    net_key_to_rank = dict(zip(net["net_key"], net["rank"]))

    # match every elo team to net rank
    elo["net_rank"] = elo["team"].apply(lambda t: best_net_rank_for_elo_team(t, net_key_to_rank))

    matches = int(pd.notna(elo["net_rank"]).sum())
    total = len(elo)
    print(f"NET matches: {matches} / {total}")
    print(f"Missing NET: {total - matches} / {total}")

    if (total - matches) > 0:
        print("\nSample missing teams:")
        print(elo.loc[elo["net_rank"].isna(), ["team"]].head(25).to_string(index=False))

     # compute games played (real, not constant)
    gp = compute_games_played(games_csv)
    elo = elo.merge(gp, on="team", how="left")
    elo["games_played"] = pd.to_numeric(elo["games_played"], errors="coerce").fillna(0)

    # --- FIX: enforce minimum games played to avoid small-sample bias ---
    # Floor at 10 games minimum so tiny-sample teams don't float to the top
    elo["games_played_adj"] = elo["games_played"].clip(lower=10)

    # Weight: more games → trust Elo more
    elo["w"] = elo["games_played_adj"] / (elo["games_played_adj"] + 10.0)

    # Final blended rating
    elo["elo_final"] = elo["w"] * elo["elo"].astype(float) + (1.0 - elo["w"]) * elo["elo_prior"]

    # sort best → worst by final rating
    elo = elo.sort_values("elo_final", ascending=False).reset_index(drop=True)

    # save output
    elo.to_csv(out_csv, index=False)
    print(f"✅ Saved blended ratings to {out_csv}")
    return elo