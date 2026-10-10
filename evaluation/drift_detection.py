"""
evaluation/drift_detection.py
==============================
Concept drift / distribution shift detection for the Hybrid IDS.

Implements three drift-detection methods:
  1. Kolmogorov-Smirnov (KS) test
  2. Population Stability Index (PSI)
  3. Jensen-Shannon Divergence (JSD)

When significant drift is detected:
  → Emit "Distribution Shift Warning"
  → Log drift statistics
  → Do NOT auto-retrain without safe validation mechanism

Research contribution
---------------------
Most IDS papers use static thresholds and ignore distribution shift.
This module monitors drift in:
  - Reconstruction error distribution
  - Feature distributions (selected key features)
  - Traffic volume
  - Prediction class distribution

Mathematical formulations
--------------------------
KS statistic:
  D = sup_x |F_1(x) - F_2(x)|
  p-value < 0.05 ⟹ significant drift

PSI:
  PSI = Σ (P_i - Q_i) * ln(P_i / Q_i)
  PSI < 0.1  : stable
  PSI < 0.25 : minor shift
  PSI ≥ 0.25 : major shift

JSD:
  JSD(P‖Q) = ½ KL(P‖M) + ½ KL(Q‖M)  where M = ½(P + Q)
  JSD ∈ [0, 1];  JSD < 0.1 : low drift
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import kl_div


# ─────────────────────────────────────────────
#  Thresholds for drift severity classification
# ─────────────────────────────────────────────

KS_ALPHA = 0.05          # p-value threshold for KS test
PSI_MINOR = 0.10         # PSI below this = stable
PSI_MAJOR = 0.25         # PSI above this = major shift
JSD_MINOR = 0.05         # JSD below this = stable
JSD_MAJOR = 0.15         # JSD above this = major shift


# ─────────────────────────────────────────────
#  1. KS Test
# ─────────────────────────────────────────────

def ks_test(
    reference: np.ndarray,
    current: np.ndarray,
    alpha: float = KS_ALPHA,
) -> dict:
    """
    Kolmogorov-Smirnov two-sample test.

    H0: the two samples come from the same distribution.
    Reject H0 (drift detected) if p-value < alpha.

    Parameters
    ----------
    reference : 1-D array from reference period (e.g. validation set)
    current   : 1-D array from current window
    alpha     : significance level

    Returns
    -------
    dict with statistic, p_value, drift_detected, severity
    """
    reference = np.asarray(reference).ravel()
    current   = np.asarray(current).ravel()

    ks_stat, p_value = stats.ks_2samp(reference, current)
    drift = bool(p_value < alpha)

    severity = "NONE"
    if drift:
        if ks_stat > 0.3:
            severity = "MAJOR"
        elif ks_stat > 0.15:
            severity = "MINOR"
        else:
            severity = "MARGINAL"

    return {
        "method":         "ks_test",
        "statistic":      float(ks_stat),
        "p_value":        float(p_value),
        "alpha":          alpha,
        "drift_detected": drift,
        "severity":       severity,
    }


# ─────────────────────────────────────────────
#  2. Population Stability Index (PSI)
# ─────────────────────────────────────────────

def psi(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
) -> dict:
    """
    Population Stability Index.

    PSI = Σ (actual% - expected%) * ln(actual% / expected%)

    Parameters
    ----------
    reference : 1-D reference array
    current   : 1-D current array
    n_bins    : number of equal-width bins

    Returns
    -------
    dict with psi_value, drift_detected, severity, bin_details
    """
    reference = np.asarray(reference).ravel()
    current   = np.asarray(current).ravel()

    # Build bins from reference distribution
    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bins    = np.linspace(min_val, max_val, n_bins + 1)
    bins[0]  -= 1e-10
    bins[-1] += 1e-10

    ref_counts, _ = np.histogram(reference, bins=bins)
    cur_counts, _ = np.histogram(current,   bins=bins)

    # Avoid division by zero
    ref_pct = ref_counts / ref_counts.sum()
    cur_pct = cur_counts / cur_counts.sum()
    ref_pct = np.where(ref_pct == 0, 1e-4, ref_pct)
    cur_pct = np.where(cur_pct == 0, 1e-4, cur_pct)

    psi_val = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))

    if psi_val < PSI_MINOR:
        severity = "NONE"
        drift    = False
    elif psi_val < PSI_MAJOR:
        severity = "MINOR"
        drift    = True
    else:
        severity = "MAJOR"
        drift    = True

    bin_details = [
        {
            "bin": i,
            "bin_range": [float(bins[i]), float(bins[i + 1])],
            "ref_pct":   float(ref_pct[i]),
            "cur_pct":   float(cur_pct[i]),
            "psi_contrib": float((cur_pct[i] - ref_pct[i]) * np.log(cur_pct[i] / ref_pct[i])),
        }
        for i in range(n_bins)
    ]

    return {
        "method":         "psi",
        "psi_value":      psi_val,
        "threshold_minor": PSI_MINOR,
        "threshold_major": PSI_MAJOR,
        "drift_detected": drift,
        "severity":       severity,
        "bin_details":    bin_details,
    }


# ─────────────────────────────────────────────
#  3. Jensen-Shannon Divergence
# ─────────────────────────────────────────────

def jensen_shannon_divergence(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 50,
) -> dict:
    """
    Jensen-Shannon Divergence (symmetric KL divergence).

    JSD ∈ [0, 1]:
      0   = identical distributions
      1   = completely different distributions
    ln(2) = maximally different (when using natural logarithm)

    Returns
    -------
    dict with jsd_value, drift_detected, severity
    """
    reference = np.asarray(reference).ravel()
    current   = np.asarray(current).ravel()

    min_val = min(reference.min(), current.min())
    max_val = max(reference.max(), current.max())
    bins    = np.linspace(min_val, max_val, n_bins + 1)
    bins[0]  -= 1e-10
    bins[-1] += 1e-10

    P, _ = np.histogram(reference, bins=bins, density=True)
    Q, _ = np.histogram(current,   bins=bins, density=True)

    # Normalize to probability distributions
    P = P / (P.sum() + 1e-10)
    Q = Q / (Q.sum() + 1e-10)

    # Smooth zeros
    P = np.where(P == 0, 1e-10, P)
    Q = np.where(Q == 0, 1e-10, Q)

    M = 0.5 * (P + Q)
    jsd = 0.5 * np.sum(P * np.log(P / M)) + 0.5 * np.sum(Q * np.log(Q / M))
    jsd = float(np.clip(jsd, 0, 1))

    if jsd < JSD_MINOR:
        severity = "NONE"
        drift    = False
    elif jsd < JSD_MAJOR:
        severity = "MINOR"
        drift    = True
    else:
        severity = "MAJOR"
        drift    = True

    return {
        "method":          "jsd",
        "jsd_value":       jsd,
        "threshold_minor": JSD_MINOR,
        "threshold_major": JSD_MAJOR,
        "drift_detected":  drift,
        "severity":        severity,
    }


# ─────────────────────────────────────────────
#  4. Combined drift report
# ─────────────────────────────────────────────

def detect_drift(
    reference: np.ndarray,
    current: np.ndarray,
    feature_name: str = "reconstruction_error",
    output_dir: str | None = None,
) -> dict:
    """
    Run all three drift-detection methods on a 1-D signal.

    Returns a combined drift report and emits a warning if drift is detected.

    Parameters
    ----------
    reference    : baseline distribution (e.g. validation set errors)
    current      : current distribution (e.g. live errors)
    feature_name : name of the signal being tested (for logging)
    output_dir   : if provided, save plots and JSON report
    """
    ks  = ks_test(reference, current)
    psi_r = psi(reference, current)
    jsd_r = jensen_shannon_divergence(reference, current)

    # Majority vote on drift
    votes        = [ks["drift_detected"], psi_r["drift_detected"], jsd_r["drift_detected"]]
    drift_overall = sum(votes) >= 2  # majority

    # Maximum severity
    severity_order = {"NONE": 0, "MARGINAL": 1, "MINOR": 2, "MAJOR": 3}
    severities = [ks["severity"], psi_r["severity"], jsd_r["severity"]]
    overall_severity = max(severities, key=lambda s: severity_order.get(s, 0))

    report = {
        "feature":          feature_name,
        "timestamp":        datetime.now().isoformat(timespec="seconds"),
        "drift_detected":   drift_overall,
        "severity":         overall_severity,
        "votes":            {"ks": ks["drift_detected"], "psi": psi_r["drift_detected"],
                             "jsd": jsd_r["drift_detected"]},
        "ks_test":          ks,
        "psi":              psi_r,
        "jsd":              jsd_r,
        "recommendation":   _drift_recommendation(drift_overall, overall_severity),
    }

    if drift_overall:
        print(f"\n  ⚠️  DISTRIBUTION SHIFT WARNING — {feature_name}")
        print(f"     Severity: {overall_severity}")
        print(f"     KS p={ks['p_value']:.4f}  PSI={psi_r['psi_value']:.4f}  "
              f"JSD={jsd_r['jsd_value']:.4f}")
        print(f"     Recommendation: {report['recommendation']}")
    else:
        print(f"\n  ✓  No significant drift — {feature_name}  "
              f"(KS p={ks['p_value']:.4f}  PSI={psi_r['psi_value']:.4f}  "
              f"JSD={jsd_r['jsd_value']:.4f})")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        safe = feature_name.replace(" ", "_")
        with open(os.path.join(output_dir, f"drift_{safe}.json"), "w") as f:
            # Strip non-serialisable fields
            clean = {k: v for k, v in report.items() if k != "psi"}
            clean["psi"] = {k: v for k, v in psi_r.items() if k != "bin_details"}
            json.dump(clean, f, indent=4)
        _plot_drift(reference, current, report, feature_name,
                    os.path.join(output_dir, f"drift_{safe}.png"))

    return report


def _drift_recommendation(drift: bool, severity: str) -> str:
    if not drift:
        return "No action required. Model is operating in distribution."
    if severity == "MARGINAL":
        return ("Monitor closely. Marginal drift detected — likely normal variation. "
                "Consider adjusting the adaptive threshold window.")
    if severity == "MINOR":
        return ("Recalibrate adaptive threshold using recent benign traffic. "
                "Do NOT retrain model without validation on labeled data.")
    return ("MAJOR DRIFT DETECTED. Suspend automatic reliance on model output. "
            "Collect labeled data, validate model on new distribution before "
            "any retraining. Alert security team.")


def _plot_drift(reference, current, report, feature_name, output_path) -> None:
    """Overlay histogram of reference vs current distribution with drift stats."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    x_all = np.concatenate([reference, current])
    clip  = np.percentile(x_all, 99.5)

    ax = axes[0]
    ax.hist(np.clip(reference, 0, clip), bins=60, alpha=0.6,
            label="Reference", color="steelblue", density=True)
    ax.hist(np.clip(current, 0, clip), bins=60, alpha=0.6,
            label="Current",   color="darkorange", density=True)
    drift_label = "DRIFT DETECTED" if report["drift_detected"] else "No drift"
    ax.set_title(f"{feature_name} — {drift_label} (Severity: {report['severity']})")
    ax.set_xlabel("Value")
    ax.set_ylabel("Density")
    ax.legend()

    ax = axes[1]
    method_names  = ["KS Test\n(stat)", "PSI\nvalue", "JSD\nvalue"]
    method_values = [
        report["ks_test"]["statistic"],
        report["psi"]["psi_value"],
        report["jsd"]["jsd_value"],
    ]
    colors = ["red" if d else "green" for d in [
        report["ks_test"]["drift_detected"],
        report["psi"]["drift_detected"],
        report["jsd"]["drift_detected"],
    ]]
    ax.bar(method_names, method_values, color=colors, edgecolor="black")
    ax.set_title("Drift Statistics by Method")
    ax.set_ylabel("Score")

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


# ─────────────────────────────────────────────
#  5. Full dataset drift monitoring run
# ─────────────────────────────────────────────

def monitor_dataset_drift(
    reference_errors: np.ndarray,
    current_errors: np.ndarray,
    reference_preds: np.ndarray | None = None,
    current_preds: np.ndarray | None = None,
    output_dir: str = "result_images/drift",
) -> dict:
    """
    Monitor drift in reconstruction error and prediction distribution.

    Parameters
    ----------
    reference_errors  : validation set reconstruction errors (baseline)
    current_errors    : test set / live errors (current)
    reference_preds   : predicted class distribution on validation (optional)
    current_preds     : predicted class distribution on test/live (optional)
    output_dir        : save directory

    Returns
    -------
    dict of all drift results
    """
    print("\n" + "=" * 60)
    print("CONCEPT DRIFT DETECTION")
    print("=" * 60)

    results = {}

    # RE drift
    results["reconstruction_error"] = detect_drift(
        reference_errors, current_errors,
        feature_name="reconstruction_error",
        output_dir=output_dir,
    )

    # Prediction distribution drift
    if reference_preds is not None and current_preds is not None:
        results["prediction_distribution"] = detect_drift(
            reference_preds.astype(float),
            current_preds.astype(float),
            feature_name="prediction_distribution",
            output_dir=output_dir,
        )

    # Save combined report
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "drift_report.json"), "w") as f:
        # Flatten for JSON
        clean = {
            k: {
                kk: vv for kk, vv in v.items()
                if not isinstance(vv, dict) or kk not in ("psi",)
            }
            for k, v in results.items()
        }
        json.dump(clean, f, indent=4)

    n_detected = sum(
        1 for r in results.values() if r.get("drift_detected", False)
    )
    print(f"\n  Drift detected in {n_detected}/{len(results)} signals.")
    return results
