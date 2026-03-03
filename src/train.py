import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

#!/usr/bin/env python3


def load_data(path: Path):
    if path is None:
        # small fake sample (replace by passing --data)
        return pd.DataFrame({
            "team_rating_diff": [5, -3, 8, 2, -6, 10, -4, 1],
            "home": [1, 0, 1, 1, 0, 1, 0, 1],
            "won": [1, 0, 1, 1, 0, 1, 0, 1]
        })
    df = pd.read_csv(path)
    return df

def main():
    p = argparse.ArgumentParser(description="Train a simple logistic regression win-probability model")
    p.add_argument("--data", type=Path, default=None, help="CSV file with columns: team_rating_diff, home, won")
    p.add_argument("--model-out", type=Path, default=Path("model.joblib"), help="Path to save trained model")
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--random-state", type=int, default=42)
    args = p.parse_args()

    df = load_data(args.data)
    X = df[["team_rating_diff", "home"]]
    y = df["won"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y if len(np.unique(y)) > 1 else None
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(solver="liblinear", random_state=args.random_state))
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    # compute ROC AUC only if both classes present in test set
    try:
        proba = pipeline.predict_proba(X_test)[:, 1]
        roc = roc_auc_score(y_test, proba)
    except Exception:
        roc = None

    joblib.dump(pipeline, args.model_out)

    print(f"saved_model: {args.model_out}")
    print(f"accuracy: {acc:.4f}")
    if roc is not None:
        print(f"roc_auc: {roc:.4f}")

if __name__ == "__main__":
    main()