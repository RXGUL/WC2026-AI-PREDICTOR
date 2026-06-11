from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data" / "processed"
TROPHY_PATH = DATA_DIR / "trophy_probabilities.csv"
OUTPUT_PATH = DATA_DIR / "golden_boot_predictions.csv"
DEFAULT_TROPHY_PROBABILITY = 0.02

PLAYERS = [
    # name, team, goals_last_12mo, xg_per90, caps, big_game_goals, market_value_m
    ("Kylian Mbappe", "France", 32, 0.71, 78, 12, 180),
    ("Erling Haaland", "Norway", 36, 0.89, 35, 8, 200),
    ("Harry Kane", "England", 28, 0.65, 98, 15, 100),
    ("Vinicius Jr", "Brazil", 24, 0.58, 45, 7, 180),
    ("Lamine Yamal", "Spain", 18, 0.52, 22, 5, 180),
    ("Bukayo Saka", "England", 20, 0.48, 42, 6, 160),
    ("Lionel Messi", "Argentina", 18, 0.61, 187, 32, 35),
    ("Julian Alvarez", "Argentina", 22, 0.54, 48, 9, 90),
    ("Rodri", "Spain", 8, 0.18, 58, 3, 150),
    ("Pedri", "Spain", 12, 0.31, 38, 4, 180),
    ("Neymar", "Brazil", 14, 0.49, 128, 18, 50),
    ("Richarlison", "Brazil", 16, 0.44, 62, 10, 60),
    ("Romelu Lukaku", "Belgium", 24, 0.58, 102, 16, 25),
    ("Donyell Malen", "Netherlands", 18, 0.47, 38, 5, 50),
    ("Memphis Depay", "Netherlands", 14, 0.41, 102, 14, 20),
    ("Leroy Sane", "Germany", 16, 0.42, 58, 7, 45),
    ("Kai Havertz", "Germany", 18, 0.44, 55, 8, 65),
    ("Diogo Jota", "Portugal", 20, 0.51, 48, 9, 60),
    ("Cristiano Ronaldo", "Portugal", 16, 0.45, 215, 28, 15),
    ("Luis Diaz", "Colombia", 18, 0.46, 48, 8, 80),
    ("Radamel Falcao", "Colombia", 10, 0.38, 108, 14, 5),
    ("Hirving Lozano", "Mexico", 14, 0.39, 68, 9, 18),
    ("Raul Jimenez", "Mexico", 16, 0.42, 88, 12, 12),
    ("Darwin Nunez", "Uruguay", 20, 0.53, 38, 7, 80),
    ("Hwang Hee-chan", "South Korea", 18, 0.44, 52, 8, 25),
    ("Ayoze Perez", "Spain", 14, 0.36, 28, 3, 20),
    ("Ferran Torres", "Spain", 16, 0.41, 42, 6, 45),
    ("Phil Foden", "England", 22, 0.52, 45, 7, 150),
    ("Jude Bellingham", "England", 20, 0.48, 38, 8, 180),
    ("Antoine Griezmann", "France", 18, 0.44, 128, 18, 30),
]

OUTPUT_COLUMNS = [
    "rank",
    "player",
    "team",
    "golden_boot_probability",
    "goals_last_12mo",
    "xg_per90",
]

CREATE_TABLE_SQL = """
create table if not exists public.golden_boot_predictions (
    rank integer primary key,
    player text not null,
    team text not null,
    golden_boot_probability double precision not null,
    goals_last_12mo integer not null,
    xg_per90 double precision not null,
    updated_at timestamptz not null default now()
);
"""


def load_supabase_uploader() -> Any:
    module_path = SRC_DIR / "18_supabase_uploader.py"
    spec = importlib.util.spec_from_file_location("supabase_uploader", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Supabase uploader from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_probability(value: Any) -> float:
    probability = float(value)
    return probability / 100 if probability > 1 else probability


def load_trophy_probabilities() -> dict[str, float]:
    trophy = pd.read_csv(TROPHY_PATH)
    missing = {"team", "trophy_probability"} - set(trophy.columns)
    if missing:
        raise ValueError(f"{TROPHY_PATH} is missing required columns: {', '.join(sorted(missing))}")

    return {
        str(row.team): normalize_probability(row.trophy_probability)
        for row in trophy.itertuples(index=False)
    }


def build_predictions() -> pd.DataFrame:
    trophy_probabilities = load_trophy_probabilities()
    players = pd.DataFrame(
        PLAYERS,
        columns=[
            "player",
            "team",
            "goals_last_12mo",
            "xg_per90",
            "caps",
            "big_game_goals",
            "market_value_m",
        ],
    )

    players["team_trophy_probability"] = players["team"].map(
        lambda team: trophy_probabilities.get(team, DEFAULT_TROPHY_PROBABILITY)
    )
    players["raw_score"] = (
        (players["goals_last_12mo"] * 0.30)
        + (players["xg_per90"] * 100 * 0.25)
        + (players["big_game_goals"] * 0.20)
        + (players["market_value_m"] * 0.10)
        + (players["caps"] * 0.05)
        + (players["team_trophy_probability"] * 200 * 0.10)
    )

    raw_scores = players["raw_score"].to_numpy()
    scores = np.array(raw_scores)

    # Use temperature-scaled softmax to spread probabilities.
    temperature = 5.0
    scores_scaled = scores / temperature

    # Shift scores before exp to prevent overflow.
    scores_shifted = scores_scaled - np.max(scores_scaled)
    exp_scores = np.exp(scores_shifted)
    probabilities = (exp_scores / exp_scores.sum()) * 100
    players["golden_boot_probability"] = probabilities

    players = players.sort_values(
        ["golden_boot_probability", "raw_score", "player"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    players["rank"] = players.index + 1
    players["golden_boot_probability"] = players["golden_boot_probability"].round(4)

    return players[OUTPUT_COLUMNS]


def save_predictions(predictions: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(OUTPUT_PATH, index=False)


def print_leaderboard(predictions: pd.DataFrame, count: int = 10) -> None:
    print("Rank  Player              Team        GB%     Goals  xG/90")
    for row in predictions.head(count).itertuples(index=False):
        print(
            f"{row.rank:<5} "
            f"{row.player:<19} "
            f"{row.team:<11} "
            f"{row.golden_boot_probability:>6.2f}% "
            f"{row.goals_last_12mo:<6} "
            f"{row.xg_per90:.2f}"
        )


def table_exists(uploader: Any, client: dict[str, str], table_name: str) -> bool:
    try:
        uploader.api_json(
            "GET",
            f"{client['url']}/rest/v1/{table_name}",
            params={"select": "rank", "limit": "1"},
            headers=uploader.rest_headers(client["key"]),
        )
        return True
    except HTTPError as exc:
        if exc.code == 404:
            return False
        raise


def create_table_if_missing(uploader: Any, client: dict[str, str]) -> None:
    table_name = "golden_boot_predictions"
    if table_exists(uploader, client, table_name):
        return

    for rpc_name, payload_key in (("execute_sql", "query"), ("exec_sql", "sql")):
        try:
            uploader.api_json(
                "POST",
                f"{client['url']}/rest/v1/rpc/{rpc_name}",
                headers=uploader.rest_headers(client["key"]),
                payload={payload_key: CREATE_TABLE_SQL},
            )
            return
        except HTTPError as exc:
            if exc.code not in {400, 401, 403, 404}:
                raise

    raise RuntimeError(
        "Could not create golden_boot_predictions through Supabase REST. "
        "Create this table in Supabase SQL, then rerun the script:\n"
        f"{CREATE_TABLE_SQL.strip()}"
    )


def upload_predictions(predictions: pd.DataFrame) -> None:
    uploader = load_supabase_uploader()
    uploader.load_env(PROJECT_ROOT / ".env")

    client = {
        "url": uploader.require_env("SUPABASE_URL").rstrip("/"),
        "key": uploader.require_env("SUPABASE_KEY"),
    }
    create_table_if_missing(uploader, client)

    upload_df = predictions.copy()
    upload_df["updated_at"] = uploader.utc_now_iso()
    records = json.loads(upload_df.to_json(orient="records"))
    count = uploader.upsert_rows(
        client,
        "golden_boot_predictions",
        records,
        on_conflict="rank",
    )
    uploader.print_summary("golden_boot_predictions", count)


def main() -> None:
    predictions = build_predictions()
    save_predictions(predictions)
    print_leaderboard(predictions)
    upload_predictions(predictions)


if __name__ == "__main__":
    main()
