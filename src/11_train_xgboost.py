from pathlib import Path
import json
import pickle
import sys
import types

import numpy as np
import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.csv"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "xgboost_model.pkl"
FEATURE_LIST_PATH = MODELS_DIR / "feature_list.json"
METRICS_PATH = MODELS_DIR / "model_metrics.json"

EXCLUDE_COLUMNS = {
    "date",
    "home_team",
    "away_team",
    "tournament",
    "result",
    "result_encoded",
}

LABEL_NAMES = {
    0: "Away",
    1: "Draw",
    2: "Home",
}


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


def import_xgboost():
    try:
        import xgboost as xgb

        return xgb
    except (ImportError, ModuleNotFoundError):
        local_site_packages = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
        if local_site_packages.exists():
            sys.path.append(str(local_site_packages))

        install_sparse_shim()

        for module_name in list(sys.modules):
            if module_name == "xgboost" or module_name.startswith("xgboost."):
                del sys.modules[module_name]

        import xgboost as xgb

        return xgb


def load_features() -> pd.DataFrame:
    features = pd.read_csv(FEATURES_PATH, parse_dates=["date"])
    features = features.sort_values("date", ascending=True, kind="mergesort").reset_index(drop=True)
    return features


def numeric_feature_columns(features: pd.DataFrame) -> list[str]:
    candidate_columns = [column for column in features.columns if column not in EXCLUDE_COLUMNS]
    numeric_columns = features[candidate_columns].select_dtypes(include=[np.number]).columns.tolist()
    return numeric_columns


def time_split(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(features) * 0.8)
    train = features.iloc[:split_index].copy()
    test = features.iloc[split_index:].copy()
    return train, test


def class_sample_weights(labels: pd.Series) -> np.ndarray:
    counts = labels.value_counts().to_dict()
    class_count = len(counts)
    total = len(labels)

    return labels.map(lambda label: total / (class_count * counts[label])).to_numpy(dtype=float)


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    return float((y_true == y_pred).mean())


def top_feature_importances(model, feature_columns: list[str]) -> list[dict]:
    scores = model.get_score(importance_type="gain")
    importances = [
        {
            "feature": feature,
            "importance": float(scores.get(feature, 0.0)),
        }
        for feature in feature_columns
    ]
    return sorted(importances, key=lambda row: row["importance"], reverse=True)


def print_importances(importances: list[dict], limit: int = 15) -> None:
    top = importances[:limit]
    max_importance = max((row["importance"] for row in top), default=0.0)

    print("\nTop 15 feature importances")
    print("-" * 76)
    for rank, row in enumerate(top, start=1):
        if max_importance > 0:
            bar_length = max(1, round((row["importance"] / max_importance) * 36))
        else:
            bar_length = 1
        bar = "█" * bar_length
        print(f"{rank:>2}. {row['feature']:<28} {row['importance']:>10.4f} {bar}")


def print_accuracy(overall_accuracy: float, win_loss_accuracy: float, test_size: int, win_loss_size: int) -> None:
    print("\nModel accuracy")
    print("-" * 76)
    print(f"Overall accuracy (W/D/L):      {overall_accuracy:.4f} on {test_size} test matches")
    print(f"Win/loss only accuracy:       {win_loss_accuracy:.4f} on {win_loss_size} non-draw matches")


def main() -> None:
    xgb = import_xgboost()
    features = load_features()
    feature_columns = numeric_feature_columns(features)
    train, test = time_split(features)

    x_train = train[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_train = train["result_encoded"].astype(int)
    x_test = test[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_test = test["result_encoded"].astype(int)
    weights = class_sample_weights(y_train)

    dtrain = xgb.DMatrix(x_train, label=y_train, weight=weights, feature_names=feature_columns)
    dtest = xgb.DMatrix(x_test, label=y_test, feature_names=feature_columns)

    params = {
        "objective": "multi:softprob",
        "num_class": 3,
        "max_depth": 5,
        "eta": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "mlogloss",
        "seed": 42,
        "random_state": 42,
    }

    model = xgb.train(params=params, dtrain=dtrain, num_boost_round=300, verbose_eval=False)

    probabilities = model.predict(dtest)
    predictions = probabilities.argmax(axis=1)
    y_test_values = y_test.to_numpy()

    overall_accuracy = accuracy(y_test_values, predictions)
    win_loss_mask = y_test_values != 1
    win_loss_accuracy = accuracy(y_test_values[win_loss_mask], predictions[win_loss_mask])
    importances = top_feature_importances(model, feature_columns)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(model, model_file)

    with FEATURE_LIST_PATH.open("w", encoding="utf-8") as feature_file:
        json.dump(feature_columns, feature_file, indent=2)

    metrics = {
        "model_type": "xgboost.Booster",
        "target": "result_encoded",
        "label_names": LABEL_NAMES,
        "rows_total": int(len(features)),
        "rows_train": int(len(train)),
        "rows_test": int(len(test)),
        "feature_count": int(len(feature_columns)),
        "overall_accuracy": overall_accuracy,
        "win_loss_only_accuracy": win_loss_accuracy,
        "win_loss_test_rows": int(win_loss_mask.sum()),
        "class_distribution_train": {
            LABEL_NAMES[int(label)]: int(count)
            for label, count in y_train.value_counts().sort_index().items()
        },
        "class_distribution_test": {
            LABEL_NAMES[int(label)]: int(count)
            for label, count in y_test.value_counts().sort_index().items()
        },
        "top_15_feature_importances": importances[:15],
    }
    with METRICS_PATH.open("w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2)

    print(f"Loaded {FEATURES_PATH}")
    print(f"Rows: {len(features)} | Features: {len(feature_columns)}")
    print(f"Train rows: {len(train)} | Test rows: {len(test)}")
    print_accuracy(overall_accuracy, win_loss_accuracy, len(test), int(win_loss_mask.sum()))
    print_importances(importances)
    print(f"\nSaved model: {MODEL_PATH}")
    print(f"Saved feature list: {FEATURE_LIST_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")


if __name__ == "__main__":
    main()
