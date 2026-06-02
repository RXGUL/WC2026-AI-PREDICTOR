from itertools import combinations, permutations
from pathlib import Path
import json
import os
import pickle
import sys
import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_VENV_SITE_PACKAGES = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import numpy as np
import pandas as pd

if LOCAL_VENV_SITE_PACKAGES.exists():
    sys.path.append(str(LOCAL_VENV_SITE_PACKAGES))


def install_sparse_shim() -> None:
    if "scipy.sparse" in sys.modules:
        return

    scipy = types.ModuleType("scipy")
    sparse = types.ModuleType("scipy.sparse")

    class SparseBase:
        pass

    sparse.spmatrix = SparseBase
    sparse.csr_matrix = SparseBase
    sparse.csc_matrix = SparseBase
    sparse.coo_matrix = SparseBase
    sparse.lil_matrix = SparseBase
    sparse.dok_matrix = SparseBase
    sparse.issparse = lambda data: False
    scipy.sparse = sparse

    sys.modules["scipy"] = scipy
    sys.modules["scipy.sparse"] = sparse


install_sparse_shim()
import xgboost as xgb

try:
    from constants import ALL_TEAMS, HOST_NATIONS, WC2026_GROUPS
except ImportError:
    from constants import ALL_TEAMS

    HOST_NATIONS = ["Canada", "Mexico", "United States"]
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
    print("Warning: WC2026_GROUPS/HOST_NATIONS not found in constants.py. Using built-in fallback groups.")


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"

MODEL_PATH = MODELS_DIR / "xgboost_model.pkl"
FEATURE_LIST_PATH = MODELS_DIR / "feature_list.json"
FEATURES_PATH = PROCESSED_DIR / "features.csv"
MASTER_TEAMS_PATH = PROCESSED_DIR / "master_teams.csv"
ELO_RATINGS_PATH = PROCESSED_DIR / "elo_ratings.csv"
H2H_STATS_PATH = PROCESSED_DIR / "h2h_stats.csv"
TEAM_FORM_PATH = PROCESSED_DIR / "team_form.csv"
TROPHY_PROBABILITIES_PATH = PROCESSED_DIR / "trophy_probabilities.csv"
CLIMATE_FEATURES_PATH = PROCESSED_DIR / "climate_features.csv"

SIMULATIONS = 10_000
RANDOM_SEED = 42

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
TO_ALL_TEAMS_ALIASES = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Curacao": "Curaçao",
    "Curaçao": "Curaçao",
    "Czechia": "Czech Republic",
}


def canonical_team(team: object) -> str:
    value = str(team)
    return TEAM_ALIASES.get(value, value)


def tournament_team(team: object) -> str:
    value = str(team)
    return TO_ALL_TEAMS_ALIASES.get(value, value)


def load_model_and_features():
    with MODEL_PATH.open("rb") as model_file:
        model = pickle.load(model_file)

    with FEATURE_LIST_PATH.open("r", encoding="utf-8") as feature_file:
        feature_columns = json.load(feature_file)

    return model, feature_columns


def predict_proba(model, x_frame: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    x_frame = x_frame[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(x_frame)
        if hasattr(model, "classes_"):
            ordered = np.zeros((len(x_frame), 3))
            for index, label in enumerate(model.classes_):
                ordered[:, int(label)] = probabilities[:, index]
            return ordered
        return probabilities

    matrix = xgb.DMatrix(x_frame, feature_names=feature_columns)
    return np.asarray(model.predict(matrix))


def number(value, default: float = 0.0) -> float:
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return float(default)
    return float(value)


def load_team_data():
    elo = pd.read_csv(ELO_RATINGS_PATH)
    elo_lookup = dict(zip(elo["team"], pd.to_numeric(elo["elo"], errors="coerce").fillna(1500)))

    if MASTER_TEAMS_PATH.exists():
        master = pd.read_csv(MASTER_TEAMS_PATH)
    else:
        print("Warning: master_teams.csv not found. Using neutral static team defaults.")
        master = pd.DataFrame({"team": ALL_TEAMS})
    master_lookup = master.set_index("team").to_dict(orient="index") if "team" in master else {}
    master_averages = master.select_dtypes(include=[np.number]).mean(numeric_only=True).to_dict()

    if TEAM_FORM_PATH.exists():
        form = pd.read_csv(TEAM_FORM_PATH)
        form_lookup = form.set_index("team").to_dict(orient="index")
    else:
        form_lookup = {}

    h2h_lookup = {}
    if H2H_STATS_PATH.exists():
        h2h = pd.read_csv(H2H_STATS_PATH)
        for row in h2h.itertuples(index=False):
            h2h_lookup[frozenset({row.team_a, row.team_b})] = {
                "team_a": row.team_a,
                "team_b": row.team_b,
                "h2h_matches": int(row.h2h_matches),
                "team_a_win_rate": float(row.team_a_win_rate),
            }

    climate_lookup = {}
    if CLIMATE_FEATURES_PATH.exists():
        climate = pd.read_csv(CLIMATE_FEATURES_PATH)
        climate["team_key"] = climate["team"].map(canonical_team)
        climate_lookup = climate.set_index("team_key").to_dict(orient="index")

    return elo_lookup, master_lookup, master_averages, form_lookup, h2h_lookup, climate_lookup


def master_value(team_data: dict, master_averages: dict, key: str, default: float = 0.0) -> float:
    return number(team_data.get(key, master_averages.get(key, default)), default)


def h2h_for_home(h2h_lookup: dict[frozenset, dict], home_team: str, away_team: str) -> tuple[float, int]:
    stats = h2h_lookup.get(frozenset({home_team, away_team}))
    if not stats:
        return 0.5, 0
    if stats["team_a"] == home_team:
        return stats["team_a_win_rate"], stats["h2h_matches"]
    return 1 - stats["team_a_win_rate"], stats["h2h_matches"]


def build_feature_row(
    home_team: str,
    away_team: str,
    feature_columns: list[str],
    feature_means: pd.Series,
    elo_lookup: dict[str, float],
    master_lookup: dict[str, dict],
    master_averages: dict,
    form_lookup: dict[str, dict],
    h2h_lookup: dict[frozenset, dict],
    climate_lookup: dict[str, dict],
) -> dict:
    home_elo = float(elo_lookup.get(home_team, 1500))
    away_elo = float(elo_lookup.get(away_team, 1500))
    home_master = master_lookup.get(home_team, {})
    away_master = master_lookup.get(away_team, {})
    home_form = form_lookup.get(home_team, {})
    away_form = form_lookup.get(away_team, {})
    home_climate = climate_lookup.get(canonical_team(home_team), {})
    away_climate = climate_lookup.get(canonical_team(away_team), {})
    h2h_rate, h2h_matches = h2h_for_home(h2h_lookup, home_team, away_team)

    home_form_score = number(home_form.get("form_score", feature_means.get("home_form", 50)), 50)
    away_form_score = number(away_form.get("form_score", feature_means.get("away_form", 50)), 50)

    values = feature_means.to_dict()
    values.update(
        {
            "is_wc": 1,
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": home_elo - away_elo,
            "home_form": home_form_score,
            "away_form": away_form_score,
            "form_diff": home_form_score - away_form_score,
            "home_goals_avg": number(
                home_form.get("goals_scored_avg", feature_means.get("home_goals_avg", 0)), 0
            ),
            "away_goals_avg": number(
                away_form.get("goals_scored_avg", feature_means.get("away_goals_avg", 0)), 0
            ),
            "h2h_rate": h2h_rate,
            "h2h_matches": h2h_matches,
            "composure_diff": master_value(home_master, master_averages, "composure")
            - master_value(away_master, master_averages, "composure"),
            "mentality_diff": master_value(home_master, master_averages, "avg_mentality")
            - master_value(away_master, master_averages, "avg_mentality"),
            "squad_value_ratio": master_value(home_master, master_averages, "squad_value_m")
            / (master_value(away_master, master_averages, "squad_value_m") + 1),
            "ca_diff": master_value(home_master, master_averages, "avg_ca")
            - master_value(away_master, master_averages, "avg_ca"),
            "pace_diff": master_value(home_master, master_averages, "avg_pace")
            - master_value(away_master, master_averages, "avg_pace"),
            "rank_diff": master_value(away_master, master_averages, "fifa_rank")
            - master_value(home_master, master_averages, "fifa_rank"),
            "is_host": int(home_team in HOST_NATIONS or master_value(home_master, master_averages, "is_host") == 1),
            "home_injured": master_value(home_master, master_averages, "injured_count"),
            "away_injured": master_value(away_master, master_averages, "injured_count"),
            "availability_diff": master_value(home_master, master_averages, "availability_score")
            - master_value(away_master, master_averages, "availability_score"),
            "is_wc_match": 1,
            "home_temp_disadvantage": number(
                home_climate.get("temp_disadvantage", feature_means.get("home_temp_disadvantage", 0)), 0
            ),
            "home_altitude_disadvantage": number(
                home_climate.get("altitude_disadvantage", feature_means.get("home_altitude_disadvantage", 0)), 0
            ),
            "home_humidity_factor": number(
                home_climate.get("humidity_factor", feature_means.get("home_humidity_factor", 0)), 0
            ),
            "home_climate_advantage": number(
                home_climate.get("climate_net_advantage", feature_means.get("home_climate_advantage", 0)), 0
            ),
            "away_temp_disadvantage": number(
                away_climate.get("temp_disadvantage", feature_means.get("away_temp_disadvantage", 0)), 0
            ),
            "away_altitude_disadvantage": number(
                away_climate.get("altitude_disadvantage", feature_means.get("away_altitude_disadvantage", 0)), 0
            ),
            "away_humidity_factor": number(
                away_climate.get("humidity_factor", feature_means.get("away_humidity_factor", 0)), 0
            ),
            "away_climate_advantage": number(
                away_climate.get("climate_net_advantage", feature_means.get("away_climate_advantage", 0)), 0
            ),
        }
    )
    values["climate_advantage_diff"] = (
        values["home_climate_advantage"] - values["away_climate_advantage"]
    )

    return {feature: number(values.get(feature, 0), 0) for feature in feature_columns}


def precompute_match_probabilities(model, feature_columns: list[str]) -> dict[tuple[str, str], np.ndarray]:
    features = pd.read_csv(FEATURES_PATH)
    feature_means = (
        features[feature_columns]
        .replace([np.inf, -np.inf], np.nan)
        .mean(numeric_only=True)
        .fillna(0)
    )
    elo_lookup, master_lookup, master_averages, form_lookup, h2h_lookup, climate_lookup = load_team_data()

    ordered_pairs = list(permutations(ALL_TEAMS, 2))
    rows = [
        build_feature_row(
            home_team,
            away_team,
            feature_columns,
            feature_means,
            elo_lookup,
            master_lookup,
            master_averages,
            form_lookup,
            h2h_lookup,
            climate_lookup,
        )
        for home_team, away_team in ordered_pairs
    ]
    probability_frame = pd.DataFrame(rows, columns=feature_columns)
    probabilities = predict_proba(model, probability_frame, feature_columns)
    return dict(zip(ordered_pairs, probabilities))


def simulate_group_match(
    rng: np.random.Generator,
    table: dict[str, int],
    probability_lookup: dict[tuple[str, str], np.ndarray],
    home_team: str,
    away_team: str,
) -> None:
    away_win, draw, home_win = probability_lookup[(home_team, away_team)]
    roll = rng.random()

    if roll < home_win:
        table[home_team] += 3
    elif roll < home_win + draw:
        table[home_team] += 1
        table[away_team] += 1
    else:
        table[away_team] += 3


def rank_group(rng: np.random.Generator, table: dict[str, int]) -> list[str]:
    tie_breakers = {team: rng.random() for team in table}
    return sorted(table, key=lambda team: (table[team], tie_breakers[team]), reverse=True)


def simulate_group_stage(
    rng: np.random.Generator,
    probability_lookup: dict[tuple[str, str], np.ndarray],
) -> list[str]:
    qualified = []
    third_place = []

    for group_teams in WC2026_GROUPS.values():
        teams = [tournament_team(team) for team in group_teams]
        table = {team: 0 for team in teams}

        for home_team, away_team in combinations(teams, 2):
            simulate_group_match(rng, table, probability_lookup, home_team, away_team)

        ranking = rank_group(rng, table)
        qualified.extend(ranking[:2])
        third_place.append((ranking[2], table[ranking[2]], rng.random()))

    third_place = sorted(third_place, key=lambda row: (row[1], row[2]), reverse=True)
    qualified.extend(team for team, _, _ in third_place[:8])
    return qualified


def knockout_winner(
    rng: np.random.Generator,
    probability_lookup: dict[tuple[str, str], np.ndarray],
    team_a: str,
    team_b: str,
) -> str:
    away_win, draw, home_win = probability_lookup[(team_a, team_b)]
    team_a_win = home_win + draw / 2
    return team_a if rng.random() < team_a_win else team_b


def play_knockout_round(
    rng: np.random.Generator,
    probability_lookup: dict[tuple[str, str], np.ndarray],
    teams: list[str],
) -> list[str]:
    winners = []
    for index in range(0, len(teams), 2):
        winners.append(knockout_winner(rng, probability_lookup, teams[index], teams[index + 1]))
    return winners


def run_simulations(probability_lookup: dict[tuple[str, str], np.ndarray]) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    trophy_counts = {team: 0 for team in ALL_TEAMS}
    final_counts = {team: 0 for team in ALL_TEAMS}
    sf_counts = {team: 0 for team in ALL_TEAMS}
    qf_counts = {team: 0 for team in ALL_TEAMS}

    for simulation in range(1, SIMULATIONS + 1):
        r32 = simulate_group_stage(rng, probability_lookup)
        rng.shuffle(r32)

        r16 = play_knockout_round(rng, probability_lookup, r32)
        qf = play_knockout_round(rng, probability_lookup, r16)
        sf = play_knockout_round(rng, probability_lookup, qf)
        final = play_knockout_round(rng, probability_lookup, sf)
        champion = play_knockout_round(rng, probability_lookup, final)[0]

        for team in qf:
            qf_counts[team] += 1
        for team in sf:
            sf_counts[team] += 1
        for team in final:
            final_counts[team] += 1
        trophy_counts[champion] += 1

        if simulation % 1000 == 0:
            print(f"Completed {simulation:,}/{SIMULATIONS:,} simulations")

    rows = []
    for team in ALL_TEAMS:
        rows.append(
            {
                "team": team,
                "trophy_probability": round((trophy_counts[team] / SIMULATIONS) * 100, 2),
                "final_prob": round((final_counts[team] / SIMULATIONS) * 100, 2),
                "sf_prob": round((sf_counts[team] / SIMULATIONS) * 100, 2),
                "qf_prob": round((qf_counts[team] / SIMULATIONS) * 100, 2),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["trophy_probability", "final_prob", "sf_prob"], ascending=[False, False, False]
    )


def print_leaderboard(results: pd.DataFrame) -> None:
    top_16 = results.head(16)
    max_probability = max(top_16["trophy_probability"].max(), 1e-12)

    print("\nTrophy probability leaderboard")
    print("-" * 86)
    print(f"{'Rank':>4}  {'Team':<18} {'Trophy %':>9} {'Final %':>8} {'SF %':>8} {'QF %':>8}  Chart")
    print("-" * 86)
    for rank, row in enumerate(top_16.itertuples(index=False), start=1):
        bar_length = max(1, round((row.trophy_probability / max_probability) * 32))
        bar = "█" * bar_length
        print(
            f"{rank:>4}  {row.team:<18} {row.trophy_probability:>9.2f} "
            f"{row.final_prob:>8.2f} {row.sf_prob:>8.2f} {row.qf_prob:>8.2f}  {bar}"
        )


def main() -> None:
    model, feature_columns = load_model_and_features()
    print("Precomputing matchup probabilities...")
    probability_lookup = precompute_match_probabilities(model, feature_columns)
    print(f"Precomputed {len(probability_lookup):,} ordered matchup probabilities")

    results = run_simulations(probability_lookup)
    results.to_csv(TROPHY_PROBABILITIES_PATH, index=False)
    print(f"\nSaved {TROPHY_PROBABILITIES_PATH}")
    print_leaderboard(results)


if __name__ == "__main__":
    main()
