import numpy as np
import pandas as pd

GAMES_FP = "data/processed/current_season_games.csv"
RATINGS_FP = "data/processed/team_ratings.csv"
LINES_FP = "data/raw/today_lines.csv"

N_SIMS = 1000

# Simple knobs (good enough for a class project)
HCA_POINTS = 3.5          # home court advantage in points
POINTS_SD_BASE = 11.5     # typical CBB single-team scoring SD
TOTAL_SD_BASE = 15.0      # typical game total SD (rough)


def canonical(name: str) -> str:
    """Light cleanup; keep your full names if you prefer."""
    return str(name).strip()


def load_ratings():
    r = pd.read_csv(RATINGS_FP)
    r["team"] = r["team"].map(canonical)
    # Expect columns: team, elo
    return r.set_index("team")


def estimate_expected_points(home_team, away_team, r):
    """
    Convert Elo difference into expected margin, then map to expected points.
    This is a simplified model:
      - margin = (elo_home - elo_away) * k + HCA
      - total = baseline_total (from recent games) + small adjustment
    """
    # Baseline total from completed games in your season file (if available)
    games = pd.read_csv(GAMES_FP)
    games = games[games["status"].astype(str).str.lower().eq("final")].copy()
    games["home_team"] = games["home_team"].map(canonical)
    games["away_team"] = games["away_team"].map(canonical)

    games["home_score"] = pd.to_numeric(games["home_score"], errors="coerce")
    games["away_score"] = pd.to_numeric(games["away_score"], errors="coerce")
    games = games.dropna(subset=["home_score", "away_score"])

    baseline_total = float((games["home_score"] + games["away_score"]).tail(300).mean()) if len(games) else 145.0

    elo_home = float(r.loc[home_team, "elo"])
    elo_away = float(r.loc[away_team, "elo"])
    elo_diff = elo_home - elo_away

    # Elo -> margin scale (tuneable). 25 Elo ~ ~1 point is reasonable-ish.
    k = 1.0 / 25.0
    exp_margin_home = elo_diff * k + HCA_POINTS

    # Split baseline total into two team expected points using the margin
    exp_home = baseline_total / 2.0 + exp_margin_home / 2.0
    exp_away = baseline_total / 2.0 - exp_margin_home / 2.0

    return exp_home, exp_away, exp_margin_home, baseline_total


def simulate_game(exp_home, exp_away, n=N_SIMS):
    # Independent normals is a simplification; fine for a first version.
    home_scores = np.random.normal(loc=exp_home, scale=POINTS_SD_BASE, size=n)
    away_scores = np.random.normal(loc=exp_away, scale=POINTS_SD_BASE, size=n)

    # clamp to realistic score floor
    home_scores = np.maximum(home_scores, 35)
    away_scores = np.maximum(away_scores, 35)

    # round to integers
    home_scores = np.rint(home_scores).astype(int)
    away_scores = np.rint(away_scores).astype(int)

    margin_home = home_scores - away_scores
    total = home_scores + away_scores
    return margin_home, total


def prob_cover_spread(margin_home, spread_home):
    """
    If spread_home = -2.5, home covers if margin_home > 2.5.
    If spread_home = +4.5, home covers if margin_home > -4.5.
    """
    return float(np.mean(margin_home > (-spread_home)))


def prob_over(total_sims, total_line):
    return float(np.mean(total_sims > total_line))


def main():
    lines = pd.read_csv(LINES_FP)
    lines["home_team"] = lines["home_team"].map(canonical)
    lines["away_team"] = lines["away_team"].map(canonical)

    r = load_ratings()

    rows = []
    for _, g in lines.iterrows():
        home = g["home_team"]
        away = g["away_team"]

        if home not in r.index or away not in r.index:
            rows.append({
                "home_team": home, "away_team": away,
                "error": "team not found in team_ratings.csv (name mismatch)"
            })
            continue

        exp_home, exp_away, exp_margin, baseline_total = estimate_expected_points(home, away, r)
        margin_sims, total_sims = simulate_game(exp_home, exp_away, n=N_SIMS)

        spread_home = float(g["spread_home"])
        total_line = float(g["total"])

        p_cover = prob_cover_spread(margin_sims, spread_home)
        p_over = prob_over(total_sims, total_line)

        model_spread = float(np.mean(margin_sims))
        model_total = float(np.mean(total_sims))

        # "Edge" = model minus book (bigger absolute = more disagreement)
        spread_edge_pts = model_spread - (-spread_home)  # compare margin vs implied margin
        total_edge_pts = model_total - total_line

        rows.append({
            "home_team": home,
            "away_team": away,
            "model_margin_home": round(model_spread, 2),
            "book_spread_home": spread_home,
            "spread_edge_pts": round(spread_edge_pts, 2),
            "p_home_cover": round(p_cover, 3),
            "model_total": round(model_total, 2),
            "book_total": total_line,
            "total_edge_pts": round(total_edge_pts, 2),
            "p_over": round(p_over, 3),
        })

    out = pd.DataFrame(rows)

    # rank by strongest disagreements (simple heuristic)
    out_ok = out[~out.get("error", "").astype(str).str.len().gt(0)].copy() if "error" in out.columns else out.copy()
    if len(out_ok):
        out_ok["rank_score"] = out_ok["spread_edge_pts"].abs() + out_ok["total_edge_pts"].abs()
        out_ok = out_ok.sort_values("rank_score", ascending=False)
        print("\nTOP 5 (by model vs book disagreement):\n")
        print(out_ok.head(5).drop(columns=["rank_score"]).to_string(index=False))
    else:
        print(out.to_string(index=False))


if __name__ == "__main__":
    main()