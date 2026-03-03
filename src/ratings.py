import pandas as pd

def expected_score(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))

def update_elo(r_home: float, r_away: float, home_win: float, k: float = 20.0):
    # home_win: 1 if home won, 0 if away won
    e_home = expected_score(r_home, r_away)
    e_away = 1.0 - e_home
    r_home_new = r_home + k * (home_win - e_home)
    r_away_new = r_away + k * ((1.0 - home_win) - e_away)
    return r_home_new, r_away_new

def main():
    print("📊 Loading current season games...")
    df = pd.read_csv("data/processed/current_season_games.csv")

    # Keep only completed games with scores
    df = df[df["status"].astype(str).str.lower().eq("final")].copy()
    df = df.dropna(subset=["home_team", "away_team", "home_score", "away_score"])

    # Convert scores to numeric
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df = df.dropna(subset=["home_score", "away_score"])

    # Sort by date (optional but nice for time-ordered Elo)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")

    teams = pd.unique(df[["home_team", "away_team"]].values.ravel("K"))
    ratings = {t: 1500.0 for t in teams}

    print(f"✅ Games loaded: {len(df)}")
    print(f"✅ Teams found: {len(teams)}")

    for _, row in df.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        hs = float(row["home_score"])
        ats = float(row["away_score"])

        home_win = 1.0 if hs > ats else 0.0
        r_home, r_away = ratings[home], ratings[away]
        r_home_new, r_away_new = update_elo(r_home, r_away, home_win, k=20.0)

        ratings[home] = r_home_new
        ratings[away] = r_away_new

    out = (
        pd.DataFrame({"team": list(ratings.keys()), "elo": list(ratings.values())})
        .sort_values("elo", ascending=False)
        .reset_index(drop=True)
    )

    out_path = "data/processed/team_ratings.csv"
    out.to_csv(out_path, index=False)

    print(f"💾 Saved ratings to: {out_path}")
    print("🏀 Top 10 teams by Elo:")
    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()