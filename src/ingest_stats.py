import argparse
from pathlib import Path
import sys
import pandas as pd

# src/ingest_stats.py


DEFAULT_RAW = Path("data/raw/ncaa")
DEFAULT_OUT = Path("data/processed")


def ingest_kaggle_ncaa(raw_dir: Path = DEFAULT_RAW, out_dir: Path = DEFAULT_OUT):
    """
    Ingests Kaggle NCAA CSVs from raw_dir and writes normalized outputs to out_dir.
    Expects:
      - MRegularSeasonCompactResults.csv
      - MNCAATourneyCompactResults.csv
      - MTeams.csv
    """
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    reg_fp = raw_dir / "MRegularSeasonCompactResults.csv"
    tou_fp = raw_dir / "MNCAATourneyCompactResults.csv"
    teams_fp = raw_dir / "MTeams.csv"

    for fp in (reg_fp, tou_fp, teams_fp):
        if not fp.exists():
            raise FileNotFoundError(f"Missing required file: {fp}")

    reg = pd.read_csv(reg_fp)
    tou = pd.read_csv(tou_fp)
    teams = pd.read_csv(teams_fp)

    games = pd.concat([reg.assign(stage="regular"), tou.assign(stage="tourney")], ignore_index=True)

    games = games.rename(
        columns={
            "Season": "season",
            "DayNum": "daynum",
            "WTeamID": "teamA_id",
            "WScore": "teamA_score",
            "LTeamID": "teamB_id",
            "LScore": "teamB_score",
        }
    )

    # compute result and margin from scores (robust if input mapping changes)
    games["teamA_score"] = pd.to_numeric(games["teamA_score"], errors="coerce")
    games["teamB_score"] = pd.to_numeric(games["teamB_score"], errors="coerce")
    games["teamA_win"] = (games["teamA_score"] > games["teamB_score"]).astype(int)
    games["margin"] = games["teamA_score"] - games["teamB_score"]

    teams = teams.rename(columns={"TeamID": "team_id", "TeamName": "team_name"})
    games = games.merge(
        teams.rename(columns={"team_id": "teamA_id", "team_name": "teamA_name"}),
        on="teamA_id",
        how="left",
    )
    games = games.merge(
        teams.rename(columns={"team_id": "teamB_id", "team_name": "teamB_name"}),
        on="teamB_id",
        how="left",
    )

    games_fp = out_dir / "games.csv"
    teams_fp_out = out_dir / "teams.csv"
    games.to_csv(games_fp, index=False)
    teams.to_csv(teams_fp_out, index=False)

    return games_fp, teams_fp_out


def main(argv=None):
    p = argparse.ArgumentParser(description="Ingest Kaggle NCAA data")
    p.add_argument("--raw", "-r", type=Path, default=DEFAULT_RAW, help="raw input directory")
    p.add_argument("--out", "-o", type=Path, default=DEFAULT_OUT, help="output directory")
    args = p.parse_args(argv)

    try:
        games_fp, teams_fp = ingest_kaggle_ncaa(args.raw, args.out)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Saved: {games_fp}  ({pd.read_csv(games_fp).shape[0]} rows)")
    print(f"Saved: {teams_fp}")


if __name__ == "__main__":
    main()