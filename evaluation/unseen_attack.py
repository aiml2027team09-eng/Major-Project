"""
evaluation/unseen_attack.py
============================
Unseen / zero-day attack evaluation (Experiment C from the master prompt).

Research Question (RQ4):
  Can the Autoencoder identify previously unseen attack categories
  as anomalous even when excluded from supervised classifier training?

Hypothesis (H4):
  The Autoencoder can detect a meaningful proportion of unseen attack
  traffic as anomalous even when the attack category is excluded from
  supervised classifier training.

Procedure (leave-one-class-out):
  1. Select a "held-out" attack class (e.g. Infiltration).
  2. Remove it from XGBoost training and supervised evaluation.
  3. Train XGBoost only on remaining attack classes.
  4. Evaluate Autoencoder on held-out class.
  5. Report detection rate, reconstruction error distribution, FNR.
  6. The system should flag held-out samples as "Anomalous / Unknown Attack"
     rather than forcing them into a known class.

Note
----
The Autoencoder is NOT retrained per held-out class experiment — it was
trained on benign traffic only, so it naturally produces high RE for any
attack type it has not seen (including held-out ones).
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
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)


# ─────────────────────────────────────────────
#  1. Run single held-out experiment
# ─────────────────────────────────────────────

def run_leave_one_out_experiment(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_encoder,
    held_out_class: str,
    threshold: float,
    output_dir: str,
) -> dict:
    """
    Evaluate the system on a held-out (unseen) attack class.

    Parameters
    ----------
    autoencoder      : trained Keras autoencoder (trained on benign only)
    xgb_model        : XGBoost model (trained WITHOUT held_out_class)
    X_test           : test feature matrix (numpy)
    y_test           : integer-encoded test labels
    label_encoder    : fitted LabelEncoder with all classes
    held_out_class   : string name of the class to treat as unseen
    threshold        : anomaly detection threshold
    output_dir       : directory for plots and results

    Returns
    -------
    dict with all metrics for this experiment
    """
    os.makedirs(output_dir, exist_ok=True)
    class_names = list(label_encoder.classes_)

    if held_out_class not in class_names:
        warnings.warn(f"Held-out class '{held_out_class}' not found in label encoder.")
        return {}

    held_out_idx = class_names.index(held_out_class)
    benign_label = next(
        (c for c in class_names if c.upper() in ("BENIGN", "NORMAL")), class_names[0]
    )
    benign_idx = class_names.index(benign_label)

    print("\n" + "=" * 60)
    print(f"UNSEEN ATTACK EXPERIMENT: {held_out_class}")
    print("=" * 60)

    # Masks
    held_out_mask = y_test == held_out_idx
    benign_mask   = y_test == benign_idx
    known_attack_mask = (~held_out_mask) & (~benign_mask)

    print(f"  Held-out samples   : {held_out_mask.sum()}")
    print(f"  Benign samples     : {benign_mask.sum()}")
    print(f"  Known attack samples: {known_attack_mask.sum()}")

    if held_out_mask.sum() == 0:
        print(f"  WARNING: No samples for held-out class '{held_out_class}'.")
        return {"held_out_class": held_out_class, "n_samples": 0}

    # Compute reconstruction errors
    from hybrid_ids.anomaly_detection import calculate_reconstruction_error
    all_errors = calculate_reconstruction_error(autoencoder, X_test)

    held_out_errors = all_errors[held_out_mask]
    benign_errors   = all_errors[benign_mask]
    known_errors    = all_errors[known_attack_mask] if known_attack_mask.sum() > 0 else np.array([])

    # Anomaly detection on held-out class
    ae_preds_held_out = (held_out_errors > threshold).astype(int)
    detection_rate = float(ae_preds_held_out.mean())
    fn_rate        = 1.0 - detection_rate

    print(f"\n  Autoencoder detection rate (held-out): {detection_rate:.4f}")
    print(f"  False negative rate (held-out):        {fn_rate:.4f}")
    print(f"  Mean RE (held-out): {held_out_errors.mean():.6f}")
    print(f"  Mean RE (benign):   {benign_errors.mean():.6f}")

    # Plot error distributions
    _plot_unseen_distributions(
        benign_errors, held_out_errors, known_errors,
        held_out_class, threshold,
        output_path=os.path.join(output_dir, f"unseen_{held_out_class.replace(' ', '_')}_errors.png"),
    )

    # XGBoost behaviour on detected held-out samples
    detected_mask = ae_preds_held_out == 1
    xgb_on_detected = {}
    if detected_mask.sum() > 0:
        X_held_detected = X_test[held_out_mask][detected_mask]
        xgb_preds = xgb_model.predict(X_held_detected)
        proba      = xgb_model.predict_proba(X_held_detected)
        pred_classes = [class_names[p] for p in xgb_preds]
        counts = pd.Series(pred_classes).value_counts().to_dict()
        print(f"\n  XGBoost forced classifications for detected held-out samples:")
        for cls, cnt in counts.items():
            print(f"    {cls}: {cnt}")
        xgb_on_detected = {
            "forced_classifications": counts,
            "note": (
                "These samples were correctly flagged as ANOMALOUS by AE. "
                "XGBoost forced them into a known class — real systems should "
                "label these as 'Unknown/Unseen Attack' when confidence is low."
            ),
        }
        # Show average confidence
        max_proba = proba.max(axis=1)
        print(f"  Mean XGBoost confidence on held-out: {max_proba.mean():.4f}")
        xgb_on_detected["mean_confidence"] = float(max_proba.mean())

    result = {
        "held_out_class":         held_out_class,
        "n_held_out_samples":     int(held_out_mask.sum()),
        "n_detected_by_ae":       int(ae_preds_held_out.sum()),
        "detection_rate":         detection_rate,
        "false_negative_rate":    fn_rate,
        "mean_re_held_out":       float(held_out_errors.mean()),
        "mean_re_benign":         float(benign_errors.mean()),
        "std_re_held_out":        float(held_out_errors.std()),
        "threshold":              threshold,
        "xgb_on_detected":        xgb_on_detected,
    }

    # Save per-experiment JSON
    out_path = os.path.join(
        output_dir,
        f"unseen_{held_out_class.replace(' ', '_')}_results.json",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    return result


def _plot_unseen_distributions(
    benign_errors: np.ndarray,
    held_out_errors: np.ndarray,
    known_errors: np.ndarray,
    held_out_class: str,
    threshold: float,
    output_path: str,
) -> None:
    """Plot reconstruction error distributions for unseen attack experiment."""
    plt.figure(figsize=(12, 5))

    bins = 80
    clip = np.percentile(
        np.concatenate([benign_errors, held_out_errors]),
        99.5,
    )

    plt.hist(np.clip(benign_errors, 0, clip), bins=bins, alpha=0.5,
             label="Benign", color="green", density=True)
    if len(known_errors) > 0:
        plt.hist(np.clip(known_errors, 0, clip), bins=bins, alpha=0.4,
                 label="Known attacks", color="orange", density=True)
    plt.hist(np.clip(held_out_errors, 0, clip), bins=bins, alpha=0.6,
             label=f"Unseen: {held_out_class}", color="red", density=True)
    plt.axvline(threshold, color="black", linestyle="--", linewidth=2,
                label=f"Threshold = {threshold:.4f}")
    plt.xlabel("Reconstruction Error (MSE)")
    plt.ylabel("Density")
    plt.title(f"Unseen Attack Experiment: {held_out_class}")
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Saved: {output_path}")


# ─────────────────────────────────────────────
#  2. Multi-class leave-one-out
# ─────────────────────────────────────────────

def run_all_unseen_experiments(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label_encoder,
    threshold: float,
    output_dir: str,
    exclude_classes: list[str] | None = None,
    min_samples: int = 10,
) -> pd.DataFrame:
    """
    Run leave-one-out unseen attack experiment for all attack classes.

    Parameters
    ----------
    autoencoder     : trained Keras autoencoder
    xgb_model       : XGBoost model (note: trained on ALL classes here;
                       for full LOO, re-train XGBoost per fold separately)
    X_test          : test features
    y_test          : integer labels
    label_encoder   : fitted LabelEncoder
    threshold       : anomaly threshold
    output_dir      : output directory
    exclude_classes : skip these classes (e.g. ["Benign"])
    min_samples     : skip classes with fewer than this many test samples

    Returns
    -------
    DataFrame with per-class unseen experiment results
    """
    os.makedirs(output_dir, exist_ok=True)
    class_names = list(label_encoder.classes_)
    benign_label = next(
        (c for c in class_names if c.upper() in ("BENIGN", "NORMAL")), None
    )

    exclude_set = set(exclude_classes or [])
    if benign_label:
        exclude_set.add(benign_label)

    results = []
    for cls in class_names:
        if cls in exclude_set:
            continue
        cls_idx = class_names.index(cls)
        n_samples = int((y_test == cls_idx).sum())
        if n_samples < min_samples:
            print(f"  Skipping {cls}: only {n_samples} samples (min={min_samples})")
            continue

        result = run_leave_one_out_experiment(
            autoencoder, xgb_model,
            X_test, y_test, label_encoder,
            held_out_class=cls,
            threshold=threshold,
            output_dir=output_dir,
        )
        results.append(result)

    if not results:
        print("  No unseen experiments completed.")
        return pd.DataFrame()

    df = pd.DataFrame(results)

    # Summary table
    print("\n=== Unseen Attack Detection Summary ===")
    display_cols = [
        "held_out_class", "n_held_out_samples",
        "detection_rate", "false_negative_rate",
        "mean_re_held_out", "mean_re_benign",
    ]
    print(df[[c for c in display_cols if c in df.columns]].to_string(
        index=False, float_format="{:.4f}".format
    ))

    df.to_csv(os.path.join(output_dir, "unseen_attack_summary.csv"), index=False)

    # Summary bar chart
    _plot_unseen_summary(df, output_dir)

    return df


def _plot_unseen_summary(df: pd.DataFrame, output_dir: str) -> None:
    """Bar chart of detection rates across all unseen experiments."""
    if df.empty or "held_out_class" not in df.columns:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.bar(df["held_out_class"], df["detection_rate"], color="steelblue", edgecolor="black")
    ax.set_title("Autoencoder Detection Rate for Unseen Attack Classes")
    ax.set_ylabel("Detection Rate (Recall)")
    ax.set_xlabel("Held-out Attack Class")
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="red", linestyle="--", linewidth=1, label="50% detection")
    ax.legend()

    ax = axes[1]
    ax.bar(df["held_out_class"], df["mean_re_held_out"], color="darkorange",
           edgecolor="black", label="Held-out")
    if "mean_re_benign" in df.columns:
        ax.axhline(df["mean_re_benign"].mean(), color="green", linestyle="--",
                   linewidth=1.5, label="Benign mean RE")
    ax.set_title("Mean Reconstruction Error (Unseen vs Benign)")
    ax.set_ylabel("Mean RE")
    ax.set_xlabel("Held-out Attack Class")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "unseen_attack_summary.png"), dpi=300)
    plt.close()
    print(f"  Summary plot saved → {output_dir}/unseen_attack_summary.png")
