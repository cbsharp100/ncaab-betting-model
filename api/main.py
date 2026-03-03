from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np

from pathlib import Path

# ---- Import your pricing helpers ----
# Make sure pricing.py is in ncaab-betting-model/src/pricing.py
from src.pricing import prob_to_moneyline, rating_to_spread, expected_value

APP_ROOT = Path(__file__).resolve().parents[1]
RATINGS_PATH = APP_ROOT / "data" / "processed" / "team_ratings.csv"

HCA_POINTS = 3.5  # home-court advantage in spread points (3–4 is typical)

app = FastAPI(title="NCAAB Betting Model API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],  # adjust as needed for your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    home_team: str
    away_team: str
    sportsbook_moneyline_home: int | None = None  # optional

class PredictResponse(BaseModel):
    home_team: str
    away_team: str
    home_elo: float
    away_elo: float
    elo_diff: float
    p_home_win: float
    fair_moneyline_home: int
    est_spread_home: float
    sportsbook_moneyline_home: int | None = None
    ev_home_bet: float | None = None


def find_team_name(user_input: str, team_list: list[str]) -> str:
    s = user_input.lower().strip()

    # exact match first
    for t in team_list:
        if t.lower() == s:
            return t

    # partial match
    matches = [t for t in team_list if s in t.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # deterministic: pick shortest match (usually the “main” name)
        matches.sort(key=len)
        return matches[0]

    raise ValueError(f"No team found matching '{user_input}'")


def elo_to_prob(diff: float) -> float:
    # classic Elo win prob
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    ratings = pd.read_csv(RATINGS_PATH)
    teams = ratings["team"].tolist()

    home = find_team_name(req.home_team, teams)
    away = find_team_name(req.away_team, teams)

    r_home = float(ratings.loc[ratings["team"] == home, "elo"].values[0])
    r_away = float(ratings.loc[ratings["team"] == away, "elo"].values[0])

    # Convert home-court points -> Elo points (approx). 1 Elo ~ 0.04 spread points means:
    # spread = elo * 0.04  => elo = spread / 0.04
    HCA_ELO = HCA_POINTS / 0.04

    diff = (r_home - r_away) + HCA_ELO
    p_home = float(elo_to_prob(diff))
    fair_ml = int(prob_to_moneyline(p_home))
    est_spread = float(rating_to_spread(diff, factor=0.04))  # spread points

    ev = None
    if req.sportsbook_moneyline_home is not None:
        ev = float(expected_value(p_home, req.sportsbook_moneyline_home, stake=1.0))

    return PredictResponse(
        home_team=home,
        away_team=away,
        home_elo=r_home,
        away_elo=r_away,
        elo_diff=diff,
        p_home_win=p_home,
        fair_moneyline_home=fair_ml,
        est_spread_home=est_spread,
        sportsbook_moneyline_home=req.sportsbook_moneyline_home,
        ev_home_bet=ev,
    )