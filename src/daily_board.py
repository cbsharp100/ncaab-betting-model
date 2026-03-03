# src/daily_board.py
from __future__ import annotations

import sys
from datetime import datetime
import pandas as pd

from src.simulate import build_team_stats, simulate_matchup
from src.team_lookup import match_team
from src.pricing import expected_value  # uses American ML

# --------- CONFIG ----------
GAMES_CSV = "data/processed/current_season_games.csv"
ODDS_CSV = "data/processed/todays_odds.csv"

# If you want home-court baked into sims, do it inside simulate_matchup
# or apply a simple adjustment here (optional).
# HCA_POINTS = 3.0  # (not used in this script by default)


def _clean_print(df: pd.DataFrame, max_rows: int = 50):
    """Print a readable table without wrapping into chaos."""
    with pd.option_context(
        "display.max_columns",
        None,
        "display.width",
        200,
        "display.max_colwidth",
        40,
    ):
        print(df.head(max_rows).to_string(index=False))


def make_daily_board(day: str, n_sims: int = 1000) -> pd.DataFrame:
    # Load odds board
    odds = pd.read_csv(ODDS_CSV)

    # date filter (works if odds["date"] is 'YYYY-MM-DD...' or actual date)
    odds["date_str"] = odds["date"].astype(str)
    odds = odds[odds["date_str"].str.startswith(day)].copy()

    if odds.empty:
        raise ValueError(
            f"No rows found in {ODDS_CSV} for date starting with '{day}'. "
            f"Check the 'date' column format and the day you passed."
        )

    # Build team stats from season results
    team_stats = build_team_stats(GAMES_CSV)
    teams = sorted(team_stats.index.tolist())

    rows = []

    for _, r in odds.iterrows():
        # Match team names robustly
        home = match_team(str(r["home_team"]), teams)
        away = match_team(str(r["away_team"]), teams)

        # Simulate
        out = simulate_matchup(home, away, team_stats, n_sims=n_sims)

        # Required book lines
        book_spread = float(r["book_spread_home"])
        book_total = float(r["book_total"])

        # Optional moneyline
        book_ml_home = None
        if "book_ml_home" in odds.columns and pd.notna(r.get("book_ml_home")):
            try:
                book_ml_home = float(r["book_ml_home"])
            except Exception:
                book_ml_home = None

        model_spread = float(out["pred_spread_home"])
        model_total = float(out["pred_total"])

        spread_edge = model_spread - book_spread
        total_edge = model_total - book_total

        # Decide “best bet type” (spread vs total) by bigger absolute edge
        bet_type = "SPREAD" if abs(spread_edge) >= abs(total_edge) else "TOTAL"

        # Build pick text
        if bet_type == "SPREAD":
            # If book spread home is negative, it means home favored by that number
            # Recommendation depends on whether model spread is "more home" or "less home"
            if spread_edge > 0:
                pick = f"{home} {book_spread:+g}"  # take home at book number
            else:
                # take away + opposite spread
                pick = f"{away} {(-book_spread):+g}"
        else:
            pick = "OVER" if total_edge > 0 else "UNDER"
            pick = f"{pick} {book_total:g}"

        # Moneyline expected value (optional)
        ev_home = None
        if book_ml_home is not None:
            ev_home = float(expected_value(out["p_home_win"], book_ml_home, stake=1.0))

        rows.append(
            {
                "date": day,
                "home_team": home,
                "away_team": away,
                "model_spread_home": round(model_spread, 2),
                "book_spread_home": round(book_spread, 2),
                "spread_edge": round(spread_edge, 2),
                "model_total": round(model_total, 2),
                "book_total": round(book_total, 2),
                "total_edge": round(total_edge, 2),
                "p_home_win": round(float(out["p_home_win"]), 3),
                "model_home_score": round(float(out["pred_home_score"]), 1),
                "model_away_score": round(float(out["pred_away_score"]), 1),
                "bet_type": bet_type,
                "pick": pick,
                "ml_home": book_ml_home,
                "ml_ev_home": (round(ev_home, 3) if ev_home is not None else None),
            }
        )

    df = pd.DataFrame(rows)

    # Rank by “best edge”
    df["best_edge_abs"] = df[["spread_edge", "total_edge"]].abs().max(axis=1)
    df = df.sort_values("best_edge_abs", ascending=False)

    return df


def main():
    # Default day = today (local)
    today = datetime.now().strftime("%Y-%m-%d")
    day = sys.argv[1] if len(sys.argv) > 1 else today
    n_sims = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    df = make_daily_board(day, n_sims=n_sims)

    print(f"\nDAILY BOARD for {day} (n_sims={n_sims})")
    board_cols = [
        "home_team",
        "away_team",
        "book_spread_home",
        "book_total",
        "ml_home",
    ]
    board_cols = [c for c in board_cols if c in df.columns]
    _clean_print(df[board_cols], max_rows=200)

    top = df.head(5).copy()

    # Keep the output super readable
    top_cols = [
        "home_team",
        "away_team",
        "bet_type",
        "pick",
        "model_spread_home",
        "book_spread_home",
        "spread_edge",
        "model_total",
        "book_total",
        "total_edge",
        "p_home_win",
        "model_home_score",
        "model_away_score",
        "ml_home",
        "ml_ev_home",
    ]
    top_cols = [c for c in top_cols if c in top.columns]

    print("\nTOP 5 BEST BETS:")
    _clean_print(top[top_cols], max_rows=50)


if __name__ == "__main__":
    main()