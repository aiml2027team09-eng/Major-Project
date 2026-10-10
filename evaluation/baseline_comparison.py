"""
evaluation/baseline_comparison.py
===================================
Baseline model comparison for the Hybrid IDS.

Trains and evaluates multiple baseline classifiers:
  1. Logistic Regression
  2. Random Forest
  3. SVM (LinearSVC for speed on large datasets)
  4. XGBoost (standalone)
  5. MLP (sklearn)
  6. Autoencoder only
  7. Autoencoder + XGBoost (full hybrid)

Research purpose
----------------
Demonstrates whether each component contributes meaningful improvement
beyond simpler baselines. This is essential for the research paper.
"""

from __future__ import annotations

import json
import os
import time
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


# ─────────────────────────────────────────────
#  Helper: fit, predict, and time
# ─────────────────────────────────────────────

def _fit_predict_timed(
    clf,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    name: str,
) -> dict:
    """Train classifier and evaluate on test set with timing."""
    print(f"  Training: {name}...", end=" ", flush=True)

    t0 = time.perf_counter()
    try:
        clf.fit(X_train, y_train)
    except Exception as e:
        print(f"FAILED ({e})")
        return {"model": name, "error": str(e)}

    train_time = time.perf_counter() - t0

    t0    = time.perf_counter()
    preds = clf.predict(X_test)
    inf_t = time.perf_counter() - t0

    acc   = float(accuracy_score(y_test, preds))
    prec  = float(precision_score(y_test, preds, average="weighted", zero_division=0))
    rec   = float(recall_score(y_test, preds, average="weighted", zero_division=0))
    f1_w  = float(f1_score(y_test, preds, average="weighted", zero_division=0))
    f1_m  = float(f1_score(y_test, preds, average="macro", zero_division=0))

    latency_ms = inf_t * 1000 / len(X_test)

    print(f"done. Acc={acc:.4f}  F1-w={f1_w:.4f}  Time={train_time:.1f}s")

    return {
        "model":                name,
        "accuracy":             acc,
        "precision_weighted":   prec,
        "recall_weighted":      rec,
        "f1_weighted":          f1_w,
        "f1_macro":             f1_m,
        "train_time_s":         float(train_time),
        "latency_ms_per_sample": latency_ms,
    }


# ─────────────────────────────────────────────
#  Individual baseline builders
# ─────────────────────────────────────────────

def build_logistic_regression(max_iter: int = 1000):
    return LogisticRegression(
        max_iter=max_iter, solver="lbfgs", multi_class="auto",
        random_state=42, n_jobs=-1,
    )


def build_random_forest(n_estimators: int = 200):
    return RandomForestClassifier(
        n_estimators=n_estimators, max_depth=15,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )


def build_linear_svm():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm", LinearSVC(max_iter=3000, class_weight="balanced", random_state=42)),
    ])


def build_xgboost_standalone(n_classes: int):
    return XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        objective="multi:softprob", num_class=n_classes,
        eval_metric="mlogloss", random_state=42,
        tree_method="hist", device="cpu",
    )


def build_mlp():
    return MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation="relu", solver="adam",
        max_iter=50, early_stopping=True,
        validation_fraction=0.1, random_state=42,
    )


# ─────────────────────────────────────────────
#  Autoencoder-only binary baseline
# ─────────────────────────────────────────────

def evaluate_autoencoder_baseline(
    autoencoder,
    X_test: np.ndarray,
    y_binary: np.ndarray,
    threshold: float,
) -> dict:
    """Evaluate autoencoder-only as a binary detector baseline."""
    from hybrid_ids.anomaly_detection import calculate_reconstruction_error

    t0     = time.perf_counter()
    errors = calculate_reconstruction_error(autoencoder, X_test)
    preds  = (errors > threshold).astype(int)
    inf_t  = time.perf_counter() - t0

    acc  = float(accuracy_score(y_binary, preds))
    f1_w = float(f1_score(y_binary, preds, average="weighted", zero_division=0))
    f1_m = float(f1_score(y_binary, preds, average="macro", zero_division=0))

    print(f"  [AE-only]  Acc={acc:.4f}  F1-w={f1_w:.4f}  Latency={inf_t*1000/len(X_test):.3f}ms/sample")

    return {
        "model":                "Autoencoder Only",
        "accuracy":             acc,
        "f1_weighted":          f1_w,
        "f1_macro":             f1_m,
        "latency_ms_per_sample": inf_t * 1000 / len(X_test),
        "note":                 "Binary only (normal vs anomaly)",
    }


# ─────────────────────────────────────────────
#  Full baseline comparison runner
# ─────────────────────────────────────────────

def run_baseline_comparison(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_classes: int,
    autoencoder=None,
    y_binary: np.ndarray | None = None,
    threshold: float | None = None,
    hybrid_metrics: dict | None = None,
    output_dir: str = "result_images/baselines",
    max_samples_train: int = 50_000,
) -> pd.DataFrame:
    """
    Train and evaluate all baseline models.

    Parameters
    ----------
    X_train, y_train  : training data (already preprocessed)
    X_test, y_test    : test data
    n_classes         : number of target classes
    autoencoder       : trained Keras autoencoder (for AE baseline)
    y_binary          : binary test labels (for AE baseline)
    threshold         : anomaly threshold (for AE baseline)
    hybrid_metrics    : pre-computed full hybrid metrics dict
    output_dir        : where to save results
    max_samples_train : cap training samples (performance limit for slow models)
    """
    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("BASELINE MODEL COMPARISON")
    print("=" * 60)

    # Subsample training if very large
    if len(X_train) > max_samples_train:
        idx    = np.random.choice(len(X_train), max_samples_train, replace=False)
        X_tr   = X_train[idx]
        y_tr   = y_train[idx]
        print(f"  Subsampled training to {max_samples_train} rows for baselines.")
    else:
        X_tr, y_tr = X_train, y_train

    results = []

    # 1. Logistic Regression
    r = _fit_predict_timed(
        build_logistic_regression(), X_tr, y_tr, X_test, y_test,
        "Logistic Regression",
    )
    results.append(r)

    # 2. Random Forest
    r = _fit_predict_timed(
        build_random_forest(), X_tr, y_tr, X_test, y_test,
        "Random Forest",
    )
    results.append(r)

    # 3. LinearSVM
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = _fit_predict_timed(
            build_linear_svm(), X_tr, y_tr, X_test, y_test,
            "LinearSVM",
        )
    results.append(r)

    # 4. XGBoost standalone
    r = _fit_predict_timed(
        build_xgboost_standalone(n_classes), X_tr, y_tr, X_test, y_test,
        "XGBoost (standalone)",
    )
    results.append(r)

    # 5. MLP
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = _fit_predict_timed(
            build_mlp(), X_tr, y_tr, X_test, y_test,
            "MLP",
        )
    results.append(r)

    # 6. Autoencoder only
    if autoencoder is not None and y_binary is not None and threshold is not None:
        r = evaluate_autoencoder_baseline(autoencoder, X_test, y_binary, threshold)
        results.append(r)

    # 7. Full hybrid (pre-computed)
    if hybrid_metrics:
        hybrid_row = {
            "model":                "Hybrid AE+XGBoost (Proposed)",
            "accuracy":             hybrid_metrics.get("accuracy"),
            "f1_weighted":          hybrid_metrics.get("f1_weighted"),
            "f1_macro":             hybrid_metrics.get("f1_macro"),
            "latency_ms_per_sample": hybrid_metrics.get("latency_ms_per_sample"),
        }
        results.append(hybrid_row)
        print(f"  [Hybrid]   Acc={hybrid_row['accuracy']:.4f}  "
              f"F1-w={hybrid_row['f1_weighted']:.4f} (pre-computed)")

    df = pd.DataFrame(results)

    print("\n=== Baseline Comparison Summary ===")
    display = ["model", "accuracy", "f1_weighted", "f1_macro", "latency_ms_per_sample"]
    cols = [c for c in display if c in df.columns]
    print(df[cols].to_string(index=False, float_format="{:.4f}".format))

    df.to_csv(os.path.join(output_dir, "baseline_comparison.csv"), index=False)
    with open(os.path.join(output_dir, "baseline_comparison.json"), "w") as f:
        json.dump(
            [{k: v for k, v in row.items() if not isinstance(v, str) or k == "model"}
             for row in results],
            f, indent=4,
        )

    _plot_baseline_comparison(df, output_dir)

    return df


def _plot_baseline_comparison(df: pd.DataFrame, output_dir: str) -> None:
    """Horizontal bar chart comparing baselines."""
    metrics = ["accuracy", "f1_weighted", "f1_macro"]
    metrics = [m for m in metrics if m in df.columns]

    df_valid = df.dropna(subset=metrics[:1])
    if df_valid.empty:
        return

    fig, axes = plt.subplots(1, len(metrics), figsize=(5 * len(metrics), 6))
    if len(metrics) == 1:
        axes = [axes]

    colors = plt.cm.Set2.colors

    for ax, metric in zip(axes, metrics):
        vals  = df_valid[metric].tolist()
        names = df_valid["model"].tolist()
        y_pos = range(len(names))
        bars  = ax.barh(y_pos, vals, color=colors[:len(vals)], edgecolor="black")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=8)
        ax.set_xlabel(metric)
        ax.set_title(metric.replace("_", " ").title(), fontsize=9)
        ax.set_xlim(0, 1.05)
        ax.axvline(0.9, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
        for bar, val in zip(bars, vals):
            ax.text(
                min(val + 0.01, 1.0), bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=7,
            )

    plt.suptitle("Baseline Model Comparison", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "baseline_comparison.png"), dpi=300)
    plt.close()
    print(f"  Baseline comparison chart saved → {output_dir}")
