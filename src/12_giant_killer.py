from itertools import combinations
from pathlib import Path
import json
import os
import pickle
import sys
import warnings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
LOCAL_DEPS = PROJECT_ROOT / ".codex_pydeps"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

import numpy as np
import pandas as pd

try:
    from constants import ALL_TEAMS, WC2026_GROUPS
except ImportError:
    from constants import ALL_TEAMS

    WC2026_GROUPS = {
        "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
        "B": ["Canada", "Switzerland", "Qatar", "Bosnia and Herzegovina"],
        "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
        "D": ["United States", "Paraguay", "Australia", "Turkey"],
        "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
        "F": ["Netherlands", "Japan", "Tunisia", "Sweden"],
        "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
        "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
        "I": ["France", "Senegal", "Norway", "Iraq"],
        "J": ["Argentina", "Algeria", "Austria", "Jordan"],
        "K": ["Portugal", "Uzbekistan", "Colombia", "DR Congo"],
        "L": ["England", "Croatia", "Ghana", "Panama"],
    }
    print("Warning: WC2026_GROUPS not found in constants.py. Using built-in fallback groups.")

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.utils.class_weight import compute_sample_weight


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

warnings.filterwarnings("ignore", category=UserWarning)


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

FEATURES_PATH = PROCESSED_DIR / "features.csv"
FEATURE_LIST_PATH = MODELS_DIR / "feature_list.json"
MASTER_TEAMS_PATH = PROCESSED_DIR / "master_teams.csv"
ELO_RATINGS_PATH = PROCESSED_DIR / "elo_ratings.csv"
H2H_STATS_PATH = PROCESSED_DIR / "h2h_stats.csv"
TEAM_FORM_PATH = PROCESSED_DIR / "team_form.csv"
MODEL_PATH = MODELS_DIR / "giant_killer_model.pkl"
UPSET_PREDICTIONS_PATH = PROCESSED_DIR / "upset_predictions.csv"

IDENTIFIER_COLUMNS = {"date", "home_team", "away_team", "tournament", "result", "result_encoded"}

MASTER_DEFAULTS = {
    "is_host": 0,
    "fifa_rank": 0,
    "squad_value_m": 0,
    "avg_ca": 0,
    "composure": 0,
    "avg_mentality": 0,
    "avg_pace": 0,
    "injured_count": 0,
    "availability_score": 0,
}


def load_feature_list(features: pd.DataFrame) -> list[str]:
    if FEATURE_LIST_PATH.exists():
        with FEATURE_LIST_PATH.open("r", encoding="utf-8") as feature_file:
            feature_list = json.load(feature_file)
    else:
        feature_list = [
            column
            for column in features.select_dtypes(include=[np.number]).columns
            if column not in IDENTIFIER_COLUMNS
        ]

    return [
        column
        for column in feature_list
        if column != "result_encoded" and column in features.columns
    ]


def label_upsets(features: pd.DataFrame) -> pd.DataFrame:
    features = features.copy()
    features["upset"] = (
        ((features["result"] == "A") & (features["elo_diff"] > 80))
        | ((features["result"] == "H") & (features["elo_diff"] < -80))
    ).astype(int)
    return features


def time_split(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(features) * 0.8)
    return features.iloc[:split_index].copy(), features.iloc[split_index:].copy()


def balance_training_data(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[pd.DataFrame, pd.Series, np.ndarray | None, str]:
    try:
        from imblearn.over_sampling import SMOTE

        minority_count = int(y_train.value_counts().min())
        if minority_count < 2:
            raise ValueError("Not enough minority samples for SMOTE.")

        smote = SMOTE(random_state=42, k_neighbors=min(5, minority_count - 1))
        x_balanced, y_balanced = smote.fit_resample(x_train, y_train)
        return x_balanced, y_balanced, None, "SMOTE"
    except Exception as exc:
        print(f"Warning: SMOTE unavailable or unsuitable ({exc}). Using balanced sample weights.")
        weights = compute_sample_weight(class_weight="balanced", y=y_train)
        return x_train, y_train, weights, 'class_weight="balanced"'


def train_model(x_train: pd.DataFrame, y_train: pd.Series) -> tuple[RandomForestClassifier, str]:
    x_balanced, y_balanced, sample_weights, balance_method = balance_training_data(x_train, y_train)
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced" if sample_weights is None and balance_method != "SMOTE" else None,
    )
    model.fit(x_balanced, y_balanced, sample_weight=sample_weights)
    return model, balance_method


def evaluate_model(model: RandomForestClassifier, x_test: pd.DataFrame, y_test: pd.Series) -> tuple[float, float, float]:
    predictions = model.predict(x_test)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        labels=[1],
        average="binary",
        zero_division=0,
    )
    return float(precision), float(recall), float(f1)


def load_master_lookup() -> dict[str, dict]:
    if MASTER_TEAMS_PATH.exists():
        master = pd.read_csv(MASTER_TEAMS_PATH)
    else:
        print("Warning: master_teams.csv not found. Using neutral static team defaults.")
        master = pd.DataFrame({"team": ALL_TEAMS})

    for column, default in MASTER_DEFAULTS.items():
        if column not in master.columns:
            master[column] = default

    return master.set_index("team").to_dict(orient="index")


def load_elo_lookup() -> dict[str, float]:
    elo = pd.read_csv(ELO_RATINGS_PATH)
    return dict(zip(elo["team"], pd.to_numeric(elo["elo"], errors="coerce").fillna(1500)))


def load_form_lookup() -> dict[str, dict]:
    if not TEAM_FORM_PATH.exists():
        return {}
    form = pd.read_csv(TEAM_FORM_PATH)
    return form.set_index("team").to_dict(orient="index")


def load_h2h_lookup() -> dict[frozenset, dict]:
    if not H2H_STATS_PATH.exists():
        return {}

    h2h = pd.read_csv(H2H_STATS_PATH)
    lookup = {}
    for row in h2h.itertuples(index=False):
        lookup[frozenset({row.team_a, row.team_b})] = {
            "team_a": row.team_a,
            "team_b": row.team_b,
            "h2h_matches": int(row.h2h_matches),
            "team_a_win_rate": float(row.team_a_win_rate),
        }
    return lookup


def numeric_value(data: dict, key: str, default: float = 0.0) -> float:
    value = pd.to_numeric(data.get(key, default), errors="coerce")
    if pd.isna(value):
        return float(default)
    return float(value)


def h2h_rate_for_home(h2h_lookup: dict[frozenset, dict], home_team: str, away_team: str) -> tuple[float, int]:
    stats = h2h_lookup.get(frozenset({home_team, away_team}))
    if not stats:
        return 0.5, 0

    if stats["team_a"] == home_team:
        return stats["team_a_win_rate"], stats["h2h_matches"]
    return 1 - stats["team_a_win_rate"], stats["h2h_matches"]


def build_matchup_features(
    favourite: str,
    underdog: str,
    feature_columns: list[str],
    elo_lookup: dict[str, float],
    master_lookup: dict[str, dict],
    form_lookup: dict[str, dict],
    h2h_lookup: dict[frozenset, dict],
) -> dict:
    home = favourite
    away = underdog
    home_elo = float(elo_lookup.get(home, 1500))
    away_elo = float(elo_lookup.get(away, 1500))
    home_master = master_lookup.get(home, {})
    away_master = master_lookup.get(away, {})
    home_form = form_lookup.get(home, {})
    away_form = form_lookup.get(away, {})
    h2h_rate, h2h_matches = h2h_rate_for_home(h2h_lookup, home, away)

    values = {
        "is_wc": 1,
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_diff": home_elo - away_elo,
        "home_form": numeric_value(home_form, "form_score", 50),
        "away_form": numeric_value(away_form, "form_score", 50),
        "form_diff": numeric_value(home_form, "form_score", 50)
        - numeric_value(away_form, "form_score", 50),
        "home_goals_avg": numeric_value(home_form, "goals_scored_avg"),
        "away_goals_avg": numeric_value(away_form, "goals_scored_avg"),
        "h2h_rate": h2h_rate,
        "h2h_matches": h2h_matches,
        "composure_diff": numeric_value(home_master, "composure")
        - numeric_value(away_master, "composure"),
        "mentality_diff": numeric_value(home_master, "avg_mentality")
        - numeric_value(away_master, "avg_mentality"),
        "squad_value_ratio": numeric_value(home_master, "squad_value_m")
        / (numeric_value(away_master, "squad_value_m") + 1),
        "ca_diff": numeric_value(home_master, "avg_ca") - numeric_value(away_master, "avg_ca"),
        "pace_diff": numeric_value(home_master, "avg_pace") - numeric_value(away_master, "avg_pace"),
        "rank_diff": numeric_value(away_master, "fifa_rank")
        - numeric_value(home_master, "fifa_rank"),
        "is_host": int(numeric_value(home_master, "is_host") == 1),
        "home_injured": numeric_value(home_master, "injured_count"),
        "away_injured": numeric_value(away_master, "injured_count"),
        "availability_diff": numeric_value(home_master, "availability_score")
        - numeric_value(away_master, "availability_score"),
        "is_wc_match": 1,
    }

    return {column: values.get(column, 0.0) for column in feature_columns}


def predict_group_stage_upsets(
    model: RandomForestClassifier,
    feature_columns: list[str],
    elo_lookup: dict[str, float],
    master_lookup: dict[str, dict],
    form_lookup: dict[str, dict],
    h2h_lookup: dict[frozenset, dict],
) -> pd.DataFrame:
    rows = []

    for group, teams in WC2026_GROUPS.items():
        for team_a, team_b in combinations(teams, 2):
            elo_a = float(elo_lookup.get(team_a, 1500))
            elo_b = float(elo_lookup.get(team_b, 1500))
            elo_gap = abs(elo_a - elo_b)
            if elo_gap <= 80:
                continue

            favourite, underdog = (team_a, team_b) if elo_a > elo_b else (team_b, team_a)
            features = build_matchup_features(
                favourite,
                underdog,
                feature_columns,
                elo_lookup,
                master_lookup,
                form_lookup,
                h2h_lookup,
            )
            x_matchup = pd.DataFrame([features], columns=feature_columns).replace(
                [np.inf, -np.inf], np.nan
            ).fillna(0)
            class_index = list(model.classes_).index(1)
            upset_prob = float(model.predict_proba(x_matchup)[0][class_index])

            rows.append(
                {
                    "group": group,
                    "favourite": favourite,
                    "underdog": underdog,
                    "upset_prob": round(upset_prob, 4),
                    "elo_gap": round(elo_gap, 2),
                }
            )

    return pd.DataFrame(
        rows,
        columns=["group", "favourite", "underdog", "upset_prob", "elo_gap"],
    ).sort_values(["upset_prob", "elo_gap"], ascending=[False, False])


def print_top_upsets(upsets: pd.DataFrame) -> None:
    print("\nTop 10 most likely giant killings")
    print("-" * 78)
    if upsets.empty:
        print("No group matchups with abs(elo_diff) > 80.")
        return

    print(f"{'Rank':>4}  {'Group':<5} {'Favourite':<18} {'Underdog':<18} {'Prob':>8} {'ELO gap':>8}")
    print("-" * 78)
    for rank, row in enumerate(upsets.head(10).itertuples(index=False), start=1):
        print(
            f"{rank:>4}  {row.group:<5} {row.favourite:<18} {row.underdog:<18} "
            f"{row.upset_prob:>8.3f} {row.elo_gap:>8.2f}"
        )


def main() -> None:
    features = pd.read_csv(FEATURES_PATH, parse_dates=["date"])
    features = features.sort_values("date", ascending=True, kind="mergesort").reset_index(drop=True)
    features = label_upsets(features)
    upset_rate = features["upset"].mean() * 100
    print(f"Upset rate: {upset_rate:.2f}% ({int(features['upset'].sum())}/{len(features)})")

    feature_columns = load_feature_list(features)
    train, test = time_split(features)
    x_train = train[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_train = train["upset"].astype(int)
    x_test = test[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_test = test["upset"].astype(int)

    model, balance_method = train_model(x_train, y_train)
    precision, recall, f1 = evaluate_model(model, x_test, y_test)
    print(f"Balance method: {balance_method}")
    print("\nUpset-class evaluation")
    print("-" * 44)
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 score:  {f1:.4f}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(model, model_file)
    print(f"\nSaved model: {MODEL_PATH}")

    upsets = predict_group_stage_upsets(
        model=model,
        feature_columns=feature_columns,
        elo_lookup=load_elo_lookup(),
        master_lookup=load_master_lookup(),
        form_lookup=load_form_lookup(),
        h2h_lookup=load_h2h_lookup(),
    )
    upsets.to_csv(UPSET_PREDICTIONS_PATH, index=False)
    print(f"Saved predictions: {UPSET_PREDICTIONS_PATH}")
    print_top_upsets(upsets)


if __name__ == "__main__":
    main()
