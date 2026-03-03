import pandas as pd
from src.simulate import build_team_stats, simulate_matchup
from src.team_lookup import match_team

def main(day: str = "2026-02-25", n_sims: int = 1000, odds_path: str = "data/processed/todays_odds.csv"):
    odds = pd.read_csv(odds_path)
    odds = odds[odds["date"].astype(str).str.startswith(day)].copy()

    team_stats = build_team_stats("data/processed/current_season_games.csv")
    teams = sorted(team_stats.index.tolist())

    rows = []
    for _, r in odds.iterrows():
        home = match_team(str(r["home_team"]), teams)
        away = match_team(str(r["away_team"]), teams)

        out = simulate_matchup(home, away, team_stats, n_sims=n_sims)

        book_spread = float(r["book_spread_home"])
        book_total  = float(r["book_total"])

        # moneyline (allow blanks)
        book_ml = pd.to_numeric(r.get("book_ml_home", None), errors="coerce")
        book_ml = None if pd.isna(book_ml) else float(book_ml)

        # "edge" definitions (simple + effective):
        # spread edge: model spread - book spread (positive means model likes home more than book does)
        spread_edge = out["pred_spread_home"] - book_spread

        # total edge: model total - book total (positive means model leans over)
        total_edge = out["pred_total"] - book_total

        rows.append({
            "date": day,
            "home_team": home,
            "away_team": away,
            "model_spread_home": round(out["pred_spread_home"], 2),
            "book_spread_home": book_spread,
            "spread_edge": round(spread_edge, 2),
            "model_total": round(out["pred_total"], 2),
            "book_total": book_total,
            "total_edge": round(total_edge, 2),
            "p_home_win": round(out["p_home_win"], 3),
            "model_home_score": round(out["pred_home_score"], 1),
            "model_away_score": round(out["pred_away_score"], 1),
        })

    df = pd.DataFrame(rows)

    # rank by absolute edge (spread vs total)
    df["best_edge_abs"] = df[["spread_edge", "total_edge"]].abs().max(axis=1)
    df = df.sort_values("best_edge_abs", ascending=False)

    top = df.head(5).copy()

    # decide what the "best bet type" is for each row
    top["bet_type"] = top.apply(
    lambda x: "SPREAD" if abs(x["spread_edge"]) >= abs(x["total_edge"]) else "TOTAL",
    axis=1
    )

    top["pick"] = top.apply(
    lambda x: (
        f"{x['home_team']} {x['book_spread_home']:+.1f}" if x["bet_type"] == "SPREAD" and x["spread_edge"] < 0 else
        f"{x['home_team']} {x['book_spread_home']:+.1f}" if x["bet_type"] == "SPREAD" else
        ("OVER" if x["total_edge"] > 0 else "UNDER") + f" {x['book_total']:.1f}"
    ),
    axis=1
    )

    # compact, readable columns
    show_cols = [
    "home_team", "away_team",
    "bet_type", "pick",
    "model_spread_home", "book_spread_home", "spread_edge",
    "model_total", "book_total", "total_edge",
    "p_home_win", "model_home_score", "model_away_score",
    ]

    # make pandas stop wrapping and print cleanly
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 50)

    print(f"\nFULL BOARD for {day} (n_sims={n_sims})")

    # round for clean display
    display_cols = [
        "home_team", "away_team",
        "model_spread_home", "book_spread_home", "spread_edge",
        "model_total", "book_total", "total_edge",
        "p_home_win",
        "model_home_score", "model_away_score"
]

    df_display = df[display_cols].copy()

    # round numeric columns for readability
    for c in ["model_spread_home", "spread_edge", "model_total", "total_edge", "p_home_win"]:
        df_display[c] = df_display[c].round(2)

    print(df_display.to_string(index=False))
    return df


if __name__ == "__main__":
    import sys
    import os

    day = sys.argv[1] if len(sys.argv) > 1 else "2026-02-27"
    sims = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    odds_path = sys.argv[3] if len(sys.argv) > 3 else "data/processed/todays_odds.csv"

    # 1) Run the model (df is created here)
    df = main(day, n_sims=sims, odds_path=odds_path)

    # 2) Save outputs
    out_dir = "data/outputs"
    os.makedirs(out_dir, exist_ok=True)

    csv_path = f"{out_dir}/board_{day}.csv"
    xlsx_path = f"{out_dir}/board_{day}.xlsx"

    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)

    print(f"\n💾 Saved board to:")
    print(csv_path)
    print(xlsx_path)