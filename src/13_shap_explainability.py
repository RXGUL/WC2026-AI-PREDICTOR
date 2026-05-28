from pathlib import Path
import json
import os
import pickle
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS = PROJECT_ROOT / ".codex_pydeps"
LOCAL_VENV_SITE_PACKAGES = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))
if LOCAL_VENV_SITE_PACKAGES.exists():
    sys.path.append(str(LOCAL_VENV_SITE_PACKAGES))

import numpy as np
import pandas as pd
import shap
import xgboost as xgb

try:
    from constants import HOST_NATIONS
except ImportError:
    HOST_NATIONS = ["Canada", "Mexico", "United States"]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
SHAP_PLOTS_DIR = PROJECT_ROOT / "outputs" / "shap_plots"

MODEL_PATH = MODELS_DIR / "xgboost_model.pkl"
FEATURE_LIST_PATH = MODELS_DIR / "feature_list.json"
FEATURES_PATH = PROCESSED_DIR / "features.csv"
MASTER_TEAMS_PATH = PROCESSED_DIR / "master_teams.csv"
ELO_RATINGS_PATH = PROCESSED_DIR / "elo_ratings.csv"
TEAM_FORM_PATH = PROCESSED_DIR / "team_form.csv"

FEATURE_IMPORTANCE_PATH = PROCESSED_DIR / "feature_importance.csv"
SHAP_VALUES_PATH = PROCESSED_DIR / "shap_values.csv"
TEAM_SHAP_SUMMARY_PATH = PROCESSED_DIR / "team_shap_summary.csv"
TEAM_WIN_PROBS_PATH = PROCESSED_DIR / "team_win_probs.csv"

TEAMS_TO_EXPLAIN = [
    "France",
    "England",
    "Brazil",
    "Argentina",
    "Spain",
    "Germany",
    "Portugal",
    "Netherlands",
]


def load_model_and_features():
    with MODEL_PATH.open("rb") as model_file:
        model = pickle.load(model_file)

    with FEATURE_LIST_PATH.open("r", encoding="utf-8") as feature_file:
        feature_columns = json.load(feature_file)

    return model, feature_columns


def predict_proba(model, x_frame: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    x_frame = x_frame[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)

    if hasattr(model, "predict_proba"):
        return model.predict_proba(x_frame)

    matrix = xgb.DMatrix(x_frame, feature_names=feature_columns)
    return np.asarray(model.predict(matrix))


def feature_importances(model, feature_columns: list[str]) -> pd.DataFrame:
    if hasattr(model, "feature_importances_"):
        values = np.asarray(model.feature_importances_, dtype=float)
        importance_lookup = dict(zip(feature_columns, values))
    elif hasattr(model, "get_score"):
        importance_lookup = model.get_score(importance_type="gain")
    else:
        importance_lookup = {}

    rows = [
        {
            "feature": feature,
            "importance": float(importance_lookup.get(feature, 0.0)),
        }
        for feature in feature_columns
    ]
    importance = pd.DataFrame(rows).sort_values(
        ["importance", "feature"], ascending=[False, True]
    )
    importance.insert(0, "rank", range(1, len(importance) + 1))
    return importance


def print_top_importances(importance: pd.DataFrame) -> None:
    top_15 = importance.head(15)
    max_importance = max(top_15["importance"].max(), 1e-12)

    print("\nTop 15 feature importances")
    print("-" * 76)
    for row in top_15.itertuples(index=False):
        bar_length = max(1, round((row.importance / max_importance) * 36))
        bar = "█" * bar_length
        print(f"{row.rank:>2}. {row.feature:<28} {row.importance:>10.4f} {bar}")


def load_lookups():
    elo = pd.read_csv(ELO_RATINGS_PATH)
    elo_lookup = dict(zip(elo["team"], pd.to_numeric(elo["elo"], errors="coerce").fillna(1500)))
    average_elo = float(pd.to_numeric(elo["elo"], errors="coerce").mean())

    if MASTER_TEAMS_PATH.exists():
        master = pd.read_csv(MASTER_TEAMS_PATH)
    else:
        print("Warning: master_teams.csv not found. Team vectors will use feature/elo averages for squad fields.")
        master = pd.DataFrame({"team": TEAMS_TO_EXPLAIN})

    master_lookup = master.set_index("team").to_dict(orient="index") if "team" in master else {}
    master_averages = master.select_dtypes(include=[np.number]).mean(numeric_only=True).to_dict()

    form_lookup = {}
    if TEAM_FORM_PATH.exists():
        form = pd.read_csv(TEAM_FORM_PATH)
        form_lookup = form.set_index("team").to_dict(orient="index")

    return elo_lookup, average_elo, master_lookup, master_averages, form_lookup


def number(value, default: float = 0.0) -> float:
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return float(default)
    return float(value)


def lookup_value(team_data: dict, averages: dict, key: str, fallback: float = 0.0) -> float:
    return number(team_data.get(key, averages.get(key, fallback)), fallback)


def team_feature_row(
    team: str,
    feature_columns: list[str],
    feature_means: pd.Series,
    elo_lookup: dict[str, float],
    average_elo: float,
    master_lookup: dict[str, dict],
    master_averages: dict,
    form_lookup: dict[str, dict],
) -> dict:
    team_data = master_lookup.get(team, {})
    team_form = form_lookup.get(team, {})
    avg_home_form = number(feature_means.get("home_form", 50), 50)
    avg_away_form = number(feature_means.get("away_form", 50), 50)
    avg_home_goals = number(feature_means.get("home_goals_avg", 0), 0)
    avg_away_goals = number(feature_means.get("away_goals_avg", 0), 0)
    team_elo = float(elo_lookup.get(team, average_elo))

    values = feature_means.to_dict()
    values.update(
        {
            "is_wc": 1,
            "home_elo": team_elo,
            "away_elo": average_elo,
            "elo_diff": team_elo - average_elo,
            "home_form": number(team_form.get("form_score", avg_home_form), avg_home_form),
            "away_form": avg_away_form,
            "form_diff": number(team_form.get("form_score", avg_home_form), avg_home_form)
            - avg_away_form,
            "home_goals_avg": number(
                team_form.get("goals_scored_avg", avg_home_goals), avg_home_goals
            ),
            "away_goals_avg": avg_away_goals,
            "h2h_rate": number(feature_means.get("h2h_rate", 0.5), 0.5),
            "h2h_matches": number(feature_means.get("h2h_matches", 0), 0),
            "composure_diff": lookup_value(team_data, master_averages, "composure")
            - number(master_averages.get("composure", 0), 0),
            "mentality_diff": lookup_value(team_data, master_averages, "avg_mentality")
            - number(master_averages.get("avg_mentality", 0), 0),
            "squad_value_ratio": lookup_value(team_data, master_averages, "squad_value_m")
            / (number(master_averages.get("squad_value_m", 0), 0) + 1),
            "ca_diff": lookup_value(team_data, master_averages, "avg_ca")
            - number(master_averages.get("avg_ca", 0), 0),
            "pace_diff": lookup_value(team_data, master_averages, "avg_pace")
            - number(master_averages.get("avg_pace", 0), 0),
            "rank_diff": number(master_averages.get("fifa_rank", 0), 0)
            - lookup_value(team_data, master_averages, "fifa_rank"),
            "is_host": int(team in HOST_NATIONS or lookup_value(team_data, master_averages, "is_host") == 1),
            "home_injured": lookup_value(team_data, master_averages, "injured_count"),
            "away_injured": number(master_averages.get("injured_count", 0), 0),
            "availability_diff": lookup_value(team_data, master_averages, "availability_score")
            - number(master_averages.get("availability_score", 0), 0),
            "is_wc_match": 1,
        }
    )

    return {feature: number(values.get(feature, 0), 0) for feature in feature_columns}


def build_team_vectors(features: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    feature_means = features[feature_columns].replace([np.inf, -np.inf], np.nan).mean(numeric_only=True)
    elo_lookup, average_elo, master_lookup, master_averages, form_lookup = load_lookups()
    rows = []

    for team in TEAMS_TO_EXPLAIN:
        row = team_feature_row(
            team,
            feature_columns,
            feature_means,
            elo_lookup,
            average_elo,
            master_lookup,
            master_averages,
            form_lookup,
        )
        row["team"] = team
        rows.append(row)

    return pd.DataFrame(rows)


def print_and_save_team_probabilities(model, team_vectors: pd.DataFrame, feature_columns: list[str]) -> None:
    probabilities = predict_proba(model, team_vectors, feature_columns)
    rows = []

    print("\nTeam probabilities vs average opponent")
    print("-" * 72)
    print(f"{'Team':<16} {'Win':>10} {'Draw':>10} {'Loss':>10}")
    print("-" * 72)

    for team, probs in zip(team_vectors["team"], probabilities):
        loss_prob = float(probs[0])
        draw_prob = float(probs[1])
        win_prob = float(probs[2])
        rows.append(
            {
                "team": team,
                "win_prob": round(win_prob, 4),
                "draw_prob": round(draw_prob, 4),
                "loss_prob": round(loss_prob, 4),
            }
        )
        print(f"{team:<16} {win_prob:>10.3f} {draw_prob:>10.3f} {loss_prob:>10.3f}")

    pd.DataFrame(rows).to_csv(TEAM_WIN_PROBS_PATH, index=False)


def class_two_shap_values(raw_values) -> np.ndarray:
    if isinstance(raw_values, list):
        return np.asarray(raw_values[2])

    values = np.asarray(raw_values)
    if values.ndim == 3:
        if values.shape[2] == 3:
            return values[:, :, 2]
        if values.shape[1] == 3:
            return values[:, 2, :]
    return values


def run_shap_analysis(model, features: pd.DataFrame, feature_columns: list[str], team_vectors: pd.DataFrame) -> None:
    sample_size = min(500, len(features))
    sample = (
        features[feature_columns]
        .sample(n=sample_size, random_state=42)
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
    )

    explainer = shap.TreeExplainer(model)
    sample_shap = class_two_shap_values(explainer.shap_values(sample))
    shap_df = pd.DataFrame(sample_shap, columns=feature_columns)
    shap_df.to_csv(SHAP_VALUES_PATH, index=False)

    team_x = team_vectors[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    team_shap = class_two_shap_values(explainer.shap_values(team_x))

    summary_rows = []
    for team, values in zip(team_vectors["team"], team_shap):
        ranked_indexes = np.argsort(values)[::-1][:3]
        row = {"team": team}
        for idx, feature_index in enumerate(ranked_indexes, start=1):
            row[f"top_feature_{idx}"] = feature_columns[feature_index]
            row[f"shap_{idx}"] = round(float(values[feature_index]), 6)
        summary_rows.append(row)

    pd.DataFrame(
        summary_rows,
        columns=[
            "team",
            "top_feature_1",
            "shap_1",
            "top_feature_2",
            "shap_2",
            "top_feature_3",
            "shap_3",
        ],
    ).to_csv(TEAM_SHAP_SUMMARY_PATH, index=False)


def main() -> None:
    SHAP_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    model, feature_columns = load_model_and_features()
    features = pd.read_csv(FEATURES_PATH, parse_dates=["date"])

    importance = feature_importances(model, feature_columns)
    importance.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
    print(f"Saved feature importance: {FEATURE_IMPORTANCE_PATH}")
    print_top_importances(importance)

    team_vectors = build_team_vectors(features, feature_columns)
    print_and_save_team_probabilities(model, team_vectors, feature_columns)

    run_shap_analysis(model, features, feature_columns, team_vectors)
    print(f"\nSaved SHAP values: {SHAP_VALUES_PATH}")
    print(f"Saved team SHAP summary: {TEAM_SHAP_SUMMARY_PATH}")
    print(f"Saved team win probabilities: {TEAM_WIN_PROBS_PATH}")
    print(f"Created SHAP plots directory: {SHAP_PLOTS_DIR}")


if __name__ == "__main__":
    main()
