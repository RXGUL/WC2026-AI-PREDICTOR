from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TROPHY_COLUMNS = [
    "team",
    "trophy_probability",
    "final_prob",
    "sf_prob",
    "qf_prob",
    "group_name",
    "elo",
    "squad_value_m",
    "fifa_rank",
    "updated_at",
]
REPORT_COLUMNS = ["team", "report_text", "word_count", "updated_at"]
PLAYER_STATUS_COLUMNS = [
    "player",
    "team",
    "status",
    "confidence",
    "summary",
    "updated_at",
]
CHANGE_LOG_COLUMNS = [
    "player",
    "team",
    "old_status",
    "new_status",
    "confidence",
    "summary",
    "logged_at",
]
TEAM_ALIASES = {
    "Bosnia and Herzegovina": "Bosnia-Herzegovina",
    "Curaçao": "Curacao",
    "Curaçao": "Curacao",
    "Czech Republic": "Czechia",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing .env file at {path}")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def require_columns(df: pd.DataFrame, path: Path, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def to_records(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    return [
        {column: clean_value(value) for column, value in row.items()}
        for row in df[columns].to_dict(orient="records")
    ]


def merge_team_key(team: str) -> str:
    return TEAM_ALIASES.get(team, team)


def chunks(records: list[dict[str, Any]], size: int = 500):
    for start in range(0, len(records), size):
        yield records[start : start + size]


def rest_headers(key: str, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def api_json(
    method: str,
    url: str,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    payload: Any | None = None,
) -> Any:
    if params:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urllib.parse.urlencode(params)}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else None


def upsert_rows(
    client: dict[str, str],
    table_name: str,
    records: list[dict[str, Any]],
    on_conflict: str,
) -> int:
    for batch in chunks(records):
        api_json(
            "POST",
            f"{client['url']}/rest/v1/{table_name}",
            params={"on_conflict": on_conflict},
            headers=rest_headers(client["key"], "resolution=merge-duplicates"),
            payload=batch,
        )
    return len(records)


def insert_rows(client: dict[str, str], table_name: str, records: list[dict[str, Any]]) -> int:
    for batch in chunks(records):
        api_json(
            "POST",
            f"{client['url']}/rest/v1/{table_name}",
            headers=rest_headers(client["key"]),
            payload=batch,
        )
    return len(records)


def print_summary(table_name: str, count: int) -> None:
    print(f"[✓] {table_name}: {count} rows uploaded")


def load_trophy_predictions() -> list[dict[str, Any]]:
    trophy_path = PROJECT_ROOT / "data" / "processed" / "trophy_probabilities.csv"
    teams_path = PROJECT_ROOT / "data" / "processed" / "master_teams.csv"
    elo_path = PROJECT_ROOT / "data" / "processed" / "elo_ratings.csv"

    trophy = pd.read_csv(trophy_path)
    teams = pd.read_csv(teams_path)
    elo = pd.read_csv(elo_path)

    require_columns(
        trophy,
        trophy_path,
        ["team", "trophy_probability", "final_prob", "sf_prob", "qf_prob"],
    )
    require_columns(teams, teams_path, ["team", "group", "fifa_rank", "squad_value_m"])
    require_columns(elo, elo_path, ["team", "elo"])

    trophy = trophy.assign(_team_key=trophy["team"].map(merge_team_key))
    teams = teams.assign(_team_key=teams["team"].map(merge_team_key))

    merged = trophy.merge(
        teams[["_team_key", "group", "fifa_rank", "squad_value_m"]],
        on="_team_key",
        how="left",
    ).merge(elo[["team", "elo"]], on="team", how="left")

    missing_group = merged.loc[merged["group"].isna(), "team"].tolist()
    missing_elo = merged.loc[merged["elo"].isna(), "team"].tolist()
    if missing_group:
        raise ValueError(f"Missing group data for teams: {', '.join(missing_group)}")
    if missing_elo:
        raise ValueError(f"Missing Elo data for teams: {', '.join(missing_elo)}")

    merged = merged.rename(columns={"group": "group_name"})
    merged["updated_at"] = utc_now_iso()
    return to_records(merged, TROPHY_COLUMNS)


def load_analyst_reports() -> list[dict[str, Any]]:
    reports_path = PROJECT_ROOT / "outputs" / "reports" / "all_reports.json"
    reports = json.loads(reports_path.read_text(encoding="utf-8"))
    updated_at = utc_now_iso()

    if not isinstance(reports, dict):
        raise ValueError(f"{reports_path} must contain a JSON object keyed by team")

    df = pd.DataFrame(
        [
            {
                "team": team,
                "report_text": report_text,
                "word_count": len(str(report_text).split()),
                "updated_at": updated_at,
            }
            for team, report_text in reports.items()
        ]
    )
    return to_records(df, REPORT_COLUMNS)


def load_player_status() -> list[dict[str, Any]]:
    status_path = PROJECT_ROOT / "data" / "injuries" / "player_status.csv"
    status = pd.read_csv(status_path)
    require_columns(status, status_path, PLAYER_STATUS_COLUMNS)
    return to_records(status, PLAYER_STATUS_COLUMNS)


def load_change_log() -> list[dict[str, Any]]:
    change_log_path = PROJECT_ROOT / "data" / "injuries" / "change_log.csv"
    change_log = pd.read_csv(change_log_path)
    require_columns(
        change_log,
        change_log_path,
        ["timestamp", "player", "team", "old_status", "new_status", "confidence", "summary"],
    )

    change_log = change_log.rename(columns={"timestamp": "logged_at"})
    return to_records(change_log, CHANGE_LOG_COLUMNS)


def filter_new_change_log_rows(
    client: dict[str, str],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = api_json(
        "GET",
        f"{client['url']}/rest/v1/change_log",
        params={"select": "logged_at"},
        headers=rest_headers(client["key"]),
    )
    existing_logged_at = {
        row["logged_at"]
        for row in rows
        if isinstance(row, dict) and row.get("logged_at")
    }

    return [
        record
        for record in records
        if record.get("logged_at") and record["logged_at"] not in existing_logged_at
    ]


def main() -> None:
    load_env(PROJECT_ROOT / ".env")

    supabase_url = require_env("SUPABASE_URL")
    supabase_key = require_env("SUPABASE_KEY")
    client = {"url": supabase_url.rstrip("/"), "key": supabase_key}

    trophy_records = load_trophy_predictions()
    print_summary(
        "trophy_predictions",
        upsert_rows(client, "trophy_predictions", trophy_records, on_conflict="team"),
    )

    report_records = load_analyst_reports()
    print_summary(
        "analyst_reports",
        upsert_rows(client, "analyst_reports", report_records, on_conflict="team"),
    )

    status_records = load_player_status()
    print_summary(
        "player_status",
        upsert_rows(client, "player_status", status_records, on_conflict="player,team"),
    )

    change_log_records = filter_new_change_log_rows(client, load_change_log())
    print_summary(
        "change_log",
        insert_rows(client, "change_log", change_log_records) if change_log_records else 0,
    )


if __name__ == "__main__":
    main()
