"""
evaluation/metrics.py
=====================
Full metrics suite for the Hybrid IDS evaluation.

Covers:
- Accuracy, Precision, Recall, F1 (weighted + macro)
- False Positive Rate (FPR), False Negative Rate (FNR)
- ROC-AUC, PR-AUC  (binary & multi-class OvR)
- Per-class metrics
- Anomaly-detection specific metrics
- Confusion matrix generation
- Detection latency / throughput helpers
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    auc,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


# ─────────────────────────────────────────────
#  Binary anomaly-detection metrics
# ─────────────────────────────────────────────

def compute_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Compute core binary classification metrics.

    Parameters
    ----------
    y_true : 1-D array-like of {0, 1}  (0=normal, 1=anomaly/attack)
    y_pred : 1-D array-like of {0, 1}

    Returns
    -------
    dict with keys: accuracy, precision, recall, f1,
                    fpr, fnr, tp, fp, tn, fn
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    acc  = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec  = float(recall_score(y_true, y_pred, zero_division=0))
    f1   = float(f1_score(y_true, y_pred, zero_division=0))

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    # Handle case where only one class exists
    if cm.shape == (1, 1):
        if y_true[0] == 0:
            tn, fp, fn, tp = int(cm[0, 0]), 0, 0, 0
        else:
            tn, fp, fn, tp = 0, 0, 0, int(cm[0, 0])
    else:
        tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]

    normal_total = tn + fp
    attack_total = fn + tp

    fpr = float(fp / normal_total) if normal_total > 0 else 0.0
    fnr = float(fn / attack_total) if attack_total > 0 else 0.0

    return {
        "accuracy":  acc,
        "precision": prec,
        "recall":    rec,
        "f1":        f1,
        "fpr":       fpr,
        "fnr":       fnr,
        "tp":        int(tp),
        "fp":        int(fp),
        "tn":        int(tn),
        "fn":        int(fn),
    }


def compute_roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> dict:
    """
    Compute ROC curve and AUC for binary anomaly detection.

    Parameters
    ----------
    y_true  : 1-D array of {0, 1}
    y_score : 1-D array of continuous anomaly scores (e.g. reconstruction error)

    Returns
    -------
    dict with roc_auc, fpr_curve, tpr_curve, pr_auc
    """
    y_true  = np.asarray(y_true)
    y_score = np.asarray(y_score)

    try:
        roc_auc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        roc_auc = float("nan")

    try:
        pr_auc = float(average_precision_score(y_true, y_score))
    except ValueError:
        pr_auc = float("nan")

    fpr_c, tpr_c, _ = roc_curve(y_true, y_score)
    prec_c, rec_c, _ = precision_recall_curve(y_true, y_score)

    return {
        "roc_auc":    roc_auc,
        "pr_auc":     pr_auc,
        "fpr_curve":  fpr_c.tolist(),
        "tpr_curve":  tpr_c.tolist(),
        "prec_curve": prec_c.tolist(),
        "rec_curve":  rec_c.tolist(),
    }


# ─────────────────────────────────────────────
#  Multi-class classification metrics
# ─────────────────────────────────────────────

def compute_multiclass_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str] | None = None,
    y_prob: np.ndarray | None = None,
) -> dict:
    """
    Full multi-class metric suite.

    Parameters
    ----------
    y_true      : integer-encoded ground truth labels
    y_pred      : integer-encoded predictions
    class_names : optional list of string class names
    y_prob      : (N, C) probability matrix for ROC-AUC OvR

    Returns
    -------
    dict with macro/weighted F1, per-class metrics, ROC-AUC OvR
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    acc         = float(accuracy_score(y_true, y_pred))
    prec_w      = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    rec_w       = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    f1_w        = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    f1_macro    = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    prec_macro  = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec_macro   = float(recall_score(y_true, y_pred, average="macro", zero_division=0))

    # Per-class report
    labels = sorted(np.unique(np.concatenate([y_true, y_pred])))
    target_names = [class_names[i] for i in labels] if class_names else None
    report = classification_report(
        y_true, y_pred,
        labels=labels,
        target_names=target_names,
        zero_division=0,
        output_dict=True,
    )

    # Multi-class ROC-AUC (OvR)
    roc_auc_ovr = None
    if y_prob is not None:
        try:
            roc_auc_ovr = float(
                roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro")
            )
        except ValueError:
            roc_auc_ovr = float("nan")

    return {
        "accuracy":           acc,
        "precision_weighted": prec_w,
        "recall_weighted":    rec_w,
        "f1_weighted":        f1_w,
        "f1_macro":           f1_macro,
        "precision_macro":    prec_macro,
        "recall_macro":       rec_macro,
        "roc_auc_ovr":        roc_auc_ovr,
        "per_class_report":   report,
    }


# ─────────────────────────────────────────────
#  FPR control: fixed vs adaptive threshold
# ─────────────────────────────────────────────

def compare_thresholds(
    y_binary_true: np.ndarray,
    reconstruction_errors: np.ndarray,
    fixed_threshold: float,
    adaptive_threshold: float,
) -> dict:
    """
    Compare fixed vs adaptive threshold on FPR / recall trade-off.

    Returns dict with metrics for both and delta.
    """
    fixed_pred    = (reconstruction_errors > fixed_threshold).astype(int)
    adaptive_pred = (reconstruction_errors > adaptive_threshold).astype(int)

    fixed_m    = compute_binary_metrics(y_binary_true, fixed_pred)
    adaptive_m = compute_binary_metrics(y_binary_true, adaptive_pred)

    return {
        "fixed_threshold":    fixed_threshold,
        "adaptive_threshold": adaptive_threshold,
        "fixed":              fixed_m,
        "adaptive":           adaptive_m,
        "fpr_delta":          adaptive_m["fpr"] - fixed_m["fpr"],
        "recall_delta":       adaptive_m["recall"] - fixed_m["recall"],
        "f1_delta":           adaptive_m["f1"] - fixed_m["f1"],
    }


# ─────────────────────────────────────────────
#  Latency and throughput helpers
# ─────────────────────────────────────────────

class LatencyTracker:
    """Context manager to measure inference latency for N samples."""

    def __init__(self, n_samples: int):
        self.n_samples = n_samples
        self._start = 0.0
        self.elapsed_ms = 0.0
        self.throughput_fps = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = time.perf_counter() - self._start
        self.elapsed_ms = elapsed * 1000
        self.throughput_fps = self.n_samples / elapsed if elapsed > 0 else float("inf")


def measure_inference_latency(
    model_fn,
    X: np.ndarray,
    n_repeats: int = 5,
) -> dict:
    """
    Measure mean and std inference latency over n_repeats runs.

    Parameters
    ----------
    model_fn  : callable that accepts X and returns predictions
    X         : input array (N, features)
    n_repeats : number of timing repetitions

    Returns
    -------
    dict with mean_ms, std_ms, throughput_fps
    """
    times = []
    n = len(X)
    for _ in range(n_repeats):
        t0 = time.perf_counter()
        _ = model_fn(X)
        times.append(time.perf_counter() - t0)

    mean_s = float(np.mean(times))
    std_s  = float(np.std(times))

    return {
        "mean_ms":        mean_s * 1000,
        "std_ms":         std_s * 1000,
        "throughput_fps": n / mean_s if mean_s > 0 else float("inf"),
        "n_samples":      n,
        "n_repeats":      n_repeats,
    }


# ─────────────────────────────────────────────
#  Severity scoring
# ─────────────────────────────────────────────

SEVERITY_RULES: dict[str, dict] = {
    "CRITICAL": {
        "confidence_min": 0.90,
        "reconstruction_error_multiplier": 3.0,
        "attack_classes": ["DDoS", "DoS", "Bot"],
    },
    "HIGH": {
        "confidence_min": 0.75,
        "reconstruction_error_multiplier": 2.0,
        "attack_classes": ["Brute Force", "Infiltration", "Web Attack"],
    },
    "MEDIUM": {
        "confidence_min": 0.50,
        "reconstruction_error_multiplier": 1.5,
        "attack_classes": [],
    },
    "LOW": {
        "confidence_min": 0.0,
        "reconstruction_error_multiplier": 1.0,
        "attack_classes": [],
    },
}


def compute_severity(
    predicted_class: str,
    confidence: float,
    reconstruction_error: float,
    threshold: float,
) -> str:
    """
    Assign severity level to a detected attack alert.

    Rules (applied in order — first match wins):
    - CRITICAL: confidence >= 0.90 AND error >= 3 * threshold,
                OR class in critical list
    - HIGH    : confidence >= 0.75 AND error >= 2 * threshold,
                OR class in high list
    - MEDIUM  : confidence >= 0.50 OR error >= 1.5 * threshold
    - LOW     : everything else

    Returns
    -------
    str : "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    """
    re_ratio = reconstruction_error / threshold if threshold > 0 else 1.0

    for level, rule in SEVERITY_RULES.items():
        class_match = any(
            ac.lower() in predicted_class.lower()
            for ac in rule["attack_classes"]
        )
        if class_match:
            return level
        if (
            confidence >= rule["confidence_min"]
            and re_ratio >= rule["reconstruction_error_multiplier"]
        ):
            return level

    return "LOW"


# ─────────────────────────────────────────────
#  Utility: pretty-print metric dict
# ─────────────────────────────────────────────

def print_metrics(metrics: dict, title: str = "Metrics") -> None:
    """Pretty-print a flat metrics dictionary."""
    width = 60
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)
    for k, v in metrics.items():
        if isinstance(v, float):
            print(f"  {k:<30s}: {v:.4f}")
        elif isinstance(v, int):
            print(f"  {k:<30s}: {v}")
        elif isinstance(v, dict):
            pass  # skip nested dicts in summary print
        else:
            print(f"  {k:<30s}: {v}")
    print("=" * width)
