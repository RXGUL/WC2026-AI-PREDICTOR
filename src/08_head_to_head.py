from itertools import combinations
from pathlib import Path
import sys

import pandas as pd

from constants import ALL_TEAMS


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MATCHES_PATH = PROJECT_ROOT / "data" / "processed" / "matches_clean.csv"
H2H_STATS_PATH = PROJECT_ROOT / "data" / "processed" / "h2h_stats.csv"

REQUIRED_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "result",
    "tournament",
]


def load_matches() -> pd.DataFrame:
    matches = pd.read_csv(MATCHES_PATH)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in matches.columns]
    if missing_columns:
        raise ValueError(f"{MATCHES_PATH} is missing columns: {missing_columns}")

    matches = matches[REQUIRED_COLUMNS].copy()
    matches["date"] = pd.to_datetime(matches["date"], errors="raise")
    matches = matches.sort_values("date", ascending=True, kind="mergesort").reset_index(drop=True)
    return matches


def team_result(match: pd.Series, team: str) -> str:
    if match["result"] == "D":
        return "D"

    if match["home_team"] == team:
        return "W" if match["result"] == "H" else "L"
    return "W" if match["result"] == "A" else "L"


def goals_for(match: pd.Series, team: str) -> float:
    if match["home_team"] == team:
        return float(match["home_score"])
    return float(match["away_score"])


def calculate_pair_stats(matches: pd.DataFrame, team_a: str, team_b: str) -> dict:
    h2h_matches = matches[
        ((matches["home_team"] == team_a) & (matches["away_team"] == team_b))
        | ((matches["home_team"] == team_b) & (matches["away_team"] == team_a))
    ].copy()

    total_matches = len(h2h_matches)
    if total_matches == 0:
        return {
            "team_a": team_a,
            "team_b": team_b,
            "h2h_matches": 0,
            "team_a_win_rate": 0.5,
            "avg_goals_a": 0.0,
            "avg_goals_b": 0.0,
            "last_5_a_wins": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "draws": 0,
        }

    team_a_results = h2h_matches.apply(lambda match: team_result(match, team_a), axis=1)
    team_a_wins = int((team_a_results == "W").sum())
    team_b_wins = int((team_a_results == "L").sum())
    draws = int((team_a_results == "D").sum())

    last_5 = h2h_matches.tail(5)
    last_5_a_wins = int(
        last_5.apply(lambda match: team_result(match, team_a), axis=1).eq("W").sum()
    )

    return {
        "team_a": team_a,
        "team_b": team_b,
        "h2h_matches": total_matches,
        "team_a_win_rate": round(team_a_wins / total_matches, 3),
        "avg_goals_a": round(h2h_matches.apply(lambda match: goals_for(match, team_a), axis=1).mean(), 2),
        "avg_goals_b": round(h2h_matches.apply(lambda match: goals_for(match, team_b), axis=1).mean(), 2),
        "last_5_a_wins": last_5_a_wins,
        "team_a_wins": team_a_wins,
        "team_b_wins": team_b_wins,
        "draws": draws,
    }


def build_h2h_lookup(matches: pd.DataFrame) -> dict[frozenset, dict]:
    h2h_lookup = {}

    for team_a, team_b in combinations(ALL_TEAMS, 2):
        stats = calculate_pair_stats(matches, team_a, team_b)
        h2h_lookup[frozenset({team_a, team_b})] = stats

    return h2h_lookup


def flat_stats(h2h_lookup: dict[frozenset, dict]) -> pd.DataFrame:
    rows = [
        {
            "team_a": stats["team_a"],
            "team_b": stats["team_b"],
            "h2h_matches": stats["h2h_matches"],
            "team_a_win_rate": stats["team_a_win_rate"],
            "avg_goals_a": stats["avg_goals_a"],
            "avg_goals_b": stats["avg_goals_b"],
            "last_5_a_wins": stats["last_5_a_wins"],
        }
        for stats in h2h_lookup.values()
        if stats["h2h_matches"] >= 1
    ]

    return pd.DataFrame(
        rows,
        columns=[
            "team_a",
            "team_b",
            "h2h_matches",
            "team_a_win_rate",
            "avg_goals_a",
            "avg_goals_b",
            "last_5_a_wins",
        ],
    ).sort_values(["h2h_matches", "team_a", "team_b"], ascending=[False, True, True])


def print_most_played_rivalries(stats_df: pd.DataFrame) -> None:
    print("\n10 most played WC2026-team rivalries")
    print("-" * 83)
    print(f"{'Pair':<42} {'Matches':>7} {'Team A WR':>9} {'Avg A':>7} {'Avg B':>7}")
    print("-" * 83)

    for row in stats_df.head(10).itertuples(index=False):
        pair = f"{row.team_a} vs {row.team_b}"
        print(
            f"{pair:<42} {row.h2h_matches:>7} {row.team_a_win_rate:>9.3f} "
            f"{row.avg_goals_a:>7.2f} {row.avg_goals_b:>7.2f}"
        )


def print_specific_record(h2h_lookup: dict[frozenset, dict], team_a: str, team_b: str, label: str) -> None:
    stats = h2h_lookup[frozenset({team_a, team_b})]

    if stats["team_a"] != team_a:
        stats = calculate_pair_stats(load_matches(), team_a, team_b)

    print(
        f"{label:<24} {stats['h2h_matches']:>3} matches | "
        f"{team_a}: {stats['team_a_wins']:>2} wins "
        f"({stats['team_a_win_rate']:.3f}) | "
        f"{team_b}: {stats['team_b_wins']:>2} wins | "
        f"Draws: {stats['draws']:>2} | "
        f"Avg goals: {stats['avg_goals_a']:.2f}-{stats['avg_goals_b']:.2f} | "
        f"Last 5 {team_a} wins: {stats['last_5_a_wins']}"
    )


def print_specific_records(h2h_lookup: dict[frozenset, dict]) -> None:
    print("\nSelected H2H records")
    print("-" * 122)
    print_specific_record(h2h_lookup, "Brazil", "Argentina", "Brazil vs Argentina")
    print_specific_record(h2h_lookup, "Germany", "England", "Germany vs England")
    print_specific_record(h2h_lookup, "France", "Spain", "France vs Spain")
    print_specific_record(h2h_lookup, "United States", "Mexico", "USA vs Mexico")


def main() -> None:
    matches = load_matches()
    h2h_lookup = build_h2h_lookup(matches)
    stats_df = flat_stats(h2h_lookup)

    H2H_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    stats_df.to_csv(H2H_STATS_PATH, index=False)

    print(f"Saved {H2H_STATS_PATH}")
    print_most_played_rivalries(stats_df)
    print_specific_records(h2h_lookup)


if __name__ == "__main__":
    main()
