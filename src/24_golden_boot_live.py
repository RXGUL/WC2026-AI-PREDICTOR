from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
RAW_FBREF_PATH = OUTPUT_DIR / "fbref_player_stats.csv"
LIVE_STATS_PATH = OUTPUT_DIR / "golden_boot_live_stats.csv"

load_dotenv(PROJECT_ROOT / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY") or os.getenv("FOOTBALL_API_KEY", "").strip()
BASE_URL = "https://api.football-data.org/v4"

headers = {"X-Auth-Token": API_KEY} if API_KEY else {}

WC2026_NATIONS = [
    "Spain",
    "France",
    "Brazil",
    "Argentina",
    "England",
    "Netherlands",
    "Germany",
    "Belgium",
    "Portugal",
    "Colombia",
    "Croatia",
    "Japan",
    "Switzerland",
    "Uruguay",
    "Norway",
    "Ecuador",
    "Morocco",
    "Senegal",
    "Mexico",
    "USA",
    "South Korea",
    "Australia",
    "Denmark",
    "Poland",
    "Serbia",
    "Turkey",
    "Ukraine",
    "Austria",
    "Czech Republic",
    "Scotland",
    "Algeria",
    "Egypt",
    "Nigeria",
    "Cameroon",
    "Ghana",
    "Ivory Coast",
    "Tunisia",
    "DR Congo",
    "South Africa",
    "Saudi Arabia",
    "Iran",
    "Qatar",
    "Paraguay",
    "Bolivia",
    "Venezuela",
    "Costa Rica",
    "Panama",
    "Haiti",
    "New Zealand",
    "Peru",
    "Chile",
    "Uzbekistan",
    "Bosnia & Herzegovina",
    "Indonesia",
]

NATION_CODE_TO_TEAM = {
    "ALG": "Algeria",
    "ARG": "Argentina",
    "AUS": "Australia",
    "AUT": "Austria",
    "BEL": "Belgium",
    "BIH": "Bosnia & Herzegovina",
    "BOL": "Bolivia",
    "BRA": "Brazil",
    "CAM": "Cameroon",
    "CHI": "Chile",
    "CHL": "Chile",
    "COL": "Colombia",
    "CRC": "Costa Rica",
    "CRO": "Croatia",
    "CIV": "Ivory Coast",
    "COD": "DR Congo",
    "CZE": "Czech Republic",
    "DEN": "Denmark",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "ENG": "England",
    "FRA": "France",
    "GER": "Germany",
    "GHA": "Ghana",
    "HAI": "Haiti",
    "IDN": "Indonesia",
    "IRN": "Iran",
    "JPN": "Japan",
    "KOR": "South Korea",
    "KSA": "Saudi Arabia",
    "MAR": "Morocco",
    "MEX": "Mexico",
    "NED": "Netherlands",
    "NGA": "Nigeria",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "PAN": "Panama",
    "PAR": "Paraguay",
    "PER": "Peru",
    "POL": "Poland",
    "POR": "Portugal",
    "QAT": "Qatar",
    "SCO": "Scotland",
    "SEN": "Senegal",
    "SRB": "Serbia",
    "RSA": "South Africa",
    "ESP": "Spain",
    "SUI": "Switzerland",
    "TUN": "Tunisia",
    "TUR": "Turkey",
    "UKR": "Ukraine",
    "URU": "Uruguay",
    "USA": "USA",
    "UZB": "Uzbekistan",
    "VEN": "Venezuela",
}


def print_json_response(label: str, payload: Any) -> None:
    print(f"\n--- {label} response ---")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def try_football_data_teams() -> bool:
    if not API_KEY:
        print("FOOTBALL_DATA_API_KEY is missing. Also checked FOOTBALL_API_KEY fallback.")
        return False

    found_teams = False
    for competition_id in (2000, 2018, 2022):
        url = f"{BASE_URL}/competitions/{competition_id}/teams"
        print(f"\nRequesting football-data.org teams: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            try:
                data = response.json()
            except ValueError:
                data = {"raw_text": response.text}
            print_json_response(f"competition {competition_id}", data)

            teams = data.get("teams", []) if isinstance(data, dict) else []
            if response.ok and teams:
                print(f"Found {len(teams)} teams for competition ID {competition_id}.")
                found_teams = True
        except requests.RequestException as exc:
            print(f"football-data.org request failed for competition {competition_id}: {exc}")

    if not found_teams:
        print("\nNo usable WC2026 squad/player data found from football-data.org.")
    else:
        print("\nfootball-data.org returned teams, but squad-level player stats are not available here.")
    return found_teams


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        flattened = []
        for column in df.columns:
            parts = [
                str(part).strip()
                for part in column
                if str(part).strip() and not str(part).startswith("Unnamed")
            ]
            deduped = []
            for part in parts:
                if part not in deduped:
                    deduped.append(part)
            flattened.append(" ".join(deduped).strip())
        df.columns = flattened
    return df


def find_fbref_table(soup: BeautifulSoup) -> Any:
    table = soup.find("table", {"id": "stats_standard"})
    if table is not None:
        return table

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "stats_standard" not in comment:
            continue
        comment_soup = BeautifulSoup(comment, "html.parser")
        table = comment_soup.find("table", {"id": "stats_standard"})
        if table is not None:
            return table

    return None


def find_column(columns: list[str], candidates: list[str]) -> str:
    normalized = {column.lower(): column for column in columns}

    for candidate in candidates:
        candidate_lower = candidate.lower()
        if candidate_lower in normalized:
            return normalized[candidate_lower]

    for candidate in candidates:
        candidate_lower = candidate.lower()
        for column in columns:
            column_lower = column.lower()
            if column_lower.endswith(candidate_lower) or candidate_lower in column_lower:
                return column

    raise KeyError(f"Could not find any of these columns: {candidates}")


def numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )


def nation_to_team(value: Any) -> str | None:
    text = str(value)
    matches = re.findall(r"\b[A-Z]{3}\b", text)
    if not matches:
        return None
    return NATION_CODE_TO_TEAM.get(matches[-1])


def scrape_fbref_standard_stats() -> pd.DataFrame:
    headers_browser = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://fbref.com/",
    }
    url = "https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats"
    print(f"\nRequesting FBref player stats: {url}")
    response = requests.get(url, headers=headers_browser, timeout=30)
    print(f"Status: {response.status_code}")
    if not response.ok:
        print("FBref error response preview:")
        print(response.text[:1000])
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    table = find_fbref_table(soup)
    if table is None:
        raise RuntimeError("Could not find FBref table with id='stats_standard'.")

    df = pd.read_html(str(table))[0]
    df = flatten_columns(df)

    print("\nFBref columns:")
    print(df.columns.tolist())
    print("\nFBref head(10):")
    print(df.head(10))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_FBREF_PATH, index=False)
    print(f"\nSaved raw FBref data to {RAW_FBREF_PATH}")
    return df


def build_live_stats(df: pd.DataFrame) -> pd.DataFrame:
    columns = df.columns.tolist()
    player_col = find_column(columns, ["Player"])
    nation_col = find_column(columns, ["Nation"])
    squad_col = find_column(columns, ["Squad"])
    comp_col = find_column(columns, ["Comp"])
    goals_col = find_column(columns, ["Performance Gls", "Gls"])
    xg_col = find_column(columns, ["Expected xG", "xG"])
    nineties_col = find_column(columns, ["Playing Time 90s", "90s"])

    stats = df[df[player_col].astype(str) != "Player"].copy()
    stats["goals"] = numeric_series(stats[goals_col])
    stats["xg"] = numeric_series(stats[xg_col])
    stats["nineties_played"] = numeric_series(stats[nineties_col])
    stats["xg_per90"] = stats["xg"] / stats["nineties_played"]
    stats["national_team"] = stats[nation_col].map(nation_to_team)

    stats = stats[
        stats["national_team"].isin(WC2026_NATIONS)
        & stats["goals"].notna()
        & stats["xg"].notna()
        & stats["nineties_played"].gt(0)
    ].copy()

    stats = stats.sort_values(["goals", "xg_per90"], ascending=[False, False]).head(30)
    stats = stats.reset_index(drop=True)
    stats["rank"] = stats.index + 1
    stats["xg_per90"] = stats["xg_per90"].round(3)

    output = stats[
        [
            "rank",
            player_col,
            "national_team",
            squad_col,
            comp_col,
            "goals",
            "xg",
            "nineties_played",
            "xg_per90",
        ]
    ].rename(
        columns={
            player_col: "player",
            squad_col: "club",
            comp_col: "league",
        }
    )
    return output


def print_top_20(live_stats: pd.DataFrame) -> None:
    print("\nTop 20 WC2026-eligible players by goals:")
    print("Rank  Player                 Nation       Club                 Goals  xG/90")
    for row in live_stats.head(20).itertuples(index=False):
        print(
            f"{row.rank:<5} "
            f"{row.player:<22} "
            f"{row.national_team:<12} "
            f"{row.club:<20} "
            f"{row.goals:>5.0f}  "
            f"{row.xg_per90:.2f}"
        )


def main() -> None:
    try_football_data_teams()
    df = scrape_fbref_standard_stats()
    live_stats = build_live_stats(df)
    live_stats.to_csv(LIVE_STATS_PATH, index=False)
    print_top_20(live_stats)
    print(f"\nSaved live Golden Boot stats to {LIVE_STATS_PATH}")


if __name__ == "__main__":
    main()
