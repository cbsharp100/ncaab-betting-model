import argparse
import os
import sys
import joblib
import pandas as pd
from pricing import prob_to_moneyline, rating_to_spread, expected_value

def load_model(path="model.joblib"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")
    return joblib.load(path)


def predict_probs(model, X):
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
    else:
        preds = model.predict(X)
        probs = preds  # assume model.predict already returns probabilities
    return probs


def backtest_dataframe(model, games_df, sportsbook_col="sportsbook_ml"):
    X = games_df[["team_rating_diff", "home"]]
    probs = predict_probs(model, X)
    games_df = games_df.copy()
    games_df["win_prob"] = probs
    games_df["fair_moneyline"] = games_df["win_prob"].apply(prob_to_moneyline)
    games_df["est_spread"] = games_df["team_rating_diff"].apply(rating_to_spread)
    if sportsbook_col in games_df.columns:
        games_df["ev"] = games_df.apply(
            lambda r: expected_value(r["win_prob"], r[sportsbook_col]), axis=1
        )
    return games_df


def example_dataframe():
    return pd.DataFrame({"team_rating_diff": [5], "home": [1], "sportsbook_ml": [-150]})


def main():
    parser = argparse.ArgumentParser(description="Backtest model on games CSV or run example.")
    parser.add_argument("--model", default="model.joblib", help="Path to trained model (joblib).")
    parser.add_argument("--csv", help="CSV file with columns team_rating_diff, home, optional sportsbook_ml.")
    parser.add_argument("--out", help="Optional output CSV to write results.")
    args = parser.parse_args()

    model = load_model(args.model)

    if args.csv:
        games = pd.read_csv(args.csv)
    else:
        games = example_dataframe()

    results = backtest_dataframe(model, games)

    pd.set_option("display.width", 120)
    print(results.head().to_string(index=False))

    if args.out:
        results.to_csv(args.out, index=False)


if __name__ == "__main__":
    main()