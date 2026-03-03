import requests
import pandas as pd

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"


def fetch_scoreboard(date):
    url = f"{BASE_URL}?dates={date}"
    res = requests.get(url)
    data = res.json()
    return data["events"]


def parse_games(events):
    games = []

    for e in events:
        comp = e["competitions"][0]
        teams = comp["competitors"]

        home = [t for t in teams if t["homeAway"] == "home"][0]
        away = [t for t in teams if t["homeAway"] == "away"][0]

        games.append({
            "date": e["date"],
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_score": home.get("score", 0),
            "away_score": away.get("score", 0),
            "status": comp["status"]["type"]["description"]
        })

    return pd.DataFrame(games)


def get_season_games(start_date, end_date):
    dates = pd.date_range(start_date, end_date)
    all_games = []

    for d in dates:
        date_str = d.strftime("%Y%m%d")
        try:
            events = fetch_scoreboard(date_str)
            df = parse_games(events)
            all_games.append(df)
        except:
            continue

    return pd.concat(all_games, ignore_index=True)


if __name__ == "__main__":
    df = get_season_games("20251101", "20260301")  # today's date
    print(df.head())  # 👈 add this line
    df.to_csv("data/processed/current_season_games.csv", index=False)
    print("Saved current season games!")