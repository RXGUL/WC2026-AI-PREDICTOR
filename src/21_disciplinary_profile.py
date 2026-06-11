from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from constants import ALL_TEAMS


DATA_DIR = PROJECT_ROOT / "data" / "processed"
MATCHES_PATH = DATA_DIR / "matches_clean.csv"
FEATURES_PATH = DATA_DIR / "features.csv"
DISCIPLINARY_PATH = DATA_DIR / "disciplinary_profile.csv"
DISCIPLINE_COLUMNS = [
    "home_discipline_risk",
    "away_discipline_risk",
    "discipline_risk_diff",
]

TEAM_ALIASES = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Czechia": "Czech Republic",
    "Curacao": "Curaçao",
    "CuraÃ§ao": "Curaçao",
    "CuraÃƒÂ§ao": "Curaçao",
    "CuraÃƒÆ’Ã‚Â§ao": "Curaçao",
}


def canonical_team(team: object) -> str:
    value = str(team)
    return TEAM_ALIASES.get(value, value)


def normalise(series: pd.Series) -> pd.Series:
    clean = series.fillna(0).astype(float)
    min_value = clean.min()
    max_value = clean.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(0.0, index=series.index)
    return (clean - min_value) / (max_value - min_value)


def find_card_columns(matches: pd.DataFrame) -> dict[str, str | None]:
    columns = {column.lower(): column for column in matches.columns}
    return {
        "home_yellow": columns.get("home_yellow_cards") or columns.get("home_yellows"),
        "away_yellow": columns.get("away_yellow_cards") or columns.get("away_yellows"),
        "home_red": columns.get("home_red_cards") or columns.get("home_reds"),
        "away_red": columns.get("away_red_cards") or columns.get("away_reds"),
        "match_yellow": columns.get("yellow_cards") or columns.get("yellows"),
        "match_red": columns.get("red_cards") or columns.get("reds"),
    }


def has_team_card_columns(card_columns: dict[str, str | None]) -> bool:
    return all(
        card_columns[key]
        for key in ("home_yellow", "away_yellow", "home_red", "away_red")
    )


def has_match_card_columns(card_columns: dict[str, str | None]) -> bool:
    return bool(card_columns["match_yellow"] or card_columns["match_red"])


def is_stakes_match(tournament: object) -> bool:
    value = str(tournament).lower()
    cup_like = bool(
        re.search(
            r"world cup|euro|copa|gold cup|asian cup|african cup|championship|cup",
            value,
        )
    )
    lower_stakes = bool(re.search(r"qualification|qualifier|friendly|nations league", value))
    return cup_like and not lower_stakes


def recent_matches(matches: pd.DataFrame) -> pd.DataFrame:
    base = matches.copy()
    base["date"] = pd.to_datetime(base["date"], errors="coerce")
    base = base.dropna(subset=["date"])
    if base.empty:
        return base
    cutoff = base["date"].max() - pd.DateOffset(years=5)
    return base[base["date"] >= cutoff].copy()


def team_match_records(matches: pd.DataFrame, card_columns: dict[str, str | None]) -> pd.DataFrame:
    use_team_cards = has_team_card_columns(card_columns)
    use_match_cards = not use_team_cards and has_match_card_columns(card_columns)
    rows = []

    for match in matches.itertuples(index=False):
        row = match._asdict()
        home_goals = float(row.get("home_score", 0) or 0)
        away_goals = float(row.get("away_score", 0) or 0)
        total_goals = home_goals + away_goals
        close_match = abs(home_goals - away_goals) <= 1
        high_scoring_close = total_goals >= 4 and close_match
        stakes_match = is_stakes_match(row.get("tournament", ""))

        sides = [
            ("home", row.get("home_team"), home_goals, away_goals),
            ("away", row.get("away_team"), away_goals, home_goals),
        ]
        for side, team, goals_for, goals_against in sides:
            yellow_cards = 0.0
            red_cards = 0.0
            if use_team_cards:
                yellow_col = card_columns[f"{side}_yellow"]
                red_col = card_columns[f"{side}_red"]
                yellow_cards = float(row.get(yellow_col, 0) or 0)
                red_cards = float(row.get(red_col, 0) or 0)
            elif use_match_cards:
                yellow_col = card_columns["match_yellow"]
                red_col = card_columns["match_red"]
                yellow_cards = float(row.get(yellow_col, 0) or 0) / 2 if yellow_col else 0.0
                red_cards = float(row.get(red_col, 0) or 0) / 2 if red_col else 0.0

            goal_diff = goals_for - goals_against
            rows.append(
                {
                    "team": canonical_team(team),
                    "goal_diff": goal_diff,
                    "high_scoring_close": int(high_scoring_close),
                    "loss_aggression": int(goal_diff < 0 and goals_against >= 3 and goals_for > 0),
                    "stakes_match": int(stakes_match),
                    "yellow_cards": yellow_cards,
                    "red_cards": red_cards,
                }
            )

    return pd.DataFrame(rows)


def build_profile(matches: pd.DataFrame) -> pd.DataFrame:
    card_columns = find_card_columns(matches)
    use_cards = has_team_card_columns(card_columns) or has_match_card_columns(card_columns)
    records = team_match_records(recent_matches(matches), card_columns)
    teams = pd.DataFrame({"team": [canonical_team(team) for team in ALL_TEAMS]})

    if records.empty:
        profile = teams.copy()
        profile["matches_analysed"] = 0
        profile["avg_yellows_per_game"] = 0.0
        profile["avg_reds_per_game"] = 0.0
        profile["card_rate"] = 0.0
        profile["aggression_proxy"] = 0.0
        profile["discipline_risk"] = 0.5
        return profile

    grouped = records.groupby("team", as_index=False).agg(
        matches_analysed=("team", "size"),
        avg_yellows_per_game=("yellow_cards", "mean"),
        avg_reds_per_game=("red_cards", "mean"),
        card_rate_raw=("yellow_cards", lambda values: values.sum()),
        red_weight_raw=("red_cards", lambda values: values.sum() * 3),
        goal_diff_volatility=("goal_diff", "std"),
        high_scoring_close_rate=("high_scoring_close", "mean"),
        loss_aggression=("loss_aggression", "mean"),
        stakes_match_rate=("stakes_match", "mean"),
    )
    grouped["goal_diff_volatility"] = grouped["goal_diff_volatility"].fillna(0)
    grouped["card_rate"] = (
        grouped["card_rate_raw"] + grouped["red_weight_raw"]
    ) / grouped["matches_analysed"].clip(lower=1)

    grouped["aggression_proxy_raw"] = (
        0.35 * normalise(grouped["goal_diff_volatility"])
        + 0.25 * normalise(grouped["high_scoring_close_rate"])
        + 0.25 * normalise(grouped["loss_aggression"])
        + 0.15 * normalise(grouped["stakes_match_rate"])
    )
    grouped["aggression_proxy"] = normalise(grouped["aggression_proxy_raw"])
    grouped["discipline_risk"] = (
        normalise(grouped["card_rate"])
        if use_cards
        else normalise(grouped["aggression_proxy"])
    )

    profile = teams.merge(grouped, on="team", how="left")
    profile["matches_analysed"] = profile["matches_analysed"].fillna(0).astype(int)
    for column in [
        "avg_yellows_per_game",
        "avg_reds_per_game",
        "card_rate",
        "aggression_proxy",
        "discipline_risk",
    ]:
        profile[column] = profile[column].fillna(0.5 if column == "discipline_risk" else 0.0)
        profile[column] = profile[column].round(6)

    return profile[
        [
            "team",
            "avg_yellows_per_game",
            "avg_reds_per_game",
            "card_rate",
            "aggression_proxy",
            "discipline_risk",
            "matches_analysed",
        ]
    ].copy()


def merge_profile_into_features(features: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    lookup = profile[["team", "discipline_risk"]].copy()
    lookup["team_key"] = lookup["team"].map(canonical_team)

    base = features.drop(columns=[column for column in DISCIPLINE_COLUMNS if column in features.columns]).copy()
    base["home_team_key"] = base["home_team"].map(canonical_team)
    base["away_team_key"] = base["away_team"].map(canonical_team)

    home_profile = lookup[["team_key", "discipline_risk"]].rename(
        columns={"team_key": "home_team_key", "discipline_risk": "home_discipline_risk"}
    )
    away_profile = lookup[["team_key", "discipline_risk"]].rename(
        columns={"team_key": "away_team_key", "discipline_risk": "away_discipline_risk"}
    )

    merged = base.merge(home_profile, on="home_team_key", how="left")
    merged = merged.merge(away_profile, on="away_team_key", how="left")
    merged["home_discipline_risk"] = merged["home_discipline_risk"].fillna(0.5)
    merged["away_discipline_risk"] = merged["away_discipline_risk"].fillna(0.5)
    merged["discipline_risk_diff"] = (
        merged["home_discipline_risk"] - merged["away_discipline_risk"]
    )
    return merged.drop(columns=["home_team_key", "away_team_key"])


def print_leaderboard(profile: pd.DataFrame) -> None:
    ranked = profile.sort_values("discipline_risk", ascending=False)

    print("\nHighest discipline risk (red card danger):")
    for row in ranked.head(10).itertuples(index=False):
        print(f"{row.team:<24} {row.discipline_risk:>6.3f}")

    print("\nMost disciplined teams:")
    for row in ranked.tail(10).sort_values("discipline_risk", ascending=True).itertuples(index=False):
        print(f"{row.team:<24} {row.discipline_risk:>6.3f}")


def main() -> None:
    if not MATCHES_PATH.exists():
        raise FileNotFoundError(f"Missing matches file: {MATCHES_PATH}")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing feature table: {FEATURES_PATH}")

    matches = pd.read_csv(MATCHES_PATH)
    card_columns = find_card_columns(matches)
    if has_team_card_columns(card_columns) or has_match_card_columns(card_columns):
        print("Card columns found; using card-rate disciplinary profile.")
    else:
        print("No card columns found; using goal/result aggression proxy.")

    profile = build_profile(matches)
    profile.to_csv(DISCIPLINARY_PATH, index=False)
    print(f"Saved disciplinary profile: {DISCIPLINARY_PATH}")

    features = pd.read_csv(FEATURES_PATH)
    before_columns = len([column for column in features.columns if column not in DISCIPLINE_COLUMNS])
    updated = merge_profile_into_features(features, profile)
    after_columns = len(updated.columns)
    updated.to_csv(FEATURES_PATH, index=False)

    print_leaderboard(profile)
    print(f"\nfeatures.csv: {before_columns} → {after_columns} columns (+3 disciplinary)")


if __name__ == "__main__":
    main()
