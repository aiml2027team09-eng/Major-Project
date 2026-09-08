"""Load model metrics, retrain comparisons, and result images."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from dataset_config import PROFILES, VALID_DATASETS

RESULT_ROOT = "result_images"
STAGES = ("Autoencoder", "XGBoost", "Hybrid", "Overall")
METRICS = ("accuracy", "precision", "recall", "f1")

# Expected outcome targets for viva / project goals
EXPECTED_TARGETS = {
    "nsl_kdd": {
        "Autoencoder": {"test_accuracy": 0.85, "test_f1": 0.85, "test_precision": 0.90},
        "XGBoost": {"test_accuracy": 0.75, "test_f1": 0.70},
        "Hybrid": {"test_accuracy": 0.68, "test_precision": 0.80},
        "Overall": {"test_accuracy": 0.72, "test_f1": 0.68},
    },
    "cicids2018": {
        "Autoencoder": {"test_accuracy": 0.90, "test_f1": 0.78, "test_precision": 0.70},
        "XGBoost": {"test_accuracy": 0.95, "test_f1": 0.95},
        "Hybrid": {"test_accuracy": 0.95, "test_f1": 0.95},
        "Overall": {"test_accuracy": 0.97, "test_f1": 0.97},
    },
}


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_metrics_summary(project_root: Path, dataset: str) -> dict | None:
    path = project_root / RESULT_ROOT / dataset / "metrics_summary.json"
    return _read_json(path)


def load_retrain_comparison(project_root: Path) -> dict | None:
    path = project_root / RESULT_ROOT / "retrain_comparison.json"
    return _read_json(path)


def load_retrain_results(project_root: Path, dataset: str) -> dict | None:
    profile = PROFILES[dataset]  # type: ignore[index]
    path = project_root / profile.model_folder / "retrain_results.json"
    return _read_json(path)


def metrics_to_long_df(metrics: dict, dataset: str, split: str = "test") -> pd.DataFrame:
    """Convert metrics_summary.json to long format for charts."""
    rows = []
    for stage in STAGES:
        if stage not in metrics:
            continue
        for metric in METRICS:
            key = f"{split}_{metric}"
            if key in metrics[stage]:
                rows.append(
                    {
                        "dataset": dataset,
                        "stage": stage,
                        "metric": metric,
                        "split": split,
                        "value": metrics[stage][key],
                    }
                )
    return pd.DataFrame(rows)


def build_outcome_table(project_root: Path) -> pd.DataFrame:
    """Compare actual test metrics against expected targets."""
    project_root = Path(project_root)
    rows = []

    for dataset in VALID_DATASETS:
        metrics = load_metrics_summary(project_root, dataset)
        targets = EXPECTED_TARGETS.get(dataset, {})
        if not metrics:
            continue

        for stage, stage_targets in targets.items():
            if stage not in metrics:
                continue
            for metric_key, target in stage_targets.items():
                actual = metrics[stage].get(metric_key)
                if actual is None:
                    continue
                rows.append(
                    {
                        "dataset": dataset,
                        "stage": stage,
                        "metric": metric_key.replace("test_", ""),
                        "expected": target,
                        "actual": actual,
                        "delta": actual - target,
                        "met_target": actual >= target,
                    }
                )

    return pd.DataFrame(rows)


def list_result_images(project_root: Path, dataset: str) -> dict[str, Path]:
    """Return available chart paths keyed by chart name."""
    folder = project_root / RESULT_ROOT / dataset
    if not folder.exists():
        return {}

    images = {}
    for path in sorted(folder.glob("*.png")):
        images[path.stem] = path
    return images


def get_threshold_info(project_root: Path, dataset: str) -> dict | None:
    profile = PROFILES[dataset]  # type: ignore[index]
    path = project_root / profile.model_folder / "threshold.json"
    return _read_json(path)


def load_dataset_classes(project_root: Path, dataset: str) -> list[str]:
    """Return all attack/normal class names from the trained label encoder."""
    profile = PROFILES[dataset]  # type: ignore[index]
    path = project_root / profile.data_folder / "label_encoder.pkl"
    if not path.exists():
        return []
    encoder = joblib.load(path)
    return [str(c) for c in encoder.classes_]


def load_all_dataset_classes(project_root: Path) -> dict[str, list[str]]:
    """Map each dataset key to its full class list."""
    project_root = Path(project_root)
    return {ds: load_dataset_classes(project_root, ds) for ds in VALID_DATASETS}


def dataset_display_name(dataset_key: str) -> str:
    profile = PROFILES.get(dataset_key)  # type: ignore[arg-type]
    return profile.display_name if profile else dataset_key
