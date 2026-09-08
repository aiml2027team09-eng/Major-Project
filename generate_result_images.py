#!/usr/bin/env python
"""
Generate result visualization images for the hybrid IDS pipeline.

Outputs per dataset under result_images/<dataset>/:
  - autoencoder_loss.png          (from training)
  - autoencoder_threshold_tuning.png
  - autoencoder_confusion_matrix.png
  - xgboost_confusion_matrix.png
  - hybrid_confusion_matrix.png
  - overall_confusion_matrix.png  (full test-set end-to-end)
  - performance_comparison.png    (AE vs XGB vs Hybrid on test)
  - performance_growth.png        (validation vs test metrics)

Usage:
  python generate_result_images.py
  python generate_result_images.py --dataset nsl_kdd
  python generate_result_images.py --dataset both
"""

from __future__ import annotations

import argparse
import json
import os
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import confusion_matrix
from xgboost import XGBClassifier

from dataset_config import VALID_DATASETS, configure_project, get_profile, resolve_model_folder
from hybrid_ids.anomaly_detection import calculate_reconstruction_error, detect_anomalies
from hybrid_ids.binary_labels import convert_to_binary_labels, load_label_encoder
from hybrid_ids.load_data import convert_to_numpy, load_datasets

OUTPUT_ROOT = "result_images"
METRICS = ("accuracy", "precision", "recall", "f1")


def _load_threshold(model_folder):
    with open(os.path.join(model_folder, "threshold.json")) as f:
        return float(json.load(f)["threshold"])


def _save_confusion_matrix(
    y_true,
    y_pred,
    labels,
    title,
    output_path,
    figsize=(10, 8),
):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=figsize)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def _copy_if_exists(src, dst):
    if os.path.exists(src):
        shutil.copy2(src, dst)
        return True
    return False


def _hybrid_predictions(autoencoder, xgb_model, X_test, threshold, label_encoder):
    """End-to-end hybrid: AE anomaly gate + XGBoost classification."""
    errors = calculate_reconstruction_error(autoencoder, X_test)
    anomaly_flags = detect_anomalies(errors, threshold)
    predictions = np.full(len(X_test), -1, dtype=int)

    benign_indices = [
        i
        for i, label in enumerate(label_encoder.classes_)
        if str(label).upper() in ("BENIGN", "NORMAL")
    ]
    benign_code = benign_indices[0]
    predictions[anomaly_flags == 0] = benign_code

    anomaly_idx = np.where(anomaly_flags == 1)[0]
    if len(anomaly_idx) > 0:
        xgb_pred = xgb_model.predict(X_test[anomaly_idx])
        predictions[anomaly_idx] = xgb_pred

    return predictions, anomaly_flags


def _metrics_from_cm(y_true, y_pred, labels):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    total = cm.sum()
    accuracy = np.trace(cm) / total if total else 0.0

    precisions, recalls, f1s = [], [], []
    for i in range(len(labels)):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        support = cm[i, :].sum()
        if support > 0:
            precisions.append(precision * support)
            recalls.append(recall * support)
            f1s.append(f1 * support)

    support_total = sum(cm[i, :].sum() for i in range(len(labels)))
    weighted_precision = sum(precisions) / support_total if support_total else 0.0
    weighted_recall = sum(recalls) / support_total if support_total else 0.0
    weighted_f1 = sum(f1s) / support_total if support_total else 0.0

    return {
        "accuracy": accuracy,
        "precision": weighted_precision,
        "recall": weighted_recall,
        "f1": weighted_f1,
    }


def _plot_performance_comparison(results, output_path, dataset_name):
    stages = ["Autoencoder", "XGBoost", "Hybrid"]
    x = np.arange(len(METRICS))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, stage in enumerate(stages):
        values = [results[stage][f"test_{m}"] for m in METRICS]
        ax.bar(x + i * width, values, width, label=stage)

    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"Model Performance Comparison — {dataset_name} (Test Set)")
    ax.set_xticks(x + width)
    ax.set_xticklabels([m.capitalize() for m in METRICS])
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def _plot_performance_growth(results, output_path, dataset_name):
    stages = ["Autoencoder", "XGBoost", "Hybrid"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for ax, metric in zip(axes, METRICS):
        val_scores = [results[s][f"validation_{metric}"] for s in stages]
        test_scores = [results[s][f"test_{metric}"] for s in stages]
        x = np.arange(len(stages))
        width = 0.35
        ax.bar(x - width / 2, val_scores, width, label="Validation", color="#4C72B0")
        ax.bar(x + width / 2, test_scores, width, label="Test", color="#55A868")
        ax.set_title(metric.capitalize())
        ax.set_xticks(x)
        ax.set_xticklabels(stages, rotation=15)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle(f"Performance Growth — {dataset_name} (Validation vs Test)", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def generate_for_dataset(dataset_name):
    profile = configure_project(dataset_name)
    model_folder = resolve_model_folder(profile)
    out_dir = os.path.join(OUTPUT_ROOT, dataset_name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'=' * 70}")
    print(f"Generating images for {profile.display_name}")
    print(f"Models: {model_folder}")
    print(f"Output: {out_dir}")
    print("=" * 70)

    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
        _X_normal,
    ) = load_datasets()
    (
        _X_train_np,
        _y_train_np,
        X_validation_np,
        y_validation_np,
        X_test_np,
        y_test_np,
        _X_normal_np,
    ) = convert_to_numpy(
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
        _X_normal,
    )

    label_encoder = load_label_encoder()
    class_names = list(label_encoder.classes_)
    threshold = _load_threshold(model_folder)

    autoencoder = tf.keras.models.load_model(
        os.path.join(model_folder, "autoencoder.keras")
    )
    xgb_model = XGBClassifier()
    xgb_model.load_model(os.path.join(model_folder, "xgboost_model.json"))

    # Copy training plots if available
    _copy_if_exists(
        os.path.join(model_folder, "autoencoder_loss.png"),
        os.path.join(out_dir, "autoencoder_loss.png"),
    )
    _copy_if_exists(
        os.path.join(model_folder, "threshold_tuning.png"),
        os.path.join(out_dir, "autoencoder_threshold_tuning.png"),
    )

    # --- Autoencoder binary confusion matrix (test) ---
    test_binary = convert_to_binary_labels(y_test_np, label_encoder)
    val_binary = convert_to_binary_labels(y_validation_np, label_encoder)
    test_errors = calculate_reconstruction_error(autoencoder, X_test_np)
    val_errors = calculate_reconstruction_error(autoencoder, X_validation_np)
    test_ae_pred = detect_anomalies(test_errors, threshold)

    ae_labels = ["Normal", "Attack"]
    cm = confusion_matrix(test_binary, test_ae_pred, labels=[0, 1])
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=ae_labels,
        yticklabels=ae_labels,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"Autoencoder Confusion Matrix — {profile.display_name} (Test)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "autoencoder_confusion_matrix.png"), dpi=300)
    plt.close()

    def _binary_metrics(y_true, y_pred):
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tp, fn, fp, tn = cm[1, 1], cm[1, 0], cm[0, 1], cm[0, 0]
        accuracy = (tp + tn) / cm.sum()
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

    ae_val_metrics = _binary_metrics(val_binary, detect_anomalies(val_errors, threshold))
    ae_test_metrics = _binary_metrics(test_binary, test_ae_pred)

    # --- XGBoost confusion matrix (test) ---
    xgb_test_pred = xgb_model.predict(X_test_np)
    xgb_val_pred = xgb_model.predict(X_validation_np)
    cm = confusion_matrix(y_test_np, xgb_test_pred, labels=np.arange(len(class_names)))
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Oranges",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"XGBoost Confusion Matrix — {profile.display_name} (Test)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "xgboost_confusion_matrix.png"), dpi=300)
    plt.close()

    xgb_val_metrics = _metrics_from_cm(
        y_validation_np, xgb_val_pred, labels=np.arange(len(class_names))
    )
    xgb_test_metrics = _metrics_from_cm(
        y_test_np, xgb_test_pred, labels=np.arange(len(class_names))
    )

    # --- Hybrid confusion matrix (anomaly subset, test) ---
    test_anomaly_flags = detect_anomalies(test_errors, threshold)
    anomaly_idx = np.where(test_anomaly_flags == 1)[0]
    if len(anomaly_idx) > 0:
        y_anom = y_test_np[anomaly_idx]
        hybrid_anom_pred = xgb_model.predict(X_test_np[anomaly_idx])
        present_labels = sorted(np.unique(np.concatenate([y_anom, hybrid_anom_pred])))
        present_names = label_encoder.inverse_transform(present_labels)
        cm = confusion_matrix(y_anom, hybrid_anom_pred, labels=present_labels)
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Purples",
            xticklabels=present_names,
            yticklabels=present_names,
        )
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title(
            f"Hybrid Pipeline Confusion Matrix — {profile.display_name} "
            f"(Anomalies Only, n={len(anomaly_idx)})"
        )
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "hybrid_confusion_matrix.png"), dpi=300)
        plt.close()
        hybrid_val_flags = detect_anomalies(val_errors, threshold)
        val_anomaly_idx = np.where(hybrid_val_flags == 1)[0]
        if len(val_anomaly_idx) > 0:
            y_val_anom = y_validation_np[val_anomaly_idx]
            hybrid_val_pred = xgb_model.predict(X_validation_np[val_anomaly_idx])
            hybrid_val_metrics = _metrics_from_cm(
                y_val_anom,
                hybrid_val_pred,
                labels=np.arange(len(class_names)),
            )
        else:
            hybrid_val_metrics = {m: 0.0 for m in METRICS}
        hybrid_test_metrics = _metrics_from_cm(
            y_anom,
            hybrid_anom_pred,
            labels=np.arange(len(class_names)),
        )
    else:
        hybrid_val_metrics = {m: 0.0 for m in METRICS}
        hybrid_test_metrics = {m: 0.0 for m in METRICS}

    # --- Overall end-to-end confusion matrix (full test set) ---
    overall_pred, _ = _hybrid_predictions(
        autoencoder, xgb_model, X_test_np, threshold, label_encoder
    )
    cm = confusion_matrix(
        y_test_np, overall_pred, labels=np.arange(len(class_names))
    )
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Reds",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"Overall Hybrid Confusion Matrix — {profile.display_name} (Full Test Set)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "overall_confusion_matrix.png"), dpi=300)
    plt.close()

    overall_val_pred, _ = _hybrid_predictions(
        autoencoder, xgb_model, X_validation_np, threshold, label_encoder
    )
    overall_val_metrics = _metrics_from_cm(
        y_validation_np, overall_val_pred, labels=np.arange(len(class_names))
    )
    overall_test_metrics = _metrics_from_cm(
        y_test_np, overall_pred, labels=np.arange(len(class_names))
    )

    results = {
        "dataset": dataset_name,
        "Autoencoder": {
            **{f"validation_{k}": v for k, v in ae_val_metrics.items()},
            **{f"test_{k}": v for k, v in ae_test_metrics.items()},
        },
        "XGBoost": {
            **{f"validation_{k}": v for k, v in xgb_val_metrics.items()},
            **{f"test_{k}": v for k, v in xgb_test_metrics.items()},
        },
        "Hybrid": {
            **{f"validation_{k}": v for k, v in hybrid_val_metrics.items()},
            **{f"test_{k}": v for k, v in hybrid_test_metrics.items()},
        },
        "Overall": {
            **{f"validation_{k}": v for k, v in overall_val_metrics.items()},
            **{f"test_{k}": v for k, v in overall_test_metrics.items()},
        },
    }

    _plot_performance_comparison(
        results,
        os.path.join(out_dir, "performance_comparison.png"),
        profile.display_name,
    )
    _plot_performance_growth(
        results,
        os.path.join(out_dir, "performance_growth.png"),
        profile.display_name,
    )

    # Summary table image
    rows = []
    for stage in ("Autoencoder", "XGBoost", "Hybrid"):
        for split in ("validation", "test"):
            row = {"Stage": stage, "Split": split.capitalize()}
            for m in METRICS:
                row[m.capitalize()] = round(results[stage][f"{split}_{m}"], 4)
            rows.append(row)
    summary_df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    table = ax.table(
        cellText=summary_df.values,
        colLabels=summary_df.columns,
        loc="center",
        cellLoc="center",
    )
    table.scale(1.2, 1.5)
    ax.set_title(f"Performance Summary — {profile.display_name}", pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "performance_summary_table.png"), dpi=300)
    plt.close()

    with open(os.path.join(out_dir, "metrics_summary.json"), "w") as f:
        json.dump(results, f, indent=2)

    generated = sorted(os.listdir(out_dir))
    print(f"\nSaved {len(generated)} files to {os.path.abspath(out_dir)}:")
    for name in generated:
        print(f"  - {name}")

    return results


def _plot_combined_comparison(all_results, output_path):
    datasets = list(all_results.keys())
    stages = ["Autoencoder", "XGBoost", "Hybrid"]
    fig, axes = plt.subplots(1, len(METRICS), figsize=(16, 5))
    x = np.arange(len(datasets))
    width = 0.25

    for ax, metric in zip(axes, METRICS):
        for i, stage in enumerate(stages):
            scores = [all_results[ds][stage][f"test_{metric}"] for ds in datasets]
            ax.bar(x + i * width, scores, width, label=stage)
        ax.set_title(metric.capitalize())
        ax.set_xticks(x + width)
        ax.set_xticklabels([d.upper() for d in datasets])
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", alpha=0.3)
        if metric == "accuracy":
            ax.legend()

    fig.suptitle("Cross-Dataset Test Performance (F1 Growth Overview)", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate hybrid IDS result images")
    parser.add_argument(
        "--dataset",
        "-d",
        choices=[*VALID_DATASETS, "both"],
        default="both",
        help="Dataset profile(s) to visualize (default: both)",
    )
    args = parser.parse_args()

    datasets = list(VALID_DATASETS) if args.dataset == "both" else [args.dataset]
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    all_results = {}
    for name in datasets:
        all_results[name] = generate_for_dataset(name)

    if len(all_results) > 1:
        combined_dir = os.path.join(OUTPUT_ROOT, "combined")
        os.makedirs(combined_dir, exist_ok=True)
        _plot_combined_comparison(
            all_results,
            os.path.join(combined_dir, "performance_comparison_both_datasets.png"),
        )
        print(f"\nCombined chart: {os.path.abspath(combined_dir)}")

    print(f"\nAll images saved under: {os.path.abspath(OUTPUT_ROOT)}")


if __name__ == "__main__":
    main()
