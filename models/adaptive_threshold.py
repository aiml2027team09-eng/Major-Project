"""
models/adaptive_threshold.py
=============================
Adaptive anomaly thresholding for the Hybrid IDS.

Implements:
  Method 1 — Fixed percentile threshold (baseline)
  Method 2a — Statistical adaptive threshold: T = μ + k*σ
  Method 2b — Sliding-window percentile threshold
  Method 3  — Validation-tuned percentile (existing approach, extended)

All methods accept only benign reconstruction errors for estimation
to prevent threshold pollution by anomalous traffic.

Mathematical formulation
------------------------
Given a window W of recent benign reconstruction errors:

  Statistical:
    T_t = μ_W + k * σ_W

  Percentile:
    T_t = percentile(E_W, q)

  Combined (used as default):
    T_t = max(statistical_T, percentile_T)   ← more conservative

Concept drift:
  When distribution shift is detected, the adaptive threshold
  recalculates from the new benign baseline WITHOUT incorporating
  confirmed attack traffic.
"""

from __future__ import annotations

import json
import os
import warnings
from collections import deque
from typing import Callable

import numpy as np
from scipy import stats


# ─────────────────────────────────────────────
#  Default hyper-parameters
# ─────────────────────────────────────────────

DEFAULT_K = 3.0          # σ multiplier for statistical threshold
DEFAULT_PERCENTILE = 97.5  # percentile for percentile threshold
WINDOW_SIZE = 500        # number of recent benign errors in sliding window
K_CANDIDATES = [2.0, 2.5, 3.0, 3.5, 4.0]
Q_CANDIDATES = [95.0, 97.5, 99.0, 99.5]


# ─────────────────────────────────────────────
#  1. Fixed threshold (baseline)
# ─────────────────────────────────────────────

def fixed_percentile_threshold(
    normal_errors: np.ndarray,
    percentile: float = 99.0,
) -> float:
    """
    Fixed validation-derived threshold.

    T = percentile(normal_errors, q)

    Parameters
    ----------
    normal_errors : reconstruction errors from benign training traffic
    percentile    : desired percentile (default 99th)

    Returns
    -------
    float threshold
    """
    t = float(np.percentile(normal_errors, percentile))
    print(f"  [Fixed] T = percentile({percentile}%) = {t:.6f}")
    return t


# ─────────────────────────────────────────────
#  2a. Statistical adaptive threshold: T = μ + k*σ
# ─────────────────────────────────────────────

def statistical_threshold(
    normal_errors: np.ndarray,
    k: float = DEFAULT_K,
) -> float:
    """
    T = μ + k * σ

    Parameters
    ----------
    normal_errors : reconstruction errors from benign traffic ONLY
    k             : sensitivity parameter (typical range 2–4)

    Returns
    -------
    float threshold

    Notes
    -----
    k = 3 corresponds roughly to the 99.7th percentile under Gaussian
    assumption, but this method is distribution-free because it uses
    the empirical μ and σ rather than a parametric model.
    """
    mu  = float(np.mean(normal_errors))
    sig = float(np.std(normal_errors))
    t   = mu + k * sig
    print(f"  [Statistical] μ={mu:.6f}  σ={sig:.6f}  k={k}  T={t:.6f}")
    return t


# ─────────────────────────────────────────────
#  2b. Percentile-based adaptive threshold
# ─────────────────────────────────────────────

def percentile_threshold(
    normal_errors: np.ndarray,
    q: float = DEFAULT_PERCENTILE,
) -> float:
    """
    T = percentile(E_recent, q)

    Parameters
    ----------
    normal_errors : benign reconstruction errors (recent window)
    q             : percentile (e.g. 95, 97.5, 99)
    """
    t = float(np.percentile(normal_errors, q))
    print(f"  [Percentile] q={q}%  T={t:.6f}")
    return t


# ─────────────────────────────────────────────
#  3. Validation-tuned adaptive threshold
# ─────────────────────────────────────────────

def tune_adaptive_threshold(
    normal_errors: np.ndarray,
    validation_errors: np.ndarray,
    y_val_binary: np.ndarray,
    method: str = "combined",
) -> dict:
    """
    Tune k and q parameters on the validation set.

    Tries multiple k and q candidates, picks the combination
    maximising F1 score while satisfying precision >= 0.85.

    Parameters
    ----------
    normal_errors      : benign training reconstruction errors
    validation_errors  : validation set reconstruction errors
    y_val_binary       : binary labels for validation (0=normal, 1=attack)
    method             : "statistical" | "percentile" | "combined"

    Returns
    -------
    dict with best_threshold, best_k, best_q, metrics, method
    """
    from sklearn.metrics import f1_score, precision_score, recall_score

    best = None

    for k in K_CANDIDATES:
        for q in Q_CANDIDATES:
            stat_t = statistical_threshold(normal_errors, k)
            perc_t = percentile_threshold(normal_errors, q)

            if method == "statistical":
                t = stat_t
            elif method == "percentile":
                t = perc_t
            else:  # combined — more conservative
                t = max(stat_t, perc_t)

            preds = (validation_errors > t).astype(int)
            prec  = float(precision_score(y_val_binary, preds, zero_division=0))
            rec   = float(recall_score(y_val_binary, preds, zero_division=0))
            f1    = float(f1_score(y_val_binary, preds, zero_division=0))

            candidate = {
                "threshold": t,
                "k": k,
                "q": q,
                "precision": prec,
                "recall":    rec,
                "f1":        f1,
                "method":    method,
            }

            if prec >= 0.85:
                if best is None or f1 > best["f1"]:
                    best = candidate
            elif best is None:
                best = candidate  # fallback: best unconstrained

    print(f"\n  [Adaptive Tuned] Best threshold = {best['threshold']:.6f}")
    print(f"  k={best['k']}  q={best['q']}%  precision={best['precision']:.4f}"
          f"  recall={best['recall']:.4f}  f1={best['f1']:.4f}")

    return best


# ─────────────────────────────────────────────
#  4. Online sliding-window adaptive threshold
# ─────────────────────────────────────────────

class SlidingWindowThreshold:
    """
    Online adaptive threshold for live monitoring.

    Maintains a FIFO queue of recent benign reconstruction errors
    and recomputes the threshold after each update.

    Only errors from flows that were NOT flagged as anomalous are
    admitted to the window (contamination prevention).

    Usage
    -----
    swt = SlidingWindowThreshold(window_size=500, k=3.0, q=97.5)
    swt.initialize(initial_normal_errors)

    For each new flow:
        threshold = swt.current_threshold
        is_anomaly = reconstruction_error > threshold
        if not is_anomaly:
            swt.update(reconstruction_error)
    """

    def __init__(
        self,
        window_size: int = WINDOW_SIZE,
        k: float = DEFAULT_K,
        q: float = DEFAULT_PERCENTILE,
        method: str = "combined",
    ):
        self.window_size = window_size
        self.k = k
        self.q = q
        self.method = method
        self._window: deque = deque(maxlen=window_size)
        self._threshold: float | None = None

    def initialize(self, seed_errors: np.ndarray) -> float:
        """Seed the window with initial benign errors."""
        # Take the most recent window_size samples
        seed = np.asarray(seed_errors).ravel()[-self.window_size:]
        for e in seed:
            self._window.append(float(e))
        self._recompute()
        return self._threshold  # type: ignore[return-value]

    def update(self, error: float) -> None:
        """Add a confirmed benign reconstruction error to the window."""
        self._window.append(float(error))
        self._recompute()

    def _recompute(self) -> None:
        arr = np.array(self._window)
        if len(arr) < 10:
            return  # not enough data yet

        stat_t = float(np.mean(arr)) + self.k * float(np.std(arr))
        perc_t = float(np.percentile(arr, self.q))

        if self.method == "statistical":
            self._threshold = stat_t
        elif self.method == "percentile":
            self._threshold = perc_t
        else:
            self._threshold = max(stat_t, perc_t)

    @property
    def current_threshold(self) -> float:
        if self._threshold is None:
            raise RuntimeError("Call initialize() before using the threshold.")
        return self._threshold

    @property
    def window_stats(self) -> dict:
        arr = np.array(self._window)
        return {
            "window_size": len(arr),
            "mean": float(np.mean(arr)) if len(arr) > 0 else 0.0,
            "std":  float(np.std(arr))  if len(arr) > 0 else 0.0,
            "threshold": self._threshold,
        }


# ─────────────────────────────────────────────
#  5. Compare thresholds experimentally
# ─────────────────────────────────────────────

def compare_all_thresholds(
    normal_errors: np.ndarray,
    test_errors: np.ndarray,
    y_test_binary: np.ndarray,
    output_dir: str | None = None,
) -> pd.DataFrame:
    """
    Compare Fixed, Statistical, Percentile, and Combined thresholds
    on the test set. Returns a DataFrame of comparison results.
    """
    import pandas as pd
    from sklearn.metrics import f1_score, precision_score, recall_score

    results = []

    configs = [
        ("Fixed-99", fixed_percentile_threshold(normal_errors, 99.0)),
        ("Fixed-97.5", fixed_percentile_threshold(normal_errors, 97.5)),
        ("Stat-k2.5", statistical_threshold(normal_errors, 2.5)),
        ("Stat-k3.0", statistical_threshold(normal_errors, 3.0)),
        ("Stat-k3.5", statistical_threshold(normal_errors, 3.5)),
        ("Perc-95", percentile_threshold(normal_errors, 95.0)),
        ("Perc-97.5", percentile_threshold(normal_errors, 97.5)),
        ("Perc-99", percentile_threshold(normal_errors, 99.0)),
    ]

    for name, t in configs:
        preds = (test_errors > t).astype(int)
        prec  = float(precision_score(y_test_binary, preds, zero_division=0))
        rec   = float(recall_score(y_test_binary, preds, zero_division=0))
        f1    = float(f1_score(y_test_binary, preds, zero_division=0))

        # FPR and FNR
        from evaluation.metrics import compute_binary_metrics
        m = compute_binary_metrics(y_test_binary, preds)

        results.append({
            "method":    name,
            "threshold": t,
            "precision": prec,
            "recall":    rec,
            "f1":        f1,
            "fpr":       m["fpr"],
            "fnr":       m["fnr"],
        })

    df = pd.DataFrame(results)

    print("\n=== Threshold Comparison ===")
    print(df.to_string(index=False, float_format="{:.4f}".format))

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(os.path.join(output_dir, "threshold_comparison.csv"), index=False)
        _plot_threshold_comparison(df, output_dir)

    return df


def _plot_threshold_comparison(df, output_dir: str) -> None:
    """Plot FPR vs Recall for each threshold method."""
    try:
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        ax = axes[0]
        ax.bar(df["method"], df["fpr"], color="salmon", edgecolor="black")
        ax.set_title("False Positive Rate by Threshold Method")
        ax.set_ylabel("FPR")
        ax.set_xlabel("Method")
        ax.tick_params(axis="x", rotation=45)

        ax = axes[1]
        ax.bar(df["method"], df["recall"], color="steelblue", edgecolor="black")
        ax.set_title("Recall (Attack Detection Rate) by Threshold Method")
        ax.set_ylabel("Recall")
        ax.set_xlabel("Method")
        ax.tick_params(axis="x", rotation=45)

        plt.tight_layout()
        plt.savefig(
            os.path.join(output_dir, "threshold_comparison.png"), dpi=300
        )
        plt.close()
    except Exception as e:
        warnings.warn(f"Could not plot threshold comparison: {e}")


# ─────────────────────────────────────────────
#  6. Save threshold to JSON
# ─────────────────────────────────────────────

def save_threshold(threshold_info: dict, output_path: str) -> None:
    """Persist threshold metadata to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(threshold_info, f, indent=4)
    print(f"  Threshold saved → {output_path}")
