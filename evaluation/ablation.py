"""
evaluation/ablation.py
========================
Ablation study for the Hybrid IDS (Section 22 from master prompt).

Compares the contribution of each component by evaluating 7 model variants:

  Model A — XGBoost only (standalone classifier)
  Model B — Autoencoder only (anomaly detection only)
  Model C — AE + XGBoost (fixed threshold, no adaptivity)
  Model D — AE + XGBoost + Fixed threshold
  Model E — AE + XGBoost + Adaptive threshold
  Model F — AE + XGBoost + Adaptive threshold + SHAP
  Model G — Full system: AE + Adaptive threshold + XGBoost + SHAP
             + temporal evaluation + unseen attack evaluation

Research objective
------------------
The ablation study demonstrates the contribution of each component
and answers: is each addition justified by measurable improvement?

Evaluation metrics per model:
  - Accuracy, Precision, Recall, F1 (weighted + macro)
  - FPR, FNR
  - ROC-AUC (binary)
  - Detection latency (ms/sample)
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
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ─────────────────────────────────────────────
#  Helper: measure inference time
# ─────────────────────────────────────────────

def _timed_predict(predict_fn, X: np.ndarray, n_runs: int = 3) -> tuple[np.ndarray, float]:
    """Run predict_fn n_runs times, return predictions and mean latency (ms/sample)."""
    times = []
    for _ in range(n_runs):
        t0  = time.perf_counter()
        out = predict_fn(X)
        times.append(time.perf_counter() - t0)
    mean_ms = float(np.mean(times)) * 1000 / len(X)  # ms per sample
    return out, mean_ms


def _binary_metrics(y_true, y_pred, y_score=None):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    acc  = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec  = float(recall_score(y_true, y_pred, zero_division=0))
    f1   = float(f1_score(y_true, y_pred, zero_division=0))

    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    roc = None
    if y_score is not None:
        try:
            roc = float(roc_auc_score(y_true, y_score))
        except ValueError:
            pass

    return {
        "accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
        "fpr": fpr, "fnr": fnr, "roc_auc": roc,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }


def _multi_metrics(y_true, y_pred):
    return {
        "accuracy":           float(accuracy_score(y_true, y_pred)),
        "f1_weighted":        float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_macro":           float(f1_score(y_true, y_pred, average="macro",    zero_division=0)),
        "precision_weighted": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_weighted":    float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


# ─────────────────────────────────────────────
#  Model A: XGBoost only
# ─────────────────────────────────────────────

def model_a_xgboost_only(
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
) -> dict:
    """Standalone XGBoost on full test set (no anomaly filter)."""
    print("\n  [Model A] XGBoost only")

    preds, latency = _timed_predict(xgb_model.predict, X_test)
    proba          = xgb_model.predict_proba(X_test)
    max_proba      = proba.max(axis=1)

    multi = _multi_metrics(y_test, preds)
    # Binary: treat non-benign as attack (1)
    preds_binary = (preds != min(set(y_test))).astype(int)  # rough
    binary = _binary_metrics(y_binary, preds_binary, max_proba)

    m = {**multi, **binary, "latency_ms_per_sample": latency}
    print(f"     Acc={m['accuracy']:.4f}  F1-w={m['f1_weighted']:.4f}  FPR={m['fpr']:.4f}  "
          f"Latency={latency:.3f}ms/sample")
    return m


# ─────────────────────────────────────────────
#  Model B: Autoencoder only
# ─────────────────────────────────────────────

def model_b_autoencoder_only(
    autoencoder,
    X_test: np.ndarray,
    y_binary: np.ndarray,
    threshold: float,
) -> dict:
    """Autoencoder-only anomaly detection (binary: anomaly/normal)."""
    print("\n  [Model B] Autoencoder only (fixed threshold)")

    from hybrid_ids.anomaly_detection import calculate_reconstruction_error
    errors, latency = _timed_predict(
        lambda X: calculate_reconstruction_error(autoencoder, X), X_test
    )
    preds = (errors > threshold).astype(int)

    m = _binary_metrics(y_binary, preds, errors)
    m["latency_ms_per_sample"] = latency
    print(f"     Acc={m['accuracy']:.4f}  F1={m['f1']:.4f}  FPR={m['fpr']:.4f}  "
          f"ROC-AUC={m['roc_auc']:.4f}")
    return m


# ─────────────────────────────────────────────
#  Model C: AE + XGBoost (no threshold tuning)
# ─────────────────────────────────────────────

def model_c_ae_xgboost_no_tuning(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
    threshold: float,
    label_encoder,
) -> dict:
    """AE + XGBoost with simple fixed 99th-percentile threshold, no tuning."""
    print("\n  [Model C] AE + XGBoost (untuned fixed threshold)")
    return _hybrid_eval(autoencoder, xgb_model, X_test, y_test,
                        y_binary, threshold, label_encoder, "Model C")


# ─────────────────────────────────────────────
#  Model D: AE + XGBoost + Fixed threshold (tuned)
# ─────────────────────────────────────────────

def model_d_ae_xgboost_fixed(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
    fixed_threshold: float,
    label_encoder,
) -> dict:
    """AE + XGBoost with validation-tuned fixed threshold."""
    print("\n  [Model D] AE + XGBoost + Fixed (tuned) threshold")
    return _hybrid_eval(autoencoder, xgb_model, X_test, y_test,
                        y_binary, fixed_threshold, label_encoder, "Model D")


# ─────────────────────────────────────────────
#  Model E: AE + XGBoost + Adaptive threshold
# ─────────────────────────────────────────────

def model_e_ae_xgboost_adaptive(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
    adaptive_threshold: float,
    label_encoder,
) -> dict:
    """AE + XGBoost with statistical adaptive threshold (μ + kσ)."""
    print("\n  [Model E] AE + XGBoost + Adaptive threshold")
    return _hybrid_eval(autoencoder, xgb_model, X_test, y_test,
                        y_binary, adaptive_threshold, label_encoder, "Model E")


# ─────────────────────────────────────────────
#  Model F: AE + XGBoost + Adaptive + SHAP
# ─────────────────────────────────────────────

def model_f_full_minus_temporal(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
    adaptive_threshold: float,
    label_encoder,
    feature_names: list[str] | None = None,
    include_shap_timing: bool = True,
) -> dict:
    """AE + XGBoost + Adaptive threshold + SHAP (timed)."""
    print("\n  [Model F] AE + XGBoost + Adaptive + SHAP")

    base_m = _hybrid_eval(autoencoder, xgb_model, X_test, y_test,
                           y_binary, adaptive_threshold, label_encoder, "Model F")

    if include_shap_timing and feature_names is not None:
        try:
            from explainability.shap_analysis import build_explainer, compute_shap_values
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                expl = build_explainer(xgb_model, X_test[:200])
                n_shap = min(100, len(X_test))
                t0 = time.perf_counter()
                compute_shap_values(expl, X_test[:n_shap])
                shap_time_ms = (time.perf_counter() - t0) * 1000 / n_shap
            base_m["shap_latency_ms_per_sample"] = shap_time_ms
            print(f"     SHAP latency: {shap_time_ms:.3f} ms/sample")
        except Exception as e:
            warnings.warn(f"SHAP timing failed: {e}")

    return base_m


# ─────────────────────────────────────────────
#  Model G: Full proposed system
# ─────────────────────────────────────────────

def model_g_full_system(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
    adaptive_threshold: float,
    label_encoder,
    temporal_metrics: dict | None = None,
    unseen_metrics: dict | None = None,
) -> dict:
    """Full proposed system — includes all components."""
    print("\n  [Model G] Full system: AE + Adaptive + XGBoost + SHAP + Temporal + Unseen")

    m = _hybrid_eval(autoencoder, xgb_model, X_test, y_test,
                     y_binary, adaptive_threshold, label_encoder, "Model G")

    if temporal_metrics:
        m["temporal_f1_weighted"] = temporal_metrics.get("f1_weighted")
    if unseen_metrics:
        # Average detection rate across all unseen experiments
        rates = [v.get("detection_rate", 0.0) for v in (
            unseen_metrics.values() if isinstance(unseen_metrics, dict)
            else [{"detection_rate": unseen_metrics}]
        )]
        m["unseen_detection_rate"] = float(np.mean(rates)) if rates else None

    return m


# ─────────────────────────────────────────────
#  Shared hybrid evaluation helper
# ─────────────────────────────────────────────

def _hybrid_eval(autoencoder, xgb_model, X_test, y_test, y_binary,
                 threshold, label_encoder, model_name) -> dict:
    from hybrid_ids.anomaly_detection import calculate_reconstruction_error

    t0     = time.perf_counter()
    errors = calculate_reconstruction_error(autoencoder, X_test)
    ae_t   = time.perf_counter() - t0

    ae_preds = (errors > threshold).astype(int)

    anomaly_idx = np.where(ae_preds == 1)[0]
    class_names = list(label_encoder.classes_)
    benign_idx  = next(
        i for i, c in enumerate(class_names) if c.upper() in ("BENIGN", "NORMAL")
    )

    final_preds = np.full(len(y_test), benign_idx, dtype=int)

    xgb_t = 0.0
    if len(anomaly_idx) > 0:
        t0 = time.perf_counter()
        xgb_preds = xgb_model.predict(X_test[anomaly_idx])
        xgb_t = time.perf_counter() - t0
        final_preds[anomaly_idx] = xgb_preds

    total_t = ae_t + xgb_t
    latency = total_t * 1000 / len(X_test)

    multi  = _multi_metrics(y_test, final_preds)
    binary = _binary_metrics(y_binary, ae_preds, errors)
    binary.pop("roc_auc", None)  # handled above

    m = {
        **multi, **binary,
        "latency_ms_per_sample": latency,
        "ae_latency_ms":         ae_t * 1000,
        "xgb_latency_ms":        xgb_t * 1000,
        "anomalies_flagged":     int(len(anomaly_idx)),
        "threshold":             threshold,
    }
    print(f"     Acc={m['accuracy']:.4f}  F1-w={m['f1_weighted']:.4f}  "
          f"FPR={m['fpr']:.4f}  FNR={m['fnr']:.4f}  Latency={latency:.3f}ms/sample")
    return m


# ─────────────────────────────────────────────
#  Run full ablation study
# ─────────────────────────────────────────────

def run_ablation_study(
    autoencoder,
    xgb_model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    y_binary: np.ndarray,
    normal_errors: np.ndarray,
    label_encoder,
    output_dir: str = "result_images/ablation",
    feature_names: list[str] | None = None,
    temporal_metrics: dict | None = None,
    unseen_metrics: dict | None = None,
) -> pd.DataFrame:
    """
    Run the complete 7-model ablation study.

    Returns DataFrame with one row per model and columns for all metrics.
    """
    from models.adaptive_threshold import (
        fixed_percentile_threshold,
        statistical_threshold,
    )

    os.makedirs(output_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("ABLATION STUDY (Models A → G)")
    print("=" * 60)

    fixed_99 = fixed_percentile_threshold(normal_errors, 99.0)
    adaptive = statistical_threshold(normal_errors, k=3.0)

    models_results = {}

    models_results["A_XGBoost_Only"] = model_a_xgboost_only(
        xgb_model, X_test, y_test, y_binary
    )
    models_results["B_AE_Only"] = model_b_autoencoder_only(
        autoencoder, X_test, y_binary, fixed_99
    )
    models_results["C_AE_XGB_Untuned"] = model_c_ae_xgboost_no_tuning(
        autoencoder, xgb_model, X_test, y_test, y_binary,
        fixed_percentile_threshold(normal_errors, 95.0),
        label_encoder,
    )
    models_results["D_AE_XGB_Fixed"] = model_d_ae_xgboost_fixed(
        autoencoder, xgb_model, X_test, y_test, y_binary, fixed_99, label_encoder
    )
    models_results["E_AE_XGB_Adaptive"] = model_e_ae_xgboost_adaptive(
        autoencoder, xgb_model, X_test, y_test, y_binary, adaptive, label_encoder
    )
    models_results["F_AE_XGB_Adaptive_SHAP"] = model_f_full_minus_temporal(
        autoencoder, xgb_model, X_test, y_test, y_binary, adaptive,
        label_encoder, feature_names,
    )
    models_results["G_Full_System"] = model_g_full_system(
        autoencoder, xgb_model, X_test, y_test, y_binary, adaptive,
        label_encoder, temporal_metrics, unseen_metrics,
    )

    # Build DataFrame
    rows = []
    for name, m in models_results.items():
        row = {"model": name}
        for k, v in m.items():
            if isinstance(v, (int, float)) and v is not None:
                row[k] = v
        rows.append(row)

    df = pd.DataFrame(rows)

    print("\n=== Ablation Study Summary ===")
    display_cols = [
        "model", "accuracy", "f1_weighted", "f1_macro",
        "fpr", "fnr", "latency_ms_per_sample",
    ]
    cols_exist = [c for c in display_cols if c in df.columns]
    print(df[cols_exist].to_string(index=False, float_format="{:.4f}".format))

    df.to_csv(os.path.join(output_dir, "ablation_results.csv"), index=False)

    with open(os.path.join(output_dir, "ablation_results.json"), "w") as f:
        json.dump({k: {kk: float(vv) for kk, vv in v.items()
                       if isinstance(vv, (int, float)) and vv is not None}
                   for k, v in models_results.items()}, f, indent=4)

    _plot_ablation(df, output_dir)

    return df


def _plot_ablation(df: pd.DataFrame, output_dir: str) -> None:
    """Bar chart comparing key metrics across ablation models."""
    metrics = ["accuracy", "f1_weighted", "fpr", "fnr", "latency_ms_per_sample"]
    metrics = [m for m in metrics if m in df.columns]

    n = len(metrics)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 5))
    if n == 1:
        axes = [axes]

    colors = plt.cm.tab10.colors

    for ax, metric in zip(axes, metrics):
        ax.bar(range(len(df)), df[metric], color=colors[:len(df)], edgecolor="black")
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(
            [m.replace("_", "\n") for m in df["model"]],
            fontsize=7, rotation=45, ha="right",
        )
        ax.set_title(metric.replace("_", " ").title(), fontsize=9)
        ax.set_ylabel(metric, fontsize=8)

    plt.suptitle("Ablation Study: Contribution of Each Component", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ablation_comparison.png"), dpi=300)
    plt.close()
    print(f"  Ablation chart saved → {output_dir}/ablation_comparison.png")
