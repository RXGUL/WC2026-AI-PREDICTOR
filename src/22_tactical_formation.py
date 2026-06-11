from __future__ import annotations

from itertools import combinations
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from constants import ALL_TEAMS, WC2026_GROUPS


FM25_CANDIDATE_PATHS = [
    PROJECT_ROOT / "data" / "fm25" / "fm25_players.csv.csv",
    PROJECT_ROOT / "data" / "fm25" / "fm25_players.csv",
]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
FEATURES_PATH = DATA_DIR / "features.csv"
TACTICAL_PROFILES_PATH = DATA_DIR / "tactical_profiles.csv"
TACTICAL_COLUMNS = [
    "home_formation_style",
    "away_formation_style",
    "tactical_matchup_score",
    "tactical_advantage",
]

FORMATION_SEARCH_TERMS = ("formation", "tactic", "style", "preferred", "manager", "system")
STYLE_ENCODING = {
    "balanced": 0,
    "high_press": 1,
    "possession": 2,
    "long_ball": 3,
}
MATCHUP_MATRIX = {
    ("high_press", "possession"): 0.55,
    ("high_press", "long_ball"): 0.45,
    ("high_press", "balanced"): 0.52,
    ("high_press", "high_press"): 0.50,
    ("possession", "long_ball"): 0.55,
    ("possession", "high_press"): 0.45,
    ("possession", "balanced"): 0.52,
    ("possession", "possession"): 0.50,
    ("long_ball", "high_press"): 0.55,
    ("long_ball", "possession"): 0.45,
    ("long_ball", "balanced"): 0.50,
    ("long_ball", "long_ball"): 0.50,
    ("balanced", "high_press"): 0.48,
    ("balanced", "possession"): 0.48,
    ("balanced", "long_ball"): 0.50,
    ("balanced", "balanced"): 0.50,
}

TEAM_ALIASES = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Czechia": "Czech Republic",
    "Curacao": "Curaçao",
    "CuraÃ§ao": "Curaçao",
    "CuraÃƒÂ§ao": "Curaçao",
    "CuraÃƒÆ’Ã‚Â§ao": "Curaçao",
}

# FM25 uses numeric NationID in this export. These IDs are anchored from known
# national-team players in the file and keep the aggregation lightweight.
TEAM_NATION_IDS = {
    "Algeria": [5],
    "Argentina": [1649],
    "Australia": [1435],
    "Austria": [755],
    "Belgium": [757],
    "Bosnia and Herzegovina": [759],
    "Brazil": [1651],
    "Canada": [364],
    "Cape Verde": [12],
    "Colombia": [1653],
    "Croatia": [761],
    "Curaçao": [375, 784],
    "Czech Republic": [763],
    "DR Congo": [53],
    "Ecuador": [1654],
    "Egypt": [16],
    "England": [765],
    "France": [769],
    "Germany": [771],
    "Ghana": [21],
    "Haiti": [375],
    "Iran": [114],
    "Iraq": [115],
    "Ivory Coast": [24],
    "Japan": [116],
    "Jordan": [118],
    "Mexico": [379],
    "Morocco": [34],
    "Netherlands": [784],
    "New Zealand": [1438],
    "Norway": [786],
    "Panama": [1657],
    "Paraguay": [1655],
    "Portugal": [788],
    "Qatar": [132],
    "Saudi Arabia": [133],
    "Scotland": [793],
    "Senegal": [41],
    "South Africa": [45],
    "South Korea": [135],
    "Spain": [796],
    "Sweden": [797],
    "Switzerland": [798],
    "Tunisia": [51],
    "Turkey": [799],
    "United States": [390],
    "Uruguay": [1656],
    "Uzbekistan": [144],
}


def canonical_team(team: object) -> str:
    value = str(team)
    return TEAM_ALIASES.get(value, value)


def fm25_path() -> Path:
    for path in FM25_CANDIDATE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Missing FM25 player file. Checked: "
        + ", ".join(str(path) for path in FM25_CANDIDATE_PATHS)
    )


def find_columns(columns: list[str], terms: tuple[str, ...]) -> list[str]:
    return [
        column
        for column in columns
        if any(term in column.lower() for term in terms)
    ]


def first_existing(columns: list[str], candidates: list[str]) -> str | None:
    by_lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    for column in columns:
        lower = column.lower()
        if any(candidate.lower() in lower for candidate in candidates):
            return column
    return None


def normalise(value: float, min_value: float = 1.0, max_value: float = 20.0) -> float:
    if pd.isna(value):
        return 0.5
    return max(0.0, min(1.0, (float(value) - min_value) / (max_value - min_value)))


def normalise_series(series: pd.Series) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce").fillna(series.mean())
    min_value = clean.min()
    max_value = clean.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(0.5, index=series.index)
    return (clean - min_value) / (max_value - min_value)


def formation_style(row: pd.Series) -> str:
    if row["pace_score"] > 0.7 and row["pressing_score"] > 0.7:
        return "high_press"
    if row["passing_score"] > 0.7 and row["strength_score"] < 0.4:
        return "possession"
    if row["strength_score"] > 0.7 and row["pace_score"] < 0.4:
        return "long_ball"
    return "balanced"


def load_fm_data() -> tuple[pd.DataFrame, list[str], str]:
    path = fm25_path()
    sample = pd.read_csv(path, nrows=5)
    columns = list(sample.columns)
    formation_columns = find_columns(columns, FORMATION_SEARCH_TERMS)
    nationality_column = first_existing(columns, ["Nationality", "Nation", "nat", "NationID"])
    if nationality_column is None:
        raise ValueError("Could not find nationality column in FM25 data")

    required_columns = {
        nationality_column,
        first_existing(columns, ["Pace", "Pac", "Acceleration", "Acc"]),
        first_existing(columns, ["Passing", "Pas"]),
        first_existing(columns, ["Workrate", "Work Rate", "Wor"]),
        first_existing(columns, ["Strength", "Str"]),
        first_existing(columns, ["Stamina", "Sta"]),
        first_existing(columns, ["Positioning"]),
        first_existing(columns, ["Jumping"]),
    }
    usecols = [column for column in required_columns if column]
    return pd.read_csv(path, usecols=usecols), formation_columns, nationality_column


def build_tactical_profiles() -> pd.DataFrame:
    players, formation_columns, nationality_column = load_fm_data()
    print("Formation-related columns found:")
    if formation_columns:
        for column in formation_columns:
            print(f"- {column}")
    else:
        print("- none; deriving tactical profile from player attributes")
    print(f"Nationality column: {nationality_column}")

    columns = list(players.columns)
    pace_col = first_existing(columns, ["Pace", "Pac", "Acceleration", "Acc"])
    passing_col = first_existing(columns, ["Passing", "Pas"])
    pressing_col = first_existing(columns, ["Workrate", "Work Rate", "Wor"])
    strength_col = first_existing(columns, ["Strength", "Str"])
    stamina_col = first_existing(columns, ["Stamina", "Sta"])
    positioning_col = first_existing(columns, ["Positioning"])
    jumping_col = first_existing(columns, ["Jumping"])

    global_defaults = {
        "avg_pace": players[pace_col].mean() if pace_col else 10.0,
        "avg_passing": players[passing_col].mean() if passing_col else 10.0,
        "avg_pressing": players[pressing_col].mean() if pressing_col else 10.0,
        "avg_strength": players[strength_col].mean() if strength_col else 10.0,
        "avg_stamina": players[stamina_col].mean() if stamina_col else 10.0,
    }

    rows = []
    for team in ALL_TEAMS:
        canonical = canonical_team(team)
        nation_ids = TEAM_NATION_IDS.get(canonical, [])
        if nationality_column == "NationID" and nation_ids:
            team_players = players[players[nationality_column].isin(nation_ids)].copy()
        else:
            team_players = players[
                players[nationality_column].astype(str).map(canonical_team) == canonical
            ].copy()

        if team_players.empty:
            avg_pace = global_defaults["avg_pace"]
            avg_passing = global_defaults["avg_passing"]
            avg_pressing = global_defaults["avg_pressing"]
            avg_strength = global_defaults["avg_strength"]
            avg_stamina = global_defaults["avg_stamina"]
            avg_positioning = avg_passing
            avg_jumping = avg_strength
        else:
            avg_pace = team_players[pace_col].mean() if pace_col else global_defaults["avg_pace"]
            avg_passing = team_players[passing_col].mean() if passing_col else global_defaults["avg_passing"]
            avg_pressing = team_players[pressing_col].mean() if pressing_col else global_defaults["avg_pressing"]
            avg_strength = team_players[strength_col].mean() if strength_col else global_defaults["avg_strength"]
            avg_stamina = team_players[stamina_col].mean() if stamina_col else global_defaults["avg_stamina"]
            avg_positioning = team_players[positioning_col].mean() if positioning_col else avg_passing
            avg_jumping = team_players[jumping_col].mean() if jumping_col else avg_strength

        rows.append(
            {
                "team": canonical,
                "avg_pace": round(float(avg_pace), 3),
                "avg_passing": round(float(avg_passing), 3),
                "avg_pressing": round(float(avg_pressing), 3),
                "avg_strength": round(float(avg_strength), 3),
                "avg_stamina": round(float(avg_stamina), 3),
                "_avg_positioning": float(avg_positioning),
                "_avg_jumping": float(avg_jumping),
            }
        )

    profiles = pd.DataFrame(rows)
    profiles["pace_score"] = normalise_series(profiles["avg_pace"])
    profiles["passing_score"] = normalise_series(
        (profiles["avg_passing"] + profiles["_avg_positioning"]) / 2
    )
    profiles["pressing_score"] = normalise_series(
        (profiles["avg_pressing"] + profiles["avg_stamina"]) / 2
    )
    profiles["strength_score"] = normalise_series(
        (profiles["avg_strength"] + profiles["_avg_jumping"]) / 2
    )
    profiles["formation_style"] = profiles.apply(formation_style, axis=1)
    profiles["tactical_score"] = profiles[
        ["pace_score", "passing_score", "pressing_score", "strength_score"]
    ].max(axis=1).round(6)

    return profiles[
        [
            "team",
            "formation_style",
            "avg_pace",
            "avg_passing",
            "avg_pressing",
            "avg_strength",
            "avg_stamina",
            "tactical_score",
        ]
    ].copy()


def merge_tactical_into_features(features: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    lookup = profiles[["team", "formation_style"]].copy()
    lookup["team_key"] = lookup["team"].map(canonical_team)

    base = features.drop(columns=[column for column in TACTICAL_COLUMNS if column in features.columns]).copy()
    base["home_team_key"] = base["home_team"].map(canonical_team)
    base["away_team_key"] = base["away_team"].map(canonical_team)

    home = lookup[["team_key", "formation_style"]].rename(
        columns={"team_key": "home_team_key", "formation_style": "home_style_name"}
    )
    away = lookup[["team_key", "formation_style"]].rename(
        columns={"team_key": "away_team_key", "formation_style": "away_style_name"}
    )

    merged = base.merge(home, on="home_team_key", how="left")
    merged = merged.merge(away, on="away_team_key", how="left")
    merged["home_style_name"] = merged["home_style_name"].fillna("balanced")
    merged["away_style_name"] = merged["away_style_name"].fillna("balanced")
    merged["home_formation_style"] = merged["home_style_name"].map(STYLE_ENCODING).fillna(0).astype(int)
    merged["away_formation_style"] = merged["away_style_name"].map(STYLE_ENCODING).fillna(0).astype(int)
    merged["tactical_matchup_score"] = [
        MATCHUP_MATRIX.get((home_style, away_style), 0.50)
        for home_style, away_style in zip(merged["home_style_name"], merged["away_style_name"])
    ]
    merged["tactical_advantage"] = merged["tactical_matchup_score"] - 0.5
    return merged.drop(columns=["home_team_key", "away_team_key", "home_style_name", "away_style_name"])


def print_profiles(profiles: pd.DataFrame) -> None:
    print("\nTeam | Style | Pace | Passing | Press | Strength")
    for row in profiles.sort_values("team").itertuples(index=False):
        print(
            f"{row.team:<24} | {row.formation_style:<10} | "
            f"{row.avg_pace:>5.2f} | {row.avg_passing:>7.2f} | "
            f"{row.avg_pressing:>5.2f} | {row.avg_strength:>8.2f}"
        )


def print_interesting_matchups(profiles: pd.DataFrame) -> None:
    style_by_team = profiles.set_index("team")["formation_style"].to_dict()
    spain_style = style_by_team.get("Spain", "balanced")
    germany_style = style_by_team.get("Germany", "balanced")
    spain_score = MATCHUP_MATRIX.get((spain_style, germany_style), 0.50)
    print(
        f"\nSpain ({spain_style}) vs Germany ({germany_style}): "
        f"Spain tactical advantage: {spain_score:.2f}"
    )

    matchups = []
    for teams in WC2026_GROUPS.values():
        canonical_teams = [canonical_team(team) for team in teams]
        for home_team, away_team in combinations(canonical_teams, 2):
            home_style = style_by_team.get(home_team, "balanced")
            away_style = style_by_team.get(away_team, "balanced")
            score = MATCHUP_MATRIX.get((home_style, away_style), 0.50)
            matchups.append(
                {
                    "home": home_team,
                    "away": away_team,
                    "home_style": home_style,
                    "away_style": away_style,
                    "score": score,
                    "imbalance": abs(score - 0.5),
                }
            )

    print("\nTop 5 most tactically imbalanced group stage matchups:")
    ranked = sorted(matchups, key=lambda row: row["imbalance"], reverse=True)
    for row in ranked[:5]:
        print(
            f"{row['home']} ({row['home_style']}) vs "
            f"{row['away']} ({row['away_style']}): {row['score']:.2f}"
        )


def main() -> None:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing feature table: {FEATURES_PATH}")

    profiles = build_tactical_profiles()
    profiles.to_csv(TACTICAL_PROFILES_PATH, index=False)
    print(f"\nSaved tactical profiles: {TACTICAL_PROFILES_PATH}")

    features = pd.read_csv(FEATURES_PATH)
    before_columns = len([column for column in features.columns if column not in TACTICAL_COLUMNS])
    updated = merge_tactical_into_features(features, profiles)
    after_columns = len(updated.columns)
    updated.to_csv(FEATURES_PATH, index=False)

    print_profiles(profiles)
    print_interesting_matchups(profiles)
    print(f"\nfeatures.csv: {before_columns} → {after_columns} columns (+4 tactical)")


if __name__ == "__main__":
    main()
