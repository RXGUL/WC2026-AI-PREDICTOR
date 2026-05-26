from datetime import date
from pathlib import Path
import sys

import pandas as pd

from constants import ALL_TEAMS


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "matches_clean.csv"
TEAM_FORM_PATH = PROJECT_ROOT / "data" / "processed" / "team_form.csv"

REQUIRED_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "result",
    "tournament",
]

RESULT_POINTS = {
    "W": 3,
    "D": 1,
    "L": 0,
}


def load_matches() -> pd.DataFrame:
    matches = pd.read_csv(MATCHES_PATH)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in matches.columns]
    if missing_columns:
        raise ValueError(f"{MATCHES_PATH} is missing columns: {missing_columns}")

    matches = matches[REQUIRED_COLUMNS].copy()
    matches["date"] = pd.to_datetime(matches["date"], errors="raise")
    matches = matches.sort_values("date", ascending=True, kind="mergesort").reset_index(drop=True)
    return matches


def result_for_team(match: pd.Series, team: str) -> str:
    if match["result"] == "D":
        return "D"

    is_home_team = match["home_team"] == team
    if (is_home_team and match["result"] == "H") or (not is_home_team and match["result"] == "A"):
        return "W"
    return "L"


def team_match_rows(matches: pd.DataFrame, team: str, cutoff_date: pd.Timestamp) -> list[dict]:
    team_matches = matches[
        ((matches["home_team"] == team) | (matches["away_team"] == team))
        & (matches["date"] <= cutoff_date)
    ].tail(10)

    rows = []
    for _, match in team_matches.iterrows():
        is_home_team = match["home_team"] == team
        goals_for = match["home_score"] if is_home_team else match["away_score"]
        goals_against = match["away_score"] if is_home_team else match["home_score"]

        rows.append(
            {
                "date": match["date"],
                "result": result_for_team(match, team),
                "goals_for": float(goals_for),
                "goals_against": float(goals_against),
            }
        )

    return rows


def linear_weights(match_count: int) -> list[float]:
    ten_match_weights = [0.6 + (0.4 * index / 9) for index in range(10)]
    return ten_match_weights[-match_count:]


def current_win_streak(rows: list[dict]) -> int:
    streak = 0
    for row in reversed(rows):
        if row["result"] != "W":
            break
        streak += 1
    return streak


def calculate_team_form(matches: pd.DataFrame, team: str, cutoff_date: pd.Timestamp) -> dict:
    rows = team_match_rows(matches, team, cutoff_date)
    matches_used = len(rows)

    goals_scored_avg = sum(row["goals_for"] for row in rows) / matches_used if rows else 0.0
    goals_conceded_avg = sum(row["goals_against"] for row in rows) / matches_used if rows else 0.0
    clean_sheets = sum(1 for row in rows if row["goals_against"] == 0)
    win_streak = current_win_streak(rows)

    if matches_used < 3:
        form_score = 50.0
    else:
        weights = linear_weights(matches_used)
        weighted_points = sum(
            RESULT_POINTS[row["result"]] * weight for row, weight in zip(rows, weights)
        )
        max_possible_weighted_points = sum(3 * weight for weight in weights)
        form_score = (weighted_points / max_possible_weighted_points) * 100

    return {
        "team": team,
        "form_score": round(form_score, 2),
        "goals_scored_avg": round(goals_scored_avg, 2),
        "goals_conceded_avg": round(goals_conceded_avg, 2),
        "clean_sheets": clean_sheets,
        "win_streak": win_streak,
        "matches_used": matches_used,
    }


def print_ranked_table(team_form: pd.DataFrame) -> None:
    print("\nCurrent form rankings")
    print("-" * 93)
    print(
        f"{'Rank':>4}  {'Team':<24} {'Form':>7} {'GF Avg':>7} {'GA Avg':>7} "
        f"{'CS':>4} {'Streak':>7} {'Used':>5}"
    )
    print("-" * 93)

    for rank, row in enumerate(team_form.itertuples(index=False), start=1):
        print(
            f"{rank:>4}  {row.team:<24} {row.form_score:>7.2f} "
            f"{row.goals_scored_avg:>7.2f} {row.goals_conceded_avg:>7.2f} "
            f"{row.clean_sheets:>4} {row.win_streak:>7} {row.matches_used:>5}"
        )


def main() -> None:
    matches = load_matches()
    cutoff_date = pd.Timestamp(date.today())

    rows = [calculate_team_form(matches, team, cutoff_date) for team in ALL_TEAMS]
    team_form = pd.DataFrame(
        rows,
        columns=[
            "team",
            "form_score",
            "goals_scored_avg",
            "goals_conceded_avg",
            "clean_sheets",
            "win_streak",
            "matches_used",
        ],
    ).sort_values(["form_score", "team"], ascending=[False, True])

    TEAM_FORM_PATH.parent.mkdir(parents=True, exist_ok=True)
    team_form.to_csv(TEAM_FORM_PATH, index=False)

    print(f"Saved {TEAM_FORM_PATH}")
    print_ranked_table(team_form)


if __name__ == "__main__":
    main()
