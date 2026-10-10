"""
evaluation/temporal_evaluation.py
===================================
Temporal split evaluation for the Hybrid IDS (Experiment B).

Research Question (RQ3):
  How well does the system generalize under temporal train-test separation?

Hypothesis (H3):
  Temporal evaluation produces different performance from random splitting
  and provides a more realistic estimate of generalization.

Methodology
-----------
If the dataset contains a Timestamp column:
  - Earlier traffic  → Training
  - Middle traffic   → Validation
  - Latest traffic   → Testing

If no timestamp is present:
  - Reconstruct temporal order using row sequence (proxy)
  - Document the limitation clearly

This evaluates temporal generalization, a key limitation in existing IDS
research that relies purely on random splits.
"""

from __future__ import annotations

import json
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import LabelEncoder


# ─────────────────────────────────────────────
#  1. Create temporal splits
# ─────────────────────────────────────────────

def create_temporal_splits(
    X: pd.DataFrame,
    y: pd.Series,
    timestamps: pd.Series | None,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
) -> dict:
    """
    Create temporal train/val/test splits.

    Parameters
    ----------
    X          : feature DataFrame
    y          : label Series
    timestamps : datetime Series (None = use row order as proxy)
    train_frac : fraction for training
    val_frac   : fraction for validation
    test_frac  : fraction for test

    Returns
    -------
    dict with keys: X_train, y_train, X_val, y_val, X_test, y_test,
                    method (str), train_period, val_period, test_period
    """
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-6, \
        "Fractions must sum to 1.0"

    n = len(X)

    if timestamps is not None:
        # Sort by time
        order = np.argsort(timestamps.values)
        method = "timestamp"
    else:
        # Row order proxy
        order = np.arange(n)
        method = "row_order_proxy"
        warnings.warn(
            "No timestamp column found. Using row order as proxy for temporal split. "
            "This may not reflect true temporal ordering."
        )

    X_sorted = X.iloc[order].reset_index(drop=True)
    y_sorted = y.iloc[order].reset_index(drop=True)

    n_train = int(n * train_frac)
    n_val   = int(n * val_frac)

    X_train = X_sorted.iloc[:n_train]
    y_train = y_sorted.iloc[:n_train]

    X_val = X_sorted.iloc[n_train:n_train + n_val]
    y_val = y_sorted.iloc[n_train:n_train + n_val]

    X_test = X_sorted.iloc[n_train + n_val:]
    y_test = y_sorted.iloc[n_train + n_val:]

    # Period info
    if timestamps is not None:
        ts_sorted = timestamps.iloc[order].reset_index(drop=True)
        train_period = (
            str(ts_sorted.iloc[0]),
            str(ts_sorted.iloc[n_train - 1]),
        )
        val_period = (
            str(ts_sorted.iloc[n_train]),
            str(ts_sorted.iloc[n_train + n_val - 1]),
        )
        test_period = (
            str(ts_sorted.iloc[n_train + n_val]),
            str(ts_sorted.iloc[-1]),
        )
    else:
        train_period = (0, n_train - 1)
        val_period   = (n_train, n_train + n_val - 1)
        test_period  = (n_train + n_val, n - 1)

    print(f"\n  Temporal split method: {method}")
    print(f"  Train: {len(X_train)} samples  ({train_period[0]} → {train_period[1]})")
    print(f"  Val:   {len(X_val)}   samples  ({val_period[0]} → {val_period[1]})")
    print(f"  Test:  {len(X_test)}  samples  ({test_period[0]} → {test_period[1]})")

    # Label distribution shift between splits
    _report_label_distribution(y_train, y_val, y_test)

    return {
        "X_train": X_train, "y_train": y_train,
        "X_val":   X_val,   "y_val":   y_val,
        "X_test":  X_test,  "y_test":  y_test,
        "method":  method,
        "train_period": train_period,
        "val_period":   val_period,
        "test_period":  test_period,
    }


def _report_label_distribution(y_train, y_val, y_test) -> None:
    """Print attack class distribution across temporal splits."""
    train_dist = pd.Series(y_train).value_counts(normalize=True)
    val_dist   = pd.Series(y_val).value_counts(normalize=True)
    test_dist  = pd.Series(y_test).value_counts(normalize=True)

    all_classes = sorted(set(train_dist.index) | set(val_dist.index) | set(test_dist.index))

    print("\n  Class distribution across temporal splits (%):")
    header = f"  {'Class':<30s} {'Train':>8s} {'Val':>8s} {'Test':>8s}"
    print(header)
    print("  " + "-" * 56)
    for cls in all_classes:
        print(
            f"  {str(cls):<30s} "
            f"{train_dist.get(cls, 0) * 100:>7.2f}% "
            f"{val_dist.get(cls, 0) * 100:>7.2f}% "
            f"{test_dist.get(cls, 0) * 100:>7.2f}%"
        )


# ─────────────────────────────────────────────
#  2. Compare temporal vs random split performance
# ─────────────────────────────────────────────

def compare_temporal_vs_random(
    random_metrics: dict,
    temporal_metrics: dict,
    output_dir: str,
) -> dict:
    """
    Compare evaluation results from random split vs temporal split.

    Parameters
    ----------
    random_metrics   : dict from random split evaluation (metric_name → value)
    temporal_metrics : dict from temporal split evaluation

    Returns
    -------
    dict with comparison and generalization gap
    """
    keys = ["accuracy", "f1_weighted", "f1_macro", "precision_weighted",
            "recall_weighted", "fpr", "fnr"]

    comparison = {}
    for k in keys:
        rv = random_metrics.get(k, None)
        tv = temporal_metrics.get(k, None)
        if rv is not None and tv is not None:
            comparison[k] = {
                "random":          float(rv),
                "temporal":        float(tv),
                "generalization_gap": float(rv - tv),   # positive = optimistic bias in random
            }

    print("\n=== Random vs Temporal Split Comparison ===")
    print(f"  {'Metric':<25s} {'Random':>10s} {'Temporal':>10s} {'Gap':>10s}")
    print("  " + "-" * 57)
    for k, v in comparison.items():
        print(
            f"  {k:<25s} {v['random']:>10.4f} {v['temporal']:>10.4f} "
            f"{v['generalization_gap']:>+10.4f}"
        )

    _plot_temporal_comparison(comparison, output_dir)

    with open(os.path.join(output_dir, "temporal_vs_random.json"), "w") as f:
        json.dump(comparison, f, indent=4)

    return comparison


def _plot_temporal_comparison(comparison: dict, output_dir: str) -> None:
    """Bar chart: metric values for random vs temporal split."""
    if not comparison:
        return

    keys   = list(comparison.keys())
    random = [comparison[k]["random"]   for k in keys]
    temp   = [comparison[k]["temporal"] for k in keys]

    x = np.arange(len(keys))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - width / 2, random, width, label="Random split",   color="steelblue")
    ax.bar(x + width / 2, temp,   width, label="Temporal split", color="darkorange")
    ax.set_xticks(x)
    ax.set_xticklabels(keys, rotation=45, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Generalization Gap: Random Split vs Temporal Split")
    ax.legend()
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "temporal_vs_random.png"), dpi=300)
    plt.close()
    print(f"  Saved temporal comparison → {output_dir}/temporal_vs_random.png")


# ─────────────────────────────────────────────
#  3. Drift analysis over time segments
# ─────────────────────────────────────────────

def analyse_temporal_drift(
    autoencoder,
    X_sorted: np.ndarray,
    timestamps_sorted: np.ndarray | None,
    n_segments: int = 10,
    output_dir: str = "result_images/temporal",
) -> pd.DataFrame:
    """
    Compute reconstruction error statistics over time windows.

    Useful for showing how the error distribution evolves and
    identifying potential distribution shift moments.
    """
    from hybrid_ids.anomaly_detection import calculate_reconstruction_error

    os.makedirs(output_dir, exist_ok=True)
    n = len(X_sorted)
    seg_size = n // n_segments

    rows = []
    for i in range(n_segments):
        start = i * seg_size
        end   = start + seg_size if i < n_segments - 1 else n
        X_seg = X_sorted[start:end]

        if len(X_seg) == 0:
            continue

        errors = calculate_reconstruction_error(autoencoder, X_seg)
        row = {
            "segment":     i + 1,
            "start_idx":   start,
            "end_idx":     end,
            "n_samples":   len(X_seg),
            "mean_re":     float(np.mean(errors)),
            "std_re":      float(np.std(errors)),
            "p95_re":      float(np.percentile(errors, 95)),
        }
        if timestamps_sorted is not None:
            row["start_time"] = str(timestamps_sorted[start])
            row["end_time"]   = str(timestamps_sorted[end - 1])
        rows.append(row)

    df = pd.DataFrame(rows)

    # Plot RE evolution
    plt.figure(figsize=(12, 4))
    plt.plot(df["segment"], df["mean_re"], marker="o", label="Mean RE", color="steelblue")
    plt.fill_between(
        df["segment"],
        df["mean_re"] - df["std_re"],
        df["mean_re"] + df["std_re"],
        alpha=0.3, color="steelblue",
    )
    plt.plot(df["segment"], df["p95_re"], marker="s", linestyle="--",
             label="95th percentile RE", color="darkorange")
    plt.xlabel("Time Segment")
    plt.ylabel("Reconstruction Error")
    plt.title("Reconstruction Error Evolution Over Time (Temporal Drift Analysis)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "temporal_re_evolution.png"), dpi=300)
    plt.close()

    df.to_csv(os.path.join(output_dir, "temporal_re_evolution.csv"), index=False)
    print(f"  Temporal drift analysis saved → {output_dir}")
    return df


# ─────────────────────────────────────────────
#  4. Full temporal evaluation runner
# ─────────────────────────────────────────────

def run_temporal_evaluation(
    autoencoder,
    xgb_model,
    preprocessor,
    X_raw: pd.DataFrame,
    y_raw: pd.Series,
    timestamps: pd.Series | None,
    label_encoder,
    threshold: float,
    output_dir: str,
    random_metrics: dict | None = None,
) -> dict:
    """
    Run the complete temporal evaluation experiment.

    Steps:
      1. Create temporal splits
      2. Apply preprocessing (fit on temporal train, transform val/test)
      3. Evaluate autoencoder and XGBoost on temporal test set
      4. Compare with random split metrics
      5. Analyse temporal drift

    Returns
    -------
    dict with all temporal evaluation results
    """
    from hybrid_ids.anomaly_detection import calculate_reconstruction_error, detect_anomalies
    from evaluation.metrics import compute_binary_metrics, compute_multiclass_metrics

    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("TEMPORAL EVALUATION (Experiment B)")
    print("=" * 60)

    # Create temporal splits
    splits = create_temporal_splits(X_raw, y_raw, timestamps)

    # Preprocess
    X_tr_raw = splits["X_train"]
    X_v_raw  = splits["X_val"]
    X_te_raw = splits["X_test"]

    # Re-fit preprocessor on temporal training data
    print("\n  Re-fitting preprocessor on temporal training data...")
    X_tr_proc = preprocessor.fit_transform(X_tr_raw)
    X_v_proc  = preprocessor.transform(X_v_raw)
    X_te_proc = preprocessor.transform(X_te_raw)

    # Encode labels
    le_temporal = LabelEncoder()
    y_tr_enc = le_temporal.fit_transform(splits["y_train"])
    y_v_enc  = le_temporal.transform(splits["y_val"])    if set(splits["y_val"].unique()).issubset(le_temporal.classes_) else splits["y_val"].values
    y_te_enc = le_temporal.transform(splits["y_test"])   if set(splits["y_test"].unique()).issubset(le_temporal.classes_) else splits["y_test"].values

    # AE evaluation
    te_errors = calculate_reconstruction_error(autoencoder, X_te_proc.astype(np.float32))
    benign_label = next(
        (c for c in le_temporal.classes_ if c.upper() in ("BENIGN", "NORMAL")),
        le_temporal.classes_[0],
    )
    benign_idx    = list(le_temporal.classes_).index(benign_label)
    y_te_binary   = (y_te_enc != benign_idx).astype(int)
    ae_preds      = detect_anomalies(te_errors, threshold)
    ae_metrics    = compute_binary_metrics(y_te_binary, ae_preds)

    # XGBoost evaluation
    xgb_preds_te  = xgb_model.predict(X_te_proc.astype(np.float32))
    xgb_metrics   = compute_multiclass_metrics(y_te_enc, xgb_preds_te)

    temporal_metrics = {
        "accuracy":            ae_metrics["accuracy"],
        "f1_weighted":         xgb_metrics["f1_weighted"],
        "f1_macro":            xgb_metrics["f1_macro"],
        "precision_weighted":  xgb_metrics["precision_weighted"],
        "recall_weighted":     xgb_metrics["recall_weighted"],
        "fpr":                 ae_metrics["fpr"],
        "fnr":                 ae_metrics["fnr"],
    }

    results = {
        "method":           splits["method"],
        "train_period":     splits["train_period"],
        "val_period":       splits["val_period"],
        "test_period":      splits["test_period"],
        "n_train":          len(X_tr_raw),
        "n_val":            len(X_v_raw),
        "n_test":           len(X_te_raw),
        "ae_metrics":       ae_metrics,
        "xgb_metrics":      {k: v for k, v in xgb_metrics.items() if not isinstance(v, dict)},
        "temporal_metrics": temporal_metrics,
    }

    if random_metrics:
        results["vs_random"] = compare_temporal_vs_random(
            random_metrics, temporal_metrics, output_dir
        )

    # Save
    with open(os.path.join(output_dir, "temporal_evaluation_results.json"), "w") as f:
        json.dump(results, f, indent=4, default=str)

    print(f"\n  Temporal evaluation complete → {output_dir}")
    return results
