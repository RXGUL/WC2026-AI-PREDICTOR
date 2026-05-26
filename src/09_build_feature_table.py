from collections import defaultdict
from pathlib import Path
import sys

import pandas as pd

from constants import ALL_TEAMS


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MATCHES_PATH = PROCESSED_DIR / "matches_clean.csv"
ELO_RATINGS_PATH = PROCESSED_DIR / "elo_ratings.csv"
ELO_HISTORY_PATH = PROCESSED_DIR / "elo_history.csv"
TEAM_FORM_PATH = PROCESSED_DIR / "team_form.csv"
H2H_STATS_PATH = PROCESSED_DIR / "h2h_stats.csv"
MASTER_TEAMS_PATH = PROCESSED_DIR / "master_teams.csv"
FEATURES_PATH = PROCESSED_DIR / "features.csv"

BASE_ELO = 1500.0
FORM_DEFAULT = 50.0

MATCH_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "result",
    "tournament",
]

MASTER_COLUMNS = [
    "team",
    "group",
    "confederation",
    "is_host",
    "fifa_rank",
    "squad_value_m",
    "avg_ca",
    "composure",
    "determination",
    "avg_mentality",
    "avg_pace",
    "avg_stamina",
    "injury_proneness",
    "injured_count",
    "availability_score",
]

OUTPUT_COLUMNS = [
    "date",
    "home_team",
    "away_team",
    "tournament",
    "is_wc",
    "home_elo",
    "away_elo",
    "elo_diff",
    "home_form",
    "away_form",
    "form_diff",
    "home_goals_avg",
    "away_goals_avg",
    "h2h_rate",
    "h2h_matches",
    "composure_diff",
    "mentality_diff",
    "squad_value_ratio",
    "ca_diff",
    "pace_diff",
    "rank_diff",
    "is_host",
    "home_injured",
    "away_injured",
    "availability_diff",
    "is_wc_match",
    "result",
    "result_encoded",
]

IDENTIFIER_COLUMNS = ["date", "home_team", "away_team", "tournament", "is_wc"]
TARGET_COLUMNS = ["result", "result_encoded"]

RESULT_POINTS = {"W": 3, "D": 1, "L": 0}
RESULT_ENCODING = {"H": 2, "D": 1, "A": 0}


def load_required_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    data = pd.read_csv(path)
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"{path} is missing columns: {missing_columns}")
    return data


def load_matches() -> pd.DataFrame:
    matches = load_required_csv(MATCHES_PATH, MATCH_COLUMNS)

    if "is_wc" not in matches.columns:
        matches["is_wc"] = matches["tournament"].astype(str).str.contains(
            "World Cup", case=False, na=False
        ).astype(int)

    matches["date"] = pd.to_datetime(matches["date"], errors="raise")
    matches = matches.sort_values("date", ascending=True, kind="mergesort").reset_index(drop=True)
    return matches


def load_master_teams() -> tuple[pd.DataFrame, set[str]]:
    if MASTER_TEAMS_PATH.exists():
        master = load_required_csv(MASTER_TEAMS_PATH, MASTER_COLUMNS)
        missing_master_teams = set(ALL_TEAMS) - set(master["team"])
        return master, missing_master_teams

    print(f"Warning: {MASTER_TEAMS_PATH} not found. Using neutral static team defaults.")
    master = pd.DataFrame({"team": ALL_TEAMS})
    for column in MASTER_COLUMNS:
        if column not in master.columns:
            master[column] = pd.NA
    return master[MASTER_COLUMNS], set(ALL_TEAMS)


def team_result(match: pd.Series, team: str) -> str:
    if match["result"] == "D":
        return "D"

    if match["home_team"] == team:
        return "W" if match["result"] == "H" else "L"
    return "W" if match["result"] == "A" else "L"


def team_goals(match: pd.Series, team: str) -> tuple[float, float]:
    if match["home_team"] == team:
        return float(match["home_score"]), float(match["away_score"])
    return float(match["away_score"]), float(match["home_score"])


def form_from_history(history: list[dict]) -> dict:
    recent = history[-10:]
    matches_used = len(recent)

    goals_avg = sum(row["goals_for"] for row in recent) / matches_used if recent else 0.0

    if matches_used < 3:
        form_score = FORM_DEFAULT
    else:
        ten_match_weights = [0.6 + (0.4 * index / 9) for index in range(10)]
        weights = ten_match_weights[-matches_used:]
        weighted_points = sum(
            RESULT_POINTS[row["result"]] * weight for row, weight in zip(recent, weights)
        )
        max_possible = sum(3 * weight for weight in weights)
        form_score = (weighted_points / max_possible) * 100

    return {
        "form_score": form_score,
        "goals_avg": goals_avg,
    }


def make_pair_key(team_a: str, team_b: str) -> frozenset:
    return frozenset({team_a, team_b})


def h2h_for_home(h2h_lookup: dict[frozenset, dict], home_team: str, away_team: str) -> tuple[float, int]:
    stats = h2h_lookup.get(make_pair_key(home_team, away_team))
    if not stats or stats["matches"] == 0:
        return 0.5, 0

    home_wins = stats["wins"].get(home_team, 0)
    return home_wins / stats["matches"], stats["matches"]


def update_h2h(h2h_lookup: dict[frozenset, dict], match: pd.Series) -> None:
    home_team = match["home_team"]
    away_team = match["away_team"]
    key = make_pair_key(home_team, away_team)
    stats = h2h_lookup.setdefault(
        key,
        {
            "matches": 0,
            "wins": defaultdict(int),
        },
    )

    stats["matches"] += 1
    if match["result"] == "H":
        stats["wins"][home_team] += 1
    elif match["result"] == "A":
        stats["wins"][away_team] += 1


def latest_elo_before(
    elo_by_team: dict[str, pd.DataFrame], team: str, match_date: pd.Timestamp
) -> float:
    team_history = elo_by_team.get(team)
    if team_history is None or team_history.empty:
        return BASE_ELO

    dates = team_history["date"]
    position = dates.searchsorted(match_date, side="left") - 1
    if position < 0:
        return BASE_ELO
    return float(team_history.iloc[position]["elo"])


def build_elo_lookup(elo_history: pd.DataFrame) -> dict[str, pd.DataFrame]:
    elo_history = elo_history.copy()
    elo_history["date"] = pd.to_datetime(elo_history["date"], errors="raise")
    elo_history = elo_history.sort_values(["team", "date"], kind="mergesort")
    return {
        team: team_history[["date", "elo"]].reset_index(drop=True)
        for team, team_history in elo_history.groupby("team")
    }


def static_features(master_lookup: dict[str, dict], home_team: str, away_team: str) -> dict:
    home = master_lookup.get(home_team, {})
    away = master_lookup.get(away_team, {})

    return {
        "composure_diff": pd.to_numeric(home.get("composure"), errors="coerce")
        - pd.to_numeric(away.get("composure"), errors="coerce"),
        "mentality_diff": pd.to_numeric(home.get("avg_mentality"), errors="coerce")
        - pd.to_numeric(away.get("avg_mentality"), errors="coerce"),
        "squad_value_ratio": pd.to_numeric(home.get("squad_value_m"), errors="coerce")
        / (pd.to_numeric(away.get("squad_value_m"), errors="coerce") + 1),
        "ca_diff": pd.to_numeric(home.get("avg_ca"), errors="coerce")
        - pd.to_numeric(away.get("avg_ca"), errors="coerce"),
        "pace_diff": pd.to_numeric(home.get("avg_pace"), errors="coerce")
        - pd.to_numeric(away.get("avg_pace"), errors="coerce"),
        "rank_diff": pd.to_numeric(away.get("fifa_rank"), errors="coerce")
        - pd.to_numeric(home.get("fifa_rank"), errors="coerce"),
        "is_host": int(pd.to_numeric(home.get("is_host"), errors="coerce") == 1),
        "home_injured": pd.to_numeric(home.get("injured_count"), errors="coerce"),
        "away_injured": pd.to_numeric(away.get("injured_count"), errors="coerce"),
        "availability_diff": pd.to_numeric(home.get("availability_score"), errors="coerce")
        - pd.to_numeric(away.get("availability_score"), errors="coerce"),
    }


def add_team_history(team_histories: dict[str, list[dict]], match: pd.Series) -> None:
    for team in (match["home_team"], match["away_team"]):
        if team not in ALL_TEAMS:
            continue

        goals_for, goals_against = team_goals(match, team)
        team_histories[team].append(
            {
                "result": team_result(match, team),
                "goals_for": goals_for,
                "goals_against": goals_against,
            }
        )


def build_features(
    matches: pd.DataFrame,
    elo_by_team: dict[str, pd.DataFrame],
    master: pd.DataFrame,
) -> pd.DataFrame:
    all_teams = set(ALL_TEAMS)
    master_lookup = master.set_index("team").to_dict(orient="index")
    team_histories = {team: [] for team in ALL_TEAMS}
    h2h_lookup = {}
    rows = []

    for _, match in matches.iterrows():
        home_team = match["home_team"]
        away_team = match["away_team"]
        include_match = home_team in all_teams and away_team in all_teams

        if include_match:
            home_elo = latest_elo_before(elo_by_team, home_team, match["date"])
            away_elo = latest_elo_before(elo_by_team, away_team, match["date"])
            home_form = form_from_history(team_histories[home_team])
            away_form = form_from_history(team_histories[away_team])
            h2h_rate, h2h_matches = h2h_for_home(h2h_lookup, home_team, away_team)
            static = static_features(master_lookup, home_team, away_team)
            is_wc_match = int("world cup" in str(match["tournament"]).lower())

            rows.append(
                {
                    "date": match["date"].date().isoformat(),
                    "home_team": home_team,
                    "away_team": away_team,
                    "tournament": match["tournament"],
                    "is_wc": int(match["is_wc"]),
                    "home_elo": home_elo,
                    "away_elo": away_elo,
                    "elo_diff": home_elo - away_elo,
                    "home_form": home_form["form_score"],
                    "away_form": away_form["form_score"],
                    "form_diff": home_form["form_score"] - away_form["form_score"],
                    "home_goals_avg": home_form["goals_avg"],
                    "away_goals_avg": away_form["goals_avg"],
                    "h2h_rate": h2h_rate,
                    "h2h_matches": h2h_matches,
                    **static,
                    "is_wc_match": is_wc_match,
                    "result": match["result"],
                    "result_encoded": RESULT_ENCODING[match["result"]],
                }
            )

        if home_team in all_teams or away_team in all_teams:
            add_team_history(team_histories, match)
        if home_team in all_teams and away_team in all_teams:
            update_h2h(h2h_lookup, match)

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def missing_value_flags(features: pd.DataFrame, missing_master_teams: set[str]) -> pd.DataFrame:
    feature_columns = [
        column
        for column in features.columns
        if column not in IDENTIFIER_COLUMNS and column not in TARGET_COLUMNS
    ]
    flags = []

    for team in ALL_TEAMS:
        team_rows = features[(features["home_team"] == team) | (features["away_team"] == team)]
        if team_rows.empty:
            continue

        missing_cells = team_rows[feature_columns].isna().sum().sum()
        total_cells = len(team_rows) * len(feature_columns)
        missing_pct = (missing_cells / total_cells) * 100 if total_cells else 0

        if team in missing_master_teams:
            missing_pct = max(missing_pct, 100.0)

        if missing_pct > 20:
            flags.append(
                {
                    "team": team,
                    "rows": len(team_rows),
                    "missing_pct": round(missing_pct, 2),
                }
            )

    return pd.DataFrame(flags, columns=["team", "rows", "missing_pct"])


def print_summary(features: pd.DataFrame, missing_flags: pd.DataFrame) -> None:
    feature_columns = [
        column
        for column in features.columns
        if column not in IDENTIFIER_COLUMNS and column not in TARGET_COLUMNS
    ]

    print("\nFeature table summary")
    print("-" * 80)
    print(f"Total rows: {len(features)}")
    print(f"Feature columns count: {len(feature_columns)}")

    print("\nResult distribution")
    distribution = features["result"].value_counts().reindex(["H", "D", "A"], fill_value=0)
    for result, count in distribution.items():
        pct = (count / len(features)) * 100 if len(features) else 0
        print(f"{result}: {count} ({pct:.1f}%)")

    print("\nTop 5 rows preview")
    print(features.head(5).to_string(index=False))

    print("\nTeams with more than 20% missing values")
    if missing_flags.empty:
        print("None")
    else:
        print(missing_flags.to_string(index=False))


def main() -> None:
    matches = load_matches()
    load_required_csv(ELO_RATINGS_PATH, ["team", "elo", "matches_played"])
    elo_history = load_required_csv(ELO_HISTORY_PATH, ["date", "team", "elo"])
    load_required_csv(
        TEAM_FORM_PATH,
        ["team", "form_score", "goals_scored_avg", "goals_conceded_avg", "clean_sheets", "win_streak"],
    )
    load_required_csv(
        H2H_STATS_PATH,
        ["team_a", "team_b", "h2h_matches", "team_a_win_rate", "avg_goals_a", "avg_goals_b"],
    )
    master, missing_master_teams = load_master_teams()

    elo_by_team = build_elo_lookup(elo_history)
    features = build_features(matches, elo_by_team, master)
    missing_flags = missing_value_flags(features, missing_master_teams)

    features = features.fillna(0)
    features.to_csv(FEATURES_PATH, index=False)

    print(f"Saved {FEATURES_PATH}")
    print_summary(features, missing_flags)


if __name__ == "__main__":
    main()
