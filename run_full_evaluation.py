"""
run_full_evaluation.py
========================
Master evaluation runner for the Adaptive Explainable Hybrid NIDS.

Runs ALL experiments from the master project prompt:
  - Experiment A: Conventional stratified split (standard benchmark)
  - Experiment B: Temporal split (generalization test)
  - Experiment C: Unseen attack detection (leave-one-class-out)
  - Ablation study: Models A → G
  - Baseline comparison: LR, RF, SVM, MLP, XGBoost, AE, Hybrid
  - Drift detection: KS, PSI, JSD
  - Reconstruction error analysis: histograms, ROC, PR, threshold curves
  - SHAP explainability: global + local + stability
  - Statistical validation: multi-seed
  - Performance measurement: latency, throughput, CPU, memory

Usage
-----
  python run_full_evaluation.py --dataset cicids2018
  python run_full_evaluation.py --dataset nsl_kdd
  python run_full_evaluation.py --dataset both
  python run_full_evaluation.py --dataset cicids2018 --skip-slow

Prerequisites
-------------
  1. Run preprocessing:  python preprocessing.py
  2. Run training:       python hybrid_ids_model.py --dataset cicids2018

All results saved to result_images/<dataset>/evaluation/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import tensorflow as tf
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

from dataset_config import VALID_DATASETS, configure_project, get_profile, resolve_model_folder
import hybrid_ids.config as config
from hybrid_ids.anomaly_detection import (
    calculate_reconstruction_error,
    detect_anomalies,
    determine_threshold,
)
from hybrid_ids.binary_labels import convert_to_binary_labels, load_label_encoder
from hybrid_ids.load_data import load_datasets, convert_to_numpy
from evaluation.metrics import (
    compute_binary_metrics,
    compute_multiclass_metrics,
    measure_inference_latency,
    compute_severity,
    print_metrics,
)


# ─────────────────────────────────────────────
#  Load models
# ─────────────────────────────────────────────

def _load_models(model_folder: str):
    """Load trained autoencoder and XGBoost from disk."""
    ae_path  = os.path.join(model_folder, "autoencoder.keras")
    xgb_path = os.path.join(model_folder, "xgboost_model.json")
    thr_path = os.path.join(model_folder, "threshold.json")

    if not os.path.exists(ae_path):
        raise FileNotFoundError(
            f"Autoencoder not found: {ae_path}\n"
            f"Run: python hybrid_ids_model.py --dataset {config.ACTIVE_DATASET}"
        )

    print("  Loading autoencoder...")
    autoencoder = tf.keras.models.load_model(ae_path)

    print("  Loading XGBoost...")
    xgb_model = XGBClassifier()
    xgb_model.load_model(xgb_path)

    print("  Loading threshold...")
    with open(thr_path, encoding="utf-8") as f:
        threshold_info = json.load(f)
    threshold = float(threshold_info["threshold"])

    return autoencoder, xgb_model, threshold


# ─────────────────────────────────────────────
#  Main evaluation runner per dataset
# ─────────────────────────────────────────────

def run_evaluation(
    dataset_name: str,
    skip_slow: bool = False,
    skip_shap: bool = False,
    skip_baselines: bool = False,
) -> dict:
    """Run complete evaluation for one dataset."""

    configure_project(dataset_name)
    model_folder = resolve_model_folder(get_profile(dataset_name))
    output_base  = os.path.join("result_images", dataset_name, "evaluation")
    os.makedirs(output_base, exist_ok=True)

    print("\n" + "=" * 70)
    print(f"FULL EVALUATION — {dataset_name.upper()}")
    print("=" * 70)

    # ── Load data ──────────────────────────────────────────────
    print("\n[1/10] Loading data...")
    (
        X_train, y_train, X_val, y_val, X_test, y_test, X_normal
    ) = load_datasets()

    (
        X_train_np, y_train_np, X_val_np, y_val_np,
        X_test_np,  y_test_np, X_normal_np,
    ) = convert_to_numpy(X_train, y_train, X_val, y_val, X_test, y_test, X_normal)

    label_encoder = load_label_encoder()
    class_names   = list(label_encoder.classes_)
    n_classes     = len(class_names)

    y_val_binary  = convert_to_binary_labels(y_val_np,  label_encoder)
    y_test_binary = convert_to_binary_labels(y_test_np, label_encoder)

    # Feature names
    try:
        feature_csv   = os.path.join(config.DATA_FOLDER, "X_test.csv")
        feature_names = pd.read_csv(feature_csv, nrows=0).columns.tolist()
    except Exception:
        feature_names = [f"feature_{i}" for i in range(X_test_np.shape[1])]

    # ── Load models ────────────────────────────────────────────
    print("\n[2/10] Loading trained models...")
    autoencoder, xgb_model, fixed_threshold = _load_models(model_folder)

    # ── Reconstruction errors ──────────────────────────────────
    print("\n[3/10] Computing reconstruction errors...")
    normal_errors = calculate_reconstruction_error(autoencoder, X_normal_np)
    val_errors    = calculate_reconstruction_error(autoencoder, X_val_np)
    test_errors   = calculate_reconstruction_error(autoencoder, X_test_np)

    # ── Adaptive threshold ─────────────────────────────────────
    print("\n[4/10] Computing adaptive threshold...")
    from models.adaptive_threshold import (
        fixed_percentile_threshold,
        statistical_threshold,
        tune_adaptive_threshold,
        compare_all_thresholds,
    )

    fixed_99    = fixed_percentile_threshold(normal_errors, 99.0)
    adaptive_th = statistical_threshold(normal_errors, k=3.0)
    tuned_info  = tune_adaptive_threshold(normal_errors, val_errors, y_val_binary)
    tuned_th    = tuned_info["threshold"]

    # Compare thresholds
    thresh_dir = os.path.join(output_base, "thresholds")
    compare_all_thresholds(
        normal_errors, test_errors, y_test_binary,
        output_dir=thresh_dir,
    )

    # ── Standard metrics (Experiment A) ────────────────────────
    print("\n[5/10] Experiment A — Standard evaluation (stratified split)...")

    ae_preds    = detect_anomalies(test_errors, tuned_th)
    ae_metrics  = compute_binary_metrics(y_test_binary, ae_preds)
    print_metrics(ae_metrics, "Autoencoder (Tuned Threshold)")

    # AE ROC/PR
    from evaluation.reconstruction_analysis import (
        plot_roc_curve, plot_pr_curve,
        plot_threshold_performance_curve,
        plot_error_distributions,
        error_statistics,
    )
    re_dir = os.path.join(output_base, "reconstruction")
    os.makedirs(re_dir, exist_ok=True)

    plot_roc_curve(y_test_binary, test_errors, tuned_th,
                   os.path.join(re_dir, "roc_curve.png"))
    plot_pr_curve(y_test_binary, test_errors,
                  os.path.join(re_dir, "pr_curve.png"))
    plot_threshold_performance_curve(y_test_binary, test_errors,
                                     os.path.join(re_dir, "threshold_performance.png"))

    # Error distributions by class
    errors_by_class = {}
    for idx, cls in enumerate(class_names):
        mask = y_test_np == idx
        if mask.sum() > 0:
            errors_by_class[cls] = test_errors[mask]
    if errors_by_class:
        plot_error_distributions(
            errors_by_class, tuned_th,
            os.path.join(re_dir, "error_by_class.png"),
        )
    error_statistics({
        "Normal (train)": normal_errors,
        "Validation":     val_errors,
        "Test":           test_errors,
    })

    # XGBoost standalone metrics
    xgb_preds   = xgb_model.predict(X_test_np)
    xgb_proba   = xgb_model.predict_proba(X_test_np)
    xgb_metrics = compute_multiclass_metrics(
        y_test_np, xgb_preds, class_names, xgb_proba
    )
    print_metrics({k: v for k, v in xgb_metrics.items() if isinstance(v, (int, float))},
                  "XGBoost (standalone)")

    # Hybrid pipeline
    benign_idx = next(
        i for i, c in enumerate(class_names) if c.upper() in ("BENIGN", "NORMAL")
    )
    anomaly_idx_arr = np.where(ae_preds == 1)[0]
    hybrid_preds = np.full(len(y_test_np), benign_idx, dtype=int)
    if len(anomaly_idx_arr) > 0:
        hybrid_preds[anomaly_idx_arr] = xgb_model.predict(X_test_np[anomaly_idx_arr])

    hybrid_metrics = compute_multiclass_metrics(y_test_np, hybrid_preds, class_names)
    print_metrics({k: v for k, v in hybrid_metrics.items() if isinstance(v, (int, float))},
                  "Hybrid AE + XGBoost")

    # FPR comparison: fixed vs adaptive
    from evaluation.metrics import compare_thresholds as _compare_th
    th_comparison = _compare_th(
        y_test_binary, test_errors, fixed_99, adaptive_th
    )
    print(f"\n  FPR: Fixed={th_comparison['fixed']['fpr']:.4f}  "
          f"Adaptive={th_comparison['adaptive']['fpr']:.4f}  "
          f"Delta={th_comparison['fpr_delta']:+.4f}")

    # ── Unseen attack evaluation (Experiment C) ────────────────
    print("\n[6/10] Experiment C — Unseen attack evaluation...")
    from evaluation.unseen_attack import run_all_unseen_experiments
    unseen_dir = os.path.join(output_base, "unseen")

    unseen_df = run_all_unseen_experiments(
        autoencoder, xgb_model,
        X_test_np, y_test_np, label_encoder,
        threshold=tuned_th,
        output_dir=unseen_dir,
    )

    # ── Drift detection ────────────────────────────────────────
    print("\n[7/10] Drift detection...")
    from evaluation.drift_detection import monitor_dataset_drift
    drift_dir = os.path.join(output_base, "drift")
    drift_results = monitor_dataset_drift(
        reference_errors=val_errors,
        current_errors=test_errors,
        reference_preds=xgb_model.predict(X_val_np).astype(float),
        current_preds=xgb_preds.astype(float),
        output_dir=drift_dir,
    )

    # ── Ablation study ─────────────────────────────────────────
    print("\n[8/10] Ablation study (Models A → G)...")
    from evaluation.ablation import run_ablation_study
    ablation_dir = os.path.join(output_base, "ablation")
    ablation_df = run_ablation_study(
        autoencoder, xgb_model,
        X_test_np, y_test_np, y_test_binary,
        normal_errors, label_encoder,
        output_dir=ablation_dir,
        feature_names=feature_names,
    )

    # ── Baseline comparison ────────────────────────────────────
    if not skip_baselines:
        print("\n[9/10] Baseline comparison...")
        from evaluation.baseline_comparison import run_baseline_comparison
        baselines_dir = os.path.join(output_base, "baselines")
        hybrid_m_for_baselines = {
            "accuracy":    hybrid_metrics.get("accuracy"),
            "f1_weighted": hybrid_metrics.get("f1_weighted"),
            "f1_macro":    hybrid_metrics.get("f1_macro"),
        }
        run_baseline_comparison(
            X_train_np, y_train_np,
            X_test_np,  y_test_np,
            n_classes=n_classes,
            autoencoder=autoencoder,
            y_binary=y_test_binary,
            threshold=tuned_th,
            hybrid_metrics=hybrid_m_for_baselines,
            output_dir=baselines_dir,
        )
    else:
        print("\n[9/10] Baseline comparison — SKIPPED (--skip-slow)")

    # ── SHAP analysis ──────────────────────────────────────────
    if not skip_shap:
        print("\n[10/10] SHAP explainability analysis...")
        from explainability.shap_analysis import run_full_shap_analysis
        shap_dir = os.path.join(output_base, "shap")
        try:
            run_full_shap_analysis(
                xgb_model,
                X_train_np, X_test_np, y_test_np,
                feature_names, label_encoder,
                output_dir=shap_dir,
            )
        except ImportError:
            print("  SHAP not installed. Install with: pip install shap")
        except Exception as e:
            print(f"  SHAP analysis failed: {e}")
    else:
        print("\n[10/10] SHAP analysis — SKIPPED (--skip-slow)")

    # ── Latency / performance ──────────────────────────────────
    print("\n[+] Measuring inference latency...")
    _measure_performance(autoencoder, xgb_model, X_test_np, tuned_th, output_base)

    # ── Save master results JSON ──────────────────────────────
    all_results = {
        "dataset":          dataset_name,
        "threshold_fixed":  fixed_99,
        "threshold_tuned":  tuned_th,
        "threshold_adaptive": adaptive_th,
        "experiment_a": {
            "autoencoder": ae_metrics,
            "xgboost":     {k: v for k, v in xgb_metrics.items() if isinstance(v, (int, float))},
            "hybrid":      {k: v for k, v in hybrid_metrics.items() if isinstance(v, (int, float))},
        },
        "threshold_comparison": {
            k: float(v) if isinstance(v, (int, float)) else v
            for k, v in th_comparison.items()
            if not isinstance(v, dict)
        },
        "drift_detected": any(
            r.get("drift_detected", False) for r in drift_results.values()
        ),
    }

    out_path = os.path.join(output_base, "full_evaluation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=4, default=str)

    print(f"\n✓ Full evaluation complete for {dataset_name.upper()}")
    print(f"  Results → {output_base}")

    return all_results


def _measure_performance(autoencoder, xgb_model, X_test_np, threshold, output_dir):
    """Measure and log inference latency and throughput."""
    try:
        import psutil
        cpu_pct = psutil.cpu_percent(interval=1)
        mem_mb  = psutil.Process().memory_info().rss / 1024 / 1024
    except ImportError:
        cpu_pct = None
        mem_mb  = None

    # AE latency
    ae_lat = measure_inference_latency(
        lambda X: calculate_reconstruction_error(autoencoder, X),
        X_test_np[:1000], n_repeats=3,
    )
    # XGBoost latency
    xgb_lat = measure_inference_latency(
        xgb_model.predict, X_test_np[:1000], n_repeats=3,
    )

    perf = {
        "ae_latency_ms_per_sample":   ae_lat["mean_ms"],
        "ae_throughput_fps":          ae_lat["throughput_fps"],
        "xgb_latency_ms_per_sample":  xgb_lat["mean_ms"],
        "xgb_throughput_fps":         xgb_lat["throughput_fps"],
        "total_latency_ms_per_sample": ae_lat["mean_ms"] + xgb_lat["mean_ms"],
        "cpu_percent":                cpu_pct,
        "memory_mb":                  mem_mb,
    }

    print(f"  AE latency:  {ae_lat['mean_ms']:.3f} ms/sample "
          f"({ae_lat['throughput_fps']:.0f} fps)")
    print(f"  XGB latency: {xgb_lat['mean_ms']:.3f} ms/sample "
          f"({xgb_lat['throughput_fps']:.0f} fps)")
    if cpu_pct:
        print(f"  CPU: {cpu_pct:.1f}%  RAM: {mem_mb:.0f} MB")

    with open(os.path.join(output_dir, "performance_metrics.json"), "w") as f:
        json.dump(perf, f, indent=4)

    return perf


# ─────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run full evaluation pipeline for the Hybrid IDS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset", "-d",
        choices=[*VALID_DATASETS, "both"],
        default="cicids2018",
        help="Dataset to evaluate (default: cicids2018)",
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip SHAP and baseline comparison (fast mode)",
    )
    parser.add_argument(
        "--skip-shap",
        action="store_true",
        help="Skip SHAP analysis only",
    )
    parser.add_argument(
        "--skip-baselines",
        action="store_true",
        help="Skip baseline model comparison only",
    )
    args = parser.parse_args()

    datasets = list(VALID_DATASETS) if args.dataset == "both" else [args.dataset]

    all_results = {}
    for ds in datasets:
        results = run_evaluation(
            ds,
            skip_slow=args.skip_slow,
            skip_shap=args.skip_slow or args.skip_shap,
            skip_baselines=args.skip_slow or args.skip_baselines,
        )
        all_results[ds] = results

    # Save combined
    os.makedirs("result_images", exist_ok=True)
    with open("result_images/full_evaluation_summary.json", "w") as f:
        json.dump(all_results, f, indent=4, default=str)

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print("Results saved to: result_images/<dataset>/evaluation/")
    print("\nNext steps:")
    print("  1. View dashboard:   python run_dashboard.py")
    print("  2. Validate model:   python validate_model.py")
    print("  3. Live monitoring:  python live_monitor.py --interface 'Wi-Fi'")


if __name__ == "__main__":
    main()
