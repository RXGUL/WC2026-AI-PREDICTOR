from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from constants import WC2026_GROUPS


DATA_DIR = PROJECT_ROOT / "data" / "processed"
FEATURES_PATH = DATA_DIR / "features.csv"
CLIMATE_FEATURES_PATH = DATA_DIR / "climate_features.csv"
CLIMATE_FEATURE_COLUMNS = [
    "home_temp_disadvantage",
    "home_altitude_disadvantage",
    "home_humidity_factor",
    "home_climate_advantage",
    "away_temp_disadvantage",
    "away_altitude_disadvantage",
    "away_humidity_factor",
    "away_climate_advantage",
    "climate_advantage_diff",
]

VENUES = {
    "Atlanta": {"temp": 29, "altitude": 320, "humidity": 71, "country": "USA"},
    "Boston": {"temp": 22, "altitude": 9, "humidity": 65, "country": "USA"},
    "Dallas": {"temp": 35, "altitude": 139, "humidity": 58, "country": "USA"},
    "Guadalajara": {"temp": 24, "altitude": 1566, "humidity": 52, "country": "Mexico"},
    "Houston": {"temp": 33, "altitude": 15, "humidity": 78, "country": "USA"},
    "Kansas City": {"temp": 27, "altitude": 273, "humidity": 65, "country": "USA"},
    "Los Angeles": {"temp": 24, "altitude": 71, "humidity": 68, "country": "USA"},
    "Mexico City": {"temp": 19, "altitude": 2240, "humidity": 44, "country": "Mexico"},
    "Miami": {"temp": 31, "altitude": 2, "humidity": 79, "country": "USA"},
    "Monterrey": {"temp": 35, "altitude": 537, "humidity": 48, "country": "Mexico"},
    "New York": {"temp": 25, "altitude": 10, "humidity": 62, "country": "USA"},
    "Philadelphia": {"temp": 27, "altitude": 12, "humidity": 63, "country": "USA"},
    "San Francisco": {"temp": 16, "altitude": 16, "humidity": 79, "country": "USA"},
    "Seattle": {"temp": 18, "altitude": 53, "humidity": 66, "country": "USA"},
    "Toronto": {"temp": 22, "altitude": 76, "humidity": 64, "country": "Canada"},
    "Vancouver": {"temp": 18, "altitude": 70, "humidity": 71, "country": "Canada"},
}

HOME_TEMPS = {
    "France": 35,
    "Germany": 22,
    "England": 18,
    "Spain": 28,
    "Portugal": 26,
    "Netherlands": 20,
    "Belgium": 19,
    "Croatia": 28,
    "Brazil": 22,
    "Argentina": 16,
    "Uruguay": 14,
    "Colombia": 18,
    "Mexico": 26,
    "United States": 25,
    "Canada": 18,
    "Japan": 26,
    "South Korea": 24,
    "Australia": 14,
    "Morocco": 26,
    "Senegal": 33,
    "Egypt": 35,
    "Ivory Coast": 32,
    "Ghana": 30,
    "DR Congo": 28,
    "Algeria": 30,
    "Tunisia": 28,
    "South Africa": 16,
    "Cape Verde": 27,
    "Iran": 32,
    "Saudi Arabia": 38,
    "Iraq": 42,
    "Qatar": 40,
    "Jordan": 34,
    "Uzbekistan": 28,
    "Norway": 16,
    "Sweden": 20,
    "Scotland": 16,
    "Austria": 22,
    "Switzerland": 20,
    "Turkey": 28,
    "Czechia": 22,
    "Ecuador": 20,
    "Paraguay": 22,
    "Haiti": 30,
    "Panama": 30,
    "Curacao": 30,
    "New Zealand": 12,
    "Bosnia-Herzegovina": 22,
}

GROUP_VENUES = {
    "A": ["Guadalajara", "Mexico City"],
    "B": ["Toronto", "Vancouver"],
    "C": ["Dallas", "Houston"],
    "D": ["Los Angeles", "San Francisco"],
    "E": ["Atlanta", "Miami"],
    "F": ["New York", "Philadelphia"],
    "G": ["Kansas City", "Seattle"],
    "H": ["Dallas", "Houston"],
    "I": ["Los Angeles", "San Francisco"],
    "J": ["Miami", "Atlanta"],
    "K": ["Boston", "New York"],
    "L": ["Seattle", "Vancouver"],
}

TEAM_ALIASES = {
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Bosnia-Herzegovina": "Bosnia-Herzegovina",
    "Curacao": "Curacao",
    "Curaçao": "Curacao",
    "CuraÃ§ao": "Curacao",
    "CuraÃƒÂ§ao": "Curacao",
    "Czech Republic": "Czechia",
    "Czechia": "Czechia",
}

ALTITUDE_ADAPTED_TEAMS = {
    "Colombia",
    "Ecuador",
    "Mexico",
}


def canonical_team(team: object) -> str:
    value = str(team)
    return TEAM_ALIASES.get(value, value)


def primary_venue_for_team(group: str, team_index: int) -> str:
    venues = GROUP_VENUES[group]
    return venues[team_index % len(venues)]


def team_climate_rows() -> pd.DataFrame:
    rows = []
    raw_scores_by_team: dict[str, float] = {}

    for group, teams in WC2026_GROUPS.items():
        for team_index, team in enumerate(teams):
            canonical = canonical_team(team)
            venue_name = primary_venue_for_team(group, team_index)
            venue = VENUES[venue_name]
            home_temp = HOME_TEMPS.get(canonical, 24)
            temp_disadvantage = venue["temp"] - home_temp
            altitude_disadvantage = venue["altitude"] / 1000
            if canonical in ALTITUDE_ADAPTED_TEAMS:
                altitude_disadvantage *= 0.35
            humidity_factor = venue["humidity"] / 100
            raw_score = (
                -temp_disadvantage * 0.4
                - altitude_disadvantage * 0.3
                - humidity_factor * 0.3
            )
            raw_scores_by_team[canonical] = raw_score
            rows.append(
                {
                    "team": canonical,
                    "group": group,
                    "venue": venue_name,
                    "venue_temp": venue["temp"],
                    "home_temp": home_temp,
                    "temp_disadvantage": temp_disadvantage,
                    "altitude_disadvantage": altitude_disadvantage,
                    "humidity_factor": humidity_factor,
                    "raw_climate_score": raw_score,
                }
            )

    climate = pd.DataFrame(rows)
    group_average = climate.groupby("group")["raw_climate_score"].transform("mean")
    climate["climate_net_advantage"] = climate["raw_climate_score"] - group_average
    max_abs = climate["climate_net_advantage"].abs().max()
    if max_abs and pd.notna(max_abs):
        climate["climate_net_advantage"] = climate["climate_net_advantage"] / max_abs

    return climate[
        [
            "team",
            "venue",
            "venue_temp",
            "home_temp",
            "temp_disadvantage",
            "altitude_disadvantage",
            "humidity_factor",
            "climate_net_advantage",
        ]
    ].copy()


def merge_climate_into_features(features: pd.DataFrame, climate: pd.DataFrame) -> pd.DataFrame:
    climate_lookup = climate.copy()
    climate_lookup["team_key"] = climate_lookup["team"].map(canonical_team)

    base = features.copy()
    base["home_team_key"] = base["home_team"].map(canonical_team)
    base["away_team_key"] = base["away_team"].map(canonical_team)

    home_climate = climate_lookup[
        [
            "team_key",
            "temp_disadvantage",
            "altitude_disadvantage",
            "humidity_factor",
            "climate_net_advantage",
        ]
    ].rename(
        columns={
            "team_key": "home_team_key",
            "temp_disadvantage": "home_temp_disadvantage",
            "altitude_disadvantage": "home_altitude_disadvantage",
            "humidity_factor": "home_humidity_factor",
            "climate_net_advantage": "home_climate_advantage",
        }
    )
    away_climate = climate_lookup[
        [
            "team_key",
            "temp_disadvantage",
            "altitude_disadvantage",
            "humidity_factor",
            "climate_net_advantage",
        ]
    ].rename(
        columns={
            "team_key": "away_team_key",
            "temp_disadvantage": "away_temp_disadvantage",
            "altitude_disadvantage": "away_altitude_disadvantage",
            "humidity_factor": "away_humidity_factor",
            "climate_net_advantage": "away_climate_advantage",
        }
    )

    base = base.drop(columns=[column for column in CLIMATE_FEATURE_COLUMNS if column in base.columns])
    base = base.merge(home_climate, on="home_team_key", how="left")
    base = base.merge(away_climate, on="away_team_key", how="left")
    base["climate_advantage_diff"] = (
        base["home_climate_advantage"] - base["away_climate_advantage"]
    )

    return base.drop(columns=["home_team_key", "away_team_key"])


def print_leaderboard(climate: pd.DataFrame) -> None:
    ranked = climate.sort_values("climate_net_advantage", ascending=False)

    print("\nClimate venue advantage leaderboard")
    print("-" * 44)
    print("Most helped by venue conditions")
    for row in ranked.head(8).itertuples(index=False):
        print(f"{row.team:<24} {row.climate_net_advantage:>6.3f}  {row.venue}")

    print("\nMost hurt by venue conditions")
    for row in ranked.tail(8).sort_values("climate_net_advantage").itertuples(index=False):
        print(f"{row.team:<24} {row.climate_net_advantage:>6.3f}  {row.venue}")


def main() -> None:
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing feature table: {FEATURES_PATH}")

    climate = team_climate_rows()
    climate.to_csv(CLIMATE_FEATURES_PATH, index=False)
    print(f"Saved climate features: {CLIMATE_FEATURES_PATH}")

    features = pd.read_csv(FEATURES_PATH)
    before_columns = len(
        [column for column in features.columns if column not in CLIMATE_FEATURE_COLUMNS]
    )
    updated = merge_climate_into_features(features, climate)
    after_columns = len(updated.columns)
    updated.to_csv(FEATURES_PATH, index=False)

    print_leaderboard(climate)
    print(f"\nfeatures.csv updated: {before_columns} columns → {after_columns} columns")


if __name__ == "__main__":
    main()
