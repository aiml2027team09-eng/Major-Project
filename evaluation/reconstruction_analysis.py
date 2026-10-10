"""
evaluation/reconstruction_analysis.py
======================================
Reconstruction error analysis module.

Generates:
  - Histogram of reconstruction errors (benign vs attack)
  - KDE/distribution overlay plot
  - ROC curve for anomaly detection
  - Precision-Recall curve
  - Threshold-performance curve (Precision, Recall, F1 vs threshold)
  - Error statistics by class (known + unseen)
"""

from __future__ import annotations

import os
import warnings

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
    f1_score,
    precision_score,
    recall_score,
)


# ─────────────────────────────────────────────
#  1. Compute reconstruction errors from autoencoder
# ─────────────────────────────────────────────

def compute_errors(autoencoder, X: np.ndarray, batch_size: int = 512) -> np.ndarray:
    """Per-sample MSE reconstruction error."""
    X = np.asarray(X, dtype=np.float32)
    X_hat = autoencoder.predict(X, batch_size=batch_size, verbose=0)
    return np.mean(np.square(X - X_hat), axis=1)


# ─────────────────────────────────────────────
#  2. Error statistics summary
# ─────────────────────────────────────────────

def error_statistics(
    errors_dict: dict[str, np.ndarray],
) -> pd.DataFrame:
    """
    Compute statistics for each group of reconstruction errors.

    Parameters
    ----------
    errors_dict : dict mapping group name → 1-D error array
                  e.g. {"Benign": ..., "DDoS": ..., "Unseen-Infiltration": ...}

    Returns
    -------
    DataFrame with columns: group, mean, std, min, p25, p50, p75, p95, p99, max
    """
    rows = []
    for group, errs in errors_dict.items():
        errs = np.asarray(errs)
        rows.append({
            "group": group,
            "count": len(errs),
            "mean":  float(np.mean(errs)),
            "std":   float(np.std(errs)),
            "min":   float(np.min(errs)),
            "p25":   float(np.percentile(errs, 25)),
            "p50":   float(np.percentile(errs, 50)),
            "p75":   float(np.percentile(errs, 75)),
            "p95":   float(np.percentile(errs, 95)),
            "p99":   float(np.percentile(errs, 99)),
            "max":   float(np.max(errs)),
        })
    df = pd.DataFrame(rows)
    print("\n=== Reconstruction Error Statistics ===")
    print(df.to_string(index=False, float_format="{:.6f}".format))
    return df


# ─────────────────────────────────────────────
#  3. Histogram + KDE overlay
# ─────────────────────────────────────────────

def plot_error_distributions(
    errors_dict: dict[str, np.ndarray],
    threshold: float,
    output_path: str,
    log_scale: bool = True,
    clip_percentile: float = 99.5,
) -> None:
    """
    Plot overlapping histograms + KDE of reconstruction errors.

    Parameters
    ----------
    errors_dict      : dict mapping group label → error array
    threshold        : vertical line showing anomaly decision boundary
    output_path      : path to save figure (.png)
    log_scale        : use log x-axis for better visibility
    clip_percentile  : clip x-axis to this percentile to remove outliers
    """
    try:
        from scipy.stats import gaussian_kde
        has_scipy = True
    except ImportError:
        has_scipy = False

    all_errors = np.concatenate(list(errors_dict.values()))
    x_max = float(np.percentile(all_errors, clip_percentile))

    colors = plt.cm.tab10.colors
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # --- Linear scale histogram ---
    ax = axes[0]
    for i, (label, errs) in enumerate(errors_dict.items()):
        clipped = errs[errs <= x_max]
        ax.hist(
            clipped,
            bins=80,
            alpha=0.5,
            label=label,
            color=colors[i % len(colors)],
            density=True,
        )
    ax.axvline(threshold, color="red", linestyle="--", linewidth=2,
               label=f"Threshold = {threshold:.4f}")
    ax.set_xlabel("Reconstruction Error (MSE)")
    ax.set_ylabel("Density")
    ax.set_title("Reconstruction Error Distribution")
    ax.legend(fontsize=8)
    ax.set_xlim(0, x_max)

    # --- Log scale + KDE ---
    ax = axes[1]
    for i, (label, errs) in enumerate(errors_dict.items()):
        if log_scale:
            errs_pos = errs[errs > 1e-10]
            log_errs = np.log10(errs_pos + 1e-10)
            ax.hist(log_errs, bins=80, alpha=0.4,
                    label=label, color=colors[i % len(colors)], density=True)
        else:
            clipped = errs[errs <= x_max]
            ax.hist(clipped, bins=80, alpha=0.4,
                    label=label, color=colors[i % len(colors)], density=True)
            if has_scipy and len(clipped) > 10:
                kde = gaussian_kde(clipped)
                xs = np.linspace(0, x_max, 300)
                ax.plot(xs, kde(xs), color=colors[i % len(colors)], linewidth=2)

    if log_scale:
        ax.axvline(
            np.log10(threshold + 1e-10),
            color="red", linestyle="--", linewidth=2,
            label=f"Threshold (log10={np.log10(threshold + 1e-10):.2f})",
        )
        ax.set_xlabel("log10(Reconstruction Error + ε)")
    else:
        ax.axvline(threshold, color="red", linestyle="--", linewidth=2,
                   label=f"Threshold = {threshold:.4f}")
        ax.set_xlabel("Reconstruction Error (MSE)")

    ax.set_ylabel("Density")
    ax.set_title("Error Distribution (Log Scale)" if log_scale else "Error Distribution + KDE")
    ax.legend(fontsize=8)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Saved: {output_path}")


# ─────────────────────────────────────────────
#  4. ROC curve
# ─────────────────────────────────────────────

def plot_roc_curve(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float,
    output_path: str,
    title: str = "Autoencoder Anomaly Detection ROC Curve",
) -> dict:
    """
    Plot ROC curve and return AUC.

    Parameters
    ----------
    y_true     : binary labels (0=normal, 1=attack)
    y_score    : reconstruction errors (higher = more anomalous)
    threshold  : operating point to mark on the curve
    output_path: save path (.png)
    """
    y_true  = np.asarray(y_true)
    y_score = np.asarray(y_score)

    fpr, tpr, thresholds = roc_curve(y_true, y_score)

    try:
        roc_auc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        roc_auc = float("nan")

    # Find operating point
    op_pred = (y_score > threshold).astype(int)
    op_fpr  = float(np.mean(op_pred[y_true == 0])) if (y_true == 0).sum() > 0 else 0.0
    op_tpr  = float(np.mean(op_pred[y_true == 1])) if (y_true == 1).sum() > 0 else 0.0

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color="darkorange", lw=2,
             label=f"ROC Curve (AUC = {roc_auc:.4f})")
    plt.scatter([op_fpr], [op_tpr], color="red", zorder=5, s=80,
                label=f"Operating Point (T={threshold:.4f})")
    plt.plot([0, 1], [0, 1], color="navy", linestyle="--", lw=1.5, label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  ROC AUC = {roc_auc:.4f} | Saved: {output_path}")

    return {
        "roc_auc":        roc_auc,
        "operating_fpr":  op_fpr,
        "operating_tpr":  op_tpr,
        "fpr_curve":      fpr.tolist(),
        "tpr_curve":      tpr.tolist(),
    }


# ─────────────────────────────────────────────
#  5. Precision-Recall curve
# ─────────────────────────────────────────────

def plot_pr_curve(
    y_true: np.ndarray,
    y_score: np.ndarray,
    output_path: str,
    title: str = "Autoencoder Precision-Recall Curve",
) -> dict:
    """Plot Precision-Recall curve and return PR-AUC."""
    y_true  = np.asarray(y_true)
    y_score = np.asarray(y_score)

    prec, rec, _ = precision_recall_curve(y_true, y_score)

    try:
        pr_auc = float(average_precision_score(y_true, y_score))
    except ValueError:
        pr_auc = float("nan")

    baseline = float(y_true.mean())  # random classifier PR-AUC

    plt.figure(figsize=(8, 6))
    plt.plot(rec, prec, color="steelblue", lw=2,
             label=f"PR Curve (AP = {pr_auc:.4f})")
    plt.axhline(baseline, color="gray", linestyle="--", lw=1.5,
                label=f"Random ({baseline:.4f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  PR AUC = {pr_auc:.4f} | Saved: {output_path}")

    return {"pr_auc": pr_auc, "baseline": baseline}


# ─────────────────────────────────────────────
#  6. Threshold-performance curve
# ─────────────────────────────────────────────

def plot_threshold_performance_curve(
    y_true: np.ndarray,
    y_score: np.ndarray,
    output_path: str,
    n_steps: int = 200,
) -> None:
    """
    Plot Precision, Recall, and F1 vs threshold.
    Highlights the chosen optimal F1 point.
    """
    y_true  = np.asarray(y_true)
    y_score = np.asarray(y_score)

    percentiles = np.linspace(50, 99.9, n_steps)
    thresholds  = np.unique(np.percentile(y_score, percentiles))

    precisions, recalls, f1_scores = [], [], []

    for t in thresholds:
        preds = (y_score > t).astype(int)
        precisions.append(float(precision_score(y_true, preds, zero_division=0)))
        recalls.append(float(recall_score(y_true, preds, zero_division=0)))
        f1_scores.append(float(f1_score(y_true, preds, zero_division=0)))

    best_idx = int(np.argmax(f1_scores))
    best_t   = thresholds[best_idx]

    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, precisions, label="Precision", color="blue")
    plt.plot(thresholds, recalls,    label="Recall",    color="green")
    plt.plot(thresholds, f1_scores,  label="F1 Score",  color="orange", linewidth=2)
    plt.axvline(best_t, color="red", linestyle="--", linewidth=1.5,
                label=f"Best F1 @ T={best_t:.4f}")
    plt.xlabel("Threshold")
    plt.ylabel("Score")
    plt.title("Threshold-Performance Curve")
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Best F1 = {f1_scores[best_idx]:.4f} @ T = {best_t:.4f}")
    print(f"  Saved: {output_path}")


# ─────────────────────────────────────────────
#  7. Full analysis pipeline
# ─────────────────────────────────────────────

def run_full_reconstruction_analysis(
    autoencoder,
    data_splits: dict[str, np.ndarray],
    label_splits: dict[str, np.ndarray],
    label_encoder,
    threshold: float,
    output_dir: str,
    batch_size: int = 512,
) -> dict:
    """
    Run complete reconstruction error analysis.

    Parameters
    ----------
    autoencoder  : trained Keras autoencoder model
    data_splits  : dict of {split_name: X_np}, e.g.
                   {"normal_train": X_n, "validation": X_v, "test": X_t}
    label_splits : dict of {split_name: y_array} for labeled splits
    label_encoder: fitted LabelEncoder
    threshold    : current anomaly threshold
    output_dir   : directory to save all plots and CSVs

    Returns
    -------
    dict of all computed metrics and paths
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    # Compute errors for all splits
    errors_by_split = {}
    for split_name, X in data_splits.items():
        print(f"  Computing reconstruction errors for: {split_name}")
        errors_by_split[split_name] = compute_errors(autoencoder, X, batch_size)

    # Error statistics
    stats_df = error_statistics(errors_by_split)
    stats_df.to_csv(os.path.join(output_dir, "error_statistics.csv"), index=False)

    # Group by class for test set
    if "test" in errors_by_split and "test" in label_splits:
        y_test  = label_splits["test"]
        e_test  = errors_by_split["test"]
        classes = label_encoder.classes_

        per_class_errors = {}
        for idx, cls in enumerate(classes):
            mask = y_test == idx
            if mask.sum() > 0:
                per_class_errors[cls] = e_test[mask]

        # Separate benign vs attacks for binary analysis
        benign_label = next(
            (c for c in classes if c.upper() in ("BENIGN", "NORMAL")), classes[0]
        )
        benign_idx   = list(classes).index(benign_label)
        benign_mask  = y_test == benign_idx
        attack_mask  = ~benign_mask
        y_binary     = attack_mask.astype(int)

        results["per_class_stats"] = error_statistics(per_class_errors)

        plot_error_distributions(
            {k: v for k, v in per_class_errors.items()},
            threshold,
            os.path.join(output_dir, "error_distribution_by_class.png"),
        )

        results["roc"] = plot_roc_curve(
            y_binary, e_test, threshold,
            os.path.join(output_dir, "roc_curve.png"),
        )

        results["pr"] = plot_pr_curve(
            y_binary, e_test,
            os.path.join(output_dir, "pr_curve.png"),
        )

        plot_threshold_performance_curve(
            y_binary, e_test,
            os.path.join(output_dir, "threshold_performance.png"),
        )

    # Benign vs all-attacks (simple)
    if "normal_train" in errors_by_split and "test" in errors_by_split:
        plot_error_distributions(
            {
                "Benign (train)": errors_by_split["normal_train"],
                "Test (all)":     errors_by_split["test"],
            },
            threshold,
            os.path.join(output_dir, "error_distribution_train_vs_test.png"),
        )

    results["errors_by_split"] = {k: v.tolist() for k, v in errors_by_split.items()}
    return results
