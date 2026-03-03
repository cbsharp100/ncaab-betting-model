import pandas as pd
from src.pricing import prob_to_moneyline, rating_to_spread, expected_value

HCA_ELO = 75  # home-court advantage in Elo points


def elo_to_prob(diff_elo: float) -> float:
    # Standard Elo win prob
    return 1.0 / (1.0 + 10 ** (-diff_elo / 400.0))

def find_team_name(user_input: str, team_list):
    user_input = user_input.lower().strip()

    # exact match first
    for team in team_list:
        if team.lower() == user_input:
            return team

    # partial match (contains)
    matches = [team for team in team_list if user_input in team.lower()]

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        print("\nMultiple matches found:")
        for i, m in enumerate(matches):
            print(f"{i+1}. {m}")
        choice = int(input("Select team number: "))
        return matches[choice - 1]

    raise ValueError(f"No team found matching '{user_input}'")

def predict_game(home_team: str, away_team: str):
    ratings = pd.read_csv("data/processed/team_ratings_net.csv")

    team_list = ratings["team"].tolist()

    # convert user input into correct full team names
    home_team = find_team_name(home_team, team_list)
    away_team = find_team_name(away_team, team_list)

    # Pull Elo ratings
    r_home = float(ratings.loc[ratings["team"] == home_team, "elo_final"].values[0])
    r_away = float(ratings.loc[ratings["team"] == away_team, "elo_final"].values[0])

    # Apply home-court advantage
    diff = (r_home - r_away) + HCA_ELO

    # Model win probs
    p_home = elo_to_prob(diff)
    p_away = 1.0 - p_home

    # Fair moneylines from model
    fair_ml_home = prob_to_moneyline(p_home)
    fair_ml_away = prob_to_moneyline(p_away)

    # Spread estimate
    spread_home = rating_to_spread(diff)

    # Print prediction summary
    print("\n🏀 GAME PREDICTION")
    print(f"{home_team} vs {away_team}")
    print("----------------------------")
    print(f"Home Elo: {r_home:.1f}")
    print(f"Away Elo: {r_away:.1f}")
    print(f"Elo diff (w/ HCA): {diff:.1f}")
    print(f"P(home win): {p_home:.3f}")
    print(f"Fair ML (home): {fair_ml_home}")
    print(f"Fair ML (away): {fair_ml_away}")
    print(f"Estimated Spread (home): {spread_home:.1f}\n")

    # --- Sportsbook input (both sides) ---
    book_ml_home = int(input("Sportsbook moneyline for HOME team (e.g., +200 or -150): ").strip())
    book_ml_away = int(input("Sportsbook moneyline for AWAY team (e.g., +200 or -150): ").strip())

    # --- EV calculations ---
    ev_home = expected_value(p_home, book_ml_home, stake=1.0)
    ev_away = expected_value(p_away, book_ml_away, stake=1.0)

    print("\n📈 EXPECTED VALUE (per $1 risked)")
    print(f"EV betting HOME ({home_team}) at {book_ml_home}: {ev_home:.3f}")
    print(f"EV betting AWAY ({away_team}) at {book_ml_away}: {ev_away:.3f}")

    # Suggest best side
    best_side = "HOME" if ev_home > ev_away else "AWAY"
    best_ev = ev_home if best_side == "HOME" else ev_away

    if best_ev > 0:
        print(f"\n✅ +EV side: {best_side} (EV={best_ev:.3f})")
    else:
        print("\n⚠️ No +EV bet based on your model vs these lines.")


if __name__ == "__main__":
    home = input("Home team (e.g., Indiana Hoosiers): ").strip()
    away = input("Away team (e.g., Northwestern Wildcats): ").strip()
    predict_game(home, away)