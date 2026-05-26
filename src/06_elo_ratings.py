from pathlib import Path
import sys

import pandas as pd

from constants import ALL_TEAMS


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


BASE_ELO = 1500.0
WORLD_CUP_K = 40
QUALIFIER_K = 30
FRIENDLY_K = 20

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "matches_clean.csv"
RAW_RESULTS_PATH = PROJECT_ROOT / "data" / "raw" / "results.csv"
ELO_RATINGS_PATH = PROJECT_ROOT / "data" / "processed" / "elo_ratings.csv"
ELO_HISTORY_PATH = PROJECT_ROOT / "data" / "processed" / "elo_history.csv"

REQUIRED_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "result",
    "tournament",
]


def expected_score(team_elo: float, opponent_elo: float) -> float:
    return 1 / (1 + 10 ** ((opponent_elo - team_elo) / 400))


def k_factor(tournament: str) -> int:
    tournament_name = str(tournament).strip().lower()

    if "world cup" in tournament_name and "qualification" not in tournament_name:
        return WORLD_CUP_K
    if "qualifier" in tournament_name or "qualification" in tournament_name:
        return QUALIFIER_K
    return FRIENDLY_K


def actual_scores(result: str) -> tuple[float, float]:
    if result == "H":
        return 1.0, 0.0
    if result == "A":
        return 0.0, 1.0
    if result == "D":
        return 0.5, 0.5
    raise ValueError(f"Unexpected result value: {result}")


def ensure_matches_clean_exists() -> None:
    if MATCHES_PATH.exists():
        return

    if not RAW_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Missing {MATCHES_PATH} and could not build it because {RAW_RESULTS_PATH} was not found."
        )

    raw_matches = pd.read_csv(RAW_RESULTS_PATH)
    raw_matches["result"] = raw_matches.apply(match_result, axis=1)
    clean_matches = raw_matches[REQUIRED_COLUMNS].copy()
    MATCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_matches.to_csv(MATCHES_PATH, index=False)
    print(f"Created {MATCHES_PATH}")


def match_result(match: pd.Series) -> str:
    if match["home_score"] > match["away_score"]:
        return "H"
    if match["home_score"] < match["away_score"]:
        return "A"
    return "D"


def load_matches() -> pd.DataFrame:
    ensure_matches_clean_exists()

    matches = pd.read_csv(MATCHES_PATH)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in matches.columns]
    if missing_columns:
        raise ValueError(f"{MATCHES_PATH} is missing columns: {missing_columns}")

    matches = matches[REQUIRED_COLUMNS].copy()
    matches["date"] = pd.to_datetime(matches["date"], errors="raise")
    matches = matches.sort_values("date", ascending=True, kind="mergesort").reset_index(drop=True)
    return matches


def calculate_elo(matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tracked_teams = list(ALL_TEAMS)
    ratings = {team: BASE_ELO for team in tracked_teams}
    matches_played = {team: 0 for team in tracked_teams}
    history = []

    for match in matches.itertuples(index=False):
        home_team = match.home_team
        away_team = match.away_team

        ratings.setdefault(home_team, BASE_ELO)
        ratings.setdefault(away_team, BASE_ELO)

        home_elo = ratings[home_team]
        away_elo = ratings[away_team]
        home_actual, away_actual = actual_scores(match.result)
        k = k_factor(match.tournament)

        ratings[home_team] = home_elo + k * (home_actual - expected_score(home_elo, away_elo))
        ratings[away_team] = away_elo + k * (away_actual - expected_score(away_elo, home_elo))

        if home_team in matches_played:
            matches_played[home_team] += 1
        if away_team in matches_played:
            matches_played[away_team] += 1

        match_date = match.date.date().isoformat()
        for team in tracked_teams:
            history.append(
                {
                    "date": match_date,
                    "team": team,
                    "elo": round(ratings[team], 2),
                }
            )

    final_ratings = pd.DataFrame(
        [
            {
                "team": team,
                "elo": round(ratings[team], 2),
                "matches_played": matches_played[team],
            }
            for team in tracked_teams
        ]
    ).sort_values(["elo", "team"], ascending=[False, True])

    history_df = pd.DataFrame(history, columns=["date", "team", "elo"])
    return final_ratings, history_df


def print_top_15(final_ratings: pd.DataFrame) -> None:
    top_15 = final_ratings.head(15).copy()
    min_elo = top_15["elo"].min()
    max_elo = top_15["elo"].max()
    span = max(max_elo - min_elo, 1)

    print("\nTop 15 teams by final ELO")
    print("-" * 48)
    for rank, row in enumerate(top_15.itertuples(index=False), start=1):
        bar_length = 8 + round(((row.elo - min_elo) / span) * 32)
        bar = "█" * bar_length
        print(f"{rank:>2}. {row.team:<24} {row.elo:>7.2f} {bar}")


def main() -> None:
    matches = load_matches()
    final_ratings, history = calculate_elo(matches)

    ELO_RATINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_ratings.to_csv(ELO_RATINGS_PATH, index=False)
    history.to_csv(ELO_HISTORY_PATH, index=False)

    print(f"Saved {ELO_RATINGS_PATH}")
    print(f"Saved {ELO_HISTORY_PATH}")
    print_top_15(final_ratings)


if __name__ == "__main__":
    main()
