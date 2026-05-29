from __future__ import annotations

from pathlib import Path
import json
import os
import re
import sys
import time
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
LOCAL_DEPS = PROJECT_ROOT / ".codex_pydeps"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

try:
    from constants import ALL_TEAMS, WC2026_GROUPS
except ImportError:
    from constants import ALL_TEAMS

    WC2026_GROUPS = {
        "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
        "B": ["Canada", "Switzerland", "Qatar", "Bosnia and Herzegovina"],
        "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
        "D": ["United States", "Paraguay", "Australia", "Turkey"],
        "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
        "F": ["Netherlands", "Japan", "Tunisia", "Sweden"],
        "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
        "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
        "I": ["France", "Senegal", "Norway", "Iraq"],
        "J": ["Argentina", "Algeria", "Austria", "Jordan"],
        "K": ["Portugal", "Uzbekistan", "Colombia", "DR Congo"],
        "L": ["England", "Croatia", "Ghana", "Panama"],
    }


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"

DATA_PATHS = {
    "trophy": PROCESSED_DIR / "trophy_probabilities.csv",
    "master": PROCESSED_DIR / "master_teams.csv",
    "elo": PROCESSED_DIR / "elo_ratings.csv",
    "features": PROCESSED_DIR / "feature_importance.csv",
    "upsets": PROCESSED_DIR / "upset_predictions.csv",
    "pressure": PROCESSED_DIR / "pressure_index.csv",
}

REQUIRED_COLUMNS = {
    "trophy": ["team", "trophy_probability", "final_prob", "sf_prob", "qf_prob"],
    "master": [
        "team",
        "group",
        "confederation",
        "is_host",
        "fifa_rank",
        "squad_value_m",
        "avg_ca",
        "composure",
        "avg_mentality",
        "injured_count",
        "availability_score",
    ],
    "elo": ["team", "elo", "matches_played"],
    "features": ["rank", "feature", "importance"],
    "upsets": ["group", "favourite", "underdog", "upset_prob", "elo_gap"],
    "pressure": [
        "team",
        "pressure_index",
        "knockout_win_rate",
        "group_win_rate",
        "knockout_games",
        "credibility",
    ],
}

MASTER_DEFAULTS = {
    "group": "",
    "confederation": "",
    "is_host": 0,
    "fifa_rank": 0,
    "squad_value_m": 0.0,
    "avg_ca": 0.0,
    "composure": 0.0,
    "avg_mentality": 0.0,
    "injured_count": 0,
    "availability_score": 0.0,
}

PRESSURE_DEFAULTS = {
    "pressure_index": 0.0,
    "knockout_win_rate": 0.0,
    "group_win_rate": 0.0,
    "knockout_games": 0,
    "credibility": "",
}


def load_csv(name: str) -> pd.DataFrame:
    path = DATA_PATHS[name]
    columns = REQUIRED_COLUMNS[name]

    if not path.exists():
        if name == "master":
            print(f"Warning: {path} not found. Using neutral team metadata defaults.")
            rows = [{"team": team, **MASTER_DEFAULTS} for team in ALL_TEAMS]
            return pd.DataFrame(rows, columns=columns)
        if name == "pressure":
            print(f"Warning: {path} not found. Using neutral pressure-index defaults.")
            rows = [{"team": team, **PRESSURE_DEFAULTS} for team in ALL_TEAMS]
            return pd.DataFrame(rows, columns=columns)
        raise FileNotFoundError(f"Required file not found: {path}")

    data = pd.read_csv(path)
    missing_columns = [column for column in columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"{path} is missing columns: {missing_columns}")
    return data


def load_dataframes() -> dict[str, pd.DataFrame]:
    return {name: load_csv(name) for name in DATA_PATHS}


def group_lookup() -> dict[str, str]:
    lookup = {}
    for group_name, teams in WC2026_GROUPS.items():
        for team in teams:
            lookup[team] = group_name
    return lookup


def to_number(value: Any, default: float = 0.0) -> float:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return float(default)
    return float(number)


def team_records(data: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if data.empty or "team" not in data.columns:
        return {}
    return data.set_index("team").to_dict(orient="index")


def build_team_lookup(dataframes: dict[str, pd.DataFrame]) -> dict[str, dict[str, Any]]:
    trophy_lookup = team_records(dataframes["trophy"])
    master_lookup = team_records(dataframes["master"])
    elo_lookup = team_records(dataframes["elo"])
    pressure_lookup = team_records(dataframes["pressure"])

    lookup = {}
    for team in ALL_TEAMS:
        combined = {
            "team": team,
            **trophy_lookup.get(team, {}),
            **master_lookup.get(team, {}),
            **elo_lookup.get(team, {}),
            **pressure_lookup.get(team, {}),
        }
        lookup[team] = combined
    return lookup


def elo_ranks(elo: pd.DataFrame) -> dict[str, int]:
    ranked = elo.copy()
    ranked["elo"] = pd.to_numeric(ranked["elo"], errors="coerce")
    ranked = ranked.sort_values("elo", ascending=False, kind="mergesort").reset_index(drop=True)
    return {row.team: index + 1 for index, row in enumerate(ranked.itertuples(index=False))}


def top_features(features: pd.DataFrame, count: int = 3) -> list[dict[str, Any]]:
    ordered = features.sort_values("rank", ascending=True, kind="mergesort").head(count)
    return [
        {
            "rank": int(to_number(row.rank)),
            "feature": str(row.feature),
            "importance": to_number(row.importance),
        }
        for row in ordered.itertuples(index=False)
    ]


def upset_status(team: str, upsets: pd.DataFrame) -> dict[str, Any]:
    as_favourite = upsets[upsets["favourite"] == team]
    as_underdog = upsets[upsets["underdog"] == team]

    risk_matches = [
        {
            "group": row.group,
            "opponent": row.underdog,
            "upset_prob": to_number(row.upset_prob),
            "elo_gap": to_number(row.elo_gap),
        }
        for row in as_favourite.itertuples(index=False)
    ]
    candidate_matches = [
        {
            "group": row.group,
            "opponent": row.favourite,
            "upset_prob": to_number(row.upset_prob),
            "elo_gap": to_number(row.elo_gap),
        }
        for row in as_underdog.itertuples(index=False)
    ]

    return {
        "upset_risk": bool(risk_matches),
        "upset_candidate": bool(candidate_matches),
        "upset_risk_matches": risk_matches,
        "upset_candidate_matches": candidate_matches,
    }


def build_contexts(dataframes: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    lookup = build_team_lookup(dataframes)
    groups = group_lookup()
    ranks = elo_ranks(dataframes["elo"])
    features = top_features(dataframes["features"])

    contexts = []
    for team in ALL_TEAMS:
        data = lookup[team]
        group = str(data.get("group") or groups.get(team, ""))
        if not group and team == "CuraÃ§ao":
            group = groups.get("Curacao", "")

        context = {
            "team": team,
            "group": group,
            "trophy_probability": to_number(data.get("trophy_probability")),
            "elo": to_number(data.get("elo"), 1500.0),
            "elo_rank": ranks.get(team, 0),
            "squad_value_m": to_number(data.get("squad_value_m")),
            "fifa_rank": int(to_number(data.get("fifa_rank"))),
            "composure": to_number(data.get("composure")),
            "avg_mentality": to_number(data.get("avg_mentality")),
            "pressure_index": to_number(data.get("pressure_index")),
            "knockout_win_rate": to_number(data.get("knockout_win_rate")),
            "injured_count": int(to_number(data.get("injured_count"))),
            "availability_score": to_number(data.get("availability_score")),
            "top_features": features,
            **upset_status(team, dataframes["upsets"]),
        }
        contexts.append(context)
    return contexts


def format_features(features: list[dict[str, Any]]) -> str:
    return ", ".join(
        f"{item['feature']} ({item['importance']:.3f})" for item in features
    )


def format_upset(context: dict[str, Any]) -> str:
    lines = []
    if context["upset_risk"]:
        risks = ", ".join(
            f"{match['opponent']} at {match['upset_prob']:.1%}"
            for match in context["upset_risk_matches"]
        )
        lines.append(f"Upset risk as favourite: yes, against {risks}.")
    else:
        lines.append("Upset risk as favourite: no listed matchup.")

    if context["upset_candidate"]:
        candidates = ", ".join(
            f"{match['opponent']} at {match['upset_prob']:.1%}"
            for match in context["upset_candidate_matches"]
        )
        lines.append(f"Upset candidate as underdog: yes, against {candidates}.")
    else:
        lines.append("Upset candidate as underdog: no listed matchup.")

    return " ".join(lines)


def build_prompt(context: dict[str, Any]) -> str:
    return f"""
Write like a BBC Sport World Cup 2026 analyst, with confident pundit language and no academic hedging.
Write exactly 150-200 words.
Do not use the phrases "based on the data" or "the model shows".
Write as if you have watched every match.
Reference the actual numbers below.
Cover overall assessment, key strengths, main risk, and trophy probability verdict.
End with one bold verdict sentence.

Team context:
- Team: {context["team"]}
- Group: {context["group"]}
- Trophy probability: {context["trophy_probability"]:.2f}%
- Elo rating: {context["elo"]:.2f}
- Elo rank among 48 teams: {context["elo_rank"]}
- Squad value: {context["squad_value_m"]:.2f}m
- FIFA rank: {context["fifa_rank"]}
- Composure score: {context["composure"]:.2f}
- Average mentality: {context["avg_mentality"]:.2f}
- Pressure index: {context["pressure_index"]:.2f}
- Knockout win rate: {context["knockout_win_rate"]:.2f}
- Injured count: {context["injured_count"]}
- Availability score: {context["availability_score"]:.2f}
- Upset status: {format_upset(context)}
- Top three model features to weave in naturally: {format_features(context["top_features"])}
""".strip()


def filename_for_team(team: str) -> str:
    clean_name = re.sub(r"[^A-Za-z0-9_ -]", "", team).strip()
    return clean_name.replace(" ", "_") + ".txt"


def report_word_count(report: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", report))


def generate_report(client: OpenAI, context: dict[str, Any]) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a sharp, concise BBC Sport World Cup analyst.",
            },
            {"role": "user", "content": build_prompt(context)},
        ],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def save_report(team: str, report: str) -> None:
    report_path = REPORTS_DIR / filename_for_team(team)
    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY was not found in .env")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dataframes = load_dataframes()
    contexts = build_contexts(dataframes)
    client = OpenAI(api_key=api_key)

    reports: dict[str, str] = {}
    succeeded = 0
    failed = 0

    for index, context in enumerate(contexts, start=1):
        team = context["team"]
        print(f"Generating [{index}/48]: {team}...")
        try:
            report = generate_report(client, context)
            succeeded += 1
        except Exception as exc:
            print(f"Error generating report for {team}: {exc}")
            report = "Report unavailable"
            failed += 1

        reports[team] = report
        save_report(team, report)
        print(report[:200])
        time.sleep(0.5)

    master_path = REPORTS_DIR / "all_reports.json"
    master_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")

    total_words = sum(report_word_count(report) for report in reports.values())
    print("\nReport generation summary")
    print(f"Succeeded: {succeeded}")
    print(f"Failed: {failed}")
    print(f"Total word count: {total_words}")
    print("\nSpain report")
    print(reports.get("Spain", "Report unavailable"))
    print("\nFrance report")
    print(reports.get("France", "Report unavailable"))


if __name__ == "__main__":
    main()
