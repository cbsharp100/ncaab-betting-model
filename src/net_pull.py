import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

NET_URL = "https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings"


def _clean_team(name: str) -> str:
    name = re.sub(r"\s+", " ", str(name)).strip()
    return name


def pull_net_rankings(out_csv: str = "data/processed/net_rankings.csv") -> pd.DataFrame:
    """
    Scrape NCAA.com NET rankings table and save to CSV.

    Output columns include: rank, team, record, conf, etc (whatever NCAA provides).
    """
    resp = requests.get(
        NET_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp.raise_for_status()

    # ✅ Use built-in parser so you don't need lxml installed
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if table is None:
        raise RuntimeError(
            "Could not find NET table on the page. NCAA page structure may have changed."
        )

    df_list = pd.read_html(str(table))
    if not df_list:
        raise RuntimeError("Could not parse NET table with pandas.")

    df = df_list[0].copy()

    # Normalize column names
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # Map the school column to 'team'
    if "school" in df.columns:
        df.rename(columns={"school": "team"}, inplace=True)
    elif "rank_school" in df.columns:
        df.rename(columns={"rank_school": "team"}, inplace=True)

    if "rank" not in df.columns or "team" not in df.columns:
        raise RuntimeError(f"Unexpected NET columns: {df.columns.tolist()}")

    df["team"] = df["team"].map(_clean_team)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df.dropna(subset=["rank"]).copy()
    df["rank"] = df["rank"].astype(int)

    df = df.sort_values("rank").reset_index(drop=True)

    df.to_csv(out_csv, index=False)
    print(f"✅ Saved NET rankings to {out_csv} ({len(df)} teams)")
    return df


if __name__ == "__main__":
    pull_net_rankings()