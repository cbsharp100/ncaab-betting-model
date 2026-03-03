import numpy as np
import pandas as pd

HCA_POINTS = 3.5  # home court advantage in points

def build_team_stats(games_csv="data/processed/current_season_games.csv") -> pd.DataFrame:
    df = pd.read_csv(games_csv)

    # keep finals only (you already have these)
    df["status"] = df["status"].astype(str).str.lower()
    df = df[df["status"].eq("final")].copy()
    df = df.dropna(subset=["home_team", "away_team", "home_score", "away_score"])

    # numeric
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df = df.dropna(subset=["home_score", "away_score"])

    home = df.groupby("home_team").agg(
        pf_home=("home_score", "mean"),
        pa_home=("away_score", "mean"),
        n_home=("home_score", "count"),
    )

    away = df.groupby("away_team").agg(
        pf_away=("away_score", "mean"),
        pa_away=("home_score", "mean"),
        n_away=("away_score", "count"),
    )

    stats = home.join(away, how="outer").fillna(0)
    stats["games"] = stats["n_home"] + stats["n_away"]

    # blended points for/against
    stats["pf"] = np.where(stats["games"] > 0,
                           (stats["pf_home"] * stats["n_home"] + stats["pf_away"] * stats["n_away"]) / np.maximum(stats["games"], 1),
                           0)
    stats["pa"] = np.where(stats["games"] > 0,
                           (stats["pa_home"] * stats["n_home"] + stats["pa_away"] * stats["n_away"]) / np.maximum(stats["games"], 1),
                           0)

    # league averages
    league_pf = df[["home_score", "away_score"]].to_numpy().mean()
    league_total = (df["home_score"] + df["away_score"]).mean()

    stats.attrs["league_pf"] = float(league_pf)
    stats.attrs["league_total"] = float(league_total)
    return stats

def simulate_matchup(
    home_team: str,
    away_team: str,
    team_stats: pd.DataFrame,
    n_sims: int = 1000,
    score_sd: float = 11.5,  # typical basketball score noise
) -> dict:
    # fallback if team has no stats yet
    league_pf = team_stats.attrs.get("league_pf", 70.0)

    def get_pf_pa(team: str):
        if team in team_stats.index and team_stats.loc[team, "games"] > 0:
            return float(team_stats.loc[team, "pf"]), float(team_stats.loc[team, "pa"])
        return league_pf, league_pf

    home_pf, home_pa = get_pf_pa(home_team)
    away_pf, away_pa = get_pf_pa(away_team)

    # expected points = blend (your offense + their defense) around league avg
    home_mu = (home_pf + away_pa) / 2.0 + (HCA_POINTS / 2.0)
    away_mu = (away_pf + home_pa) / 2.0 - (HCA_POINTS / 2.0)

    # simulate with Normal (simple, works surprisingly well)
    home_scores = np.random.normal(home_mu, score_sd, size=n_sims)
    away_scores = np.random.normal(away_mu, score_sd, size=n_sims)

    # clamp to reasonable min
    home_scores = np.clip(home_scores, 40, 120)
    away_scores = np.clip(away_scores, 40, 120)

    margin = home_scores - away_scores
    total = home_scores + away_scores

    return {
        "home_team": home_team,
        "away_team": away_team,
        "pred_home_score": float(np.mean(home_scores)),
        "pred_away_score": float(np.mean(away_scores)),
        "pred_spread_home": float(np.mean(margin)),     # positive = home favored by X
        "pred_total": float(np.mean(total)),
        "p_home_win": float(np.mean(margin > 0)),
        "spread_sd": float(np.std(margin)),
        "total_sd": float(np.std(total)),
    }