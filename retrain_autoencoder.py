"""
Retrain the hybrid IDS using live-captured normal traffic.

Merges captured normal flows into the autoencoder training set, retrains
the autoencoder, retunes the threshold, and evaluates on the held-out test set.

Usage:
  python retrain_autoencoder.py --dataset nsl_kdd
  python retrain_autoencoder.py --dataset nsl_kdd --merge-live
  python retrain_autoencoder.py --dataset cicids2018 --data processed_live/cicids2018/X_normal_autoencoder.csv
"""

import argparse
import json
import os

import numpy as np
import pandas as pd

from dataset_config import VALID_DATASETS, configure_project, get_profile, resolve_model_folder
from hybrid_ids.anomaly_detection import (
    compute_reconstruction_errors,
    determine_threshold,
    detect_anomalies,
)
from hybrid_ids.autoencoder import (
    build_autoencoder,
    compile_autoencoder,
    plot_autoencoder_loss,
    save_autoencoder,
    train_autoencoder,
)
from hybrid_ids.binary_labels import convert_to_binary_labels, load_label_encoder
import hybrid_ids.config as config
from hybrid_ids.device_config import setup_training_devices
from hybrid_ids.evaluate_autoencoder import evaluate_autoencoder


def _load_validation_test():
    X_validation = pd.read_csv(os.path.join(config.DATA_FOLDER, "X_validation.csv"))
    X_test = pd.read_csv(os.path.join(config.DATA_FOLDER, "X_test.csv"))
    y_validation = pd.read_csv(os.path.join(config.DATA_FOLDER, "y_validation.csv"))["Label"]
    y_test = pd.read_csv(os.path.join(config.DATA_FOLDER, "y_test.csv"))["Label"]
    return (
        X_validation.astype(np.float32).values,
        y_validation.values,
        X_test.astype(np.float32).values,
        y_test.values,
    )


def _merge_normal_data(base_path, processed_live_path=None, live_oversample=1):
    """Combine dataset normal samples with preprocessed live normal samples."""
    base = pd.read_csv(base_path)
    frames = [base]

    if processed_live_path:
        live_normal = os.path.join(processed_live_path, "X_normal_autoencoder.csv")
        if os.path.exists(live_normal):
            live_df = pd.read_csv(live_normal)
            repeat = max(int(live_oversample), 1)
            frames.extend([live_df] * repeat)

    combined = pd.concat(frames, ignore_index=True)
    return combined.astype(np.float32)


def retrain_autoencoder(
    normal_data_path=None,
    merge_live=False,
    save_merged=False,
    live_oversample=5,
    threshold_metric="balanced",
):
    """Retrain autoencoder on normal-only processed features."""
    profile = get_profile(config.ACTIVE_DATASET)
    base_normal = os.path.join(config.DATA_FOLDER, "X_train_normal_autoencoder.csv")
    processed_live = os.path.join("processed_live", profile.captured_subfolder)

    if normal_data_path:
        X_normal_df = pd.read_csv(normal_data_path).astype(np.float32)
    elif merge_live:
        X_normal_df = _merge_normal_data(
            base_normal,
            processed_live_path=processed_live,
            live_oversample=live_oversample,
        )
    else:
        if not os.path.exists(base_normal):
            raise FileNotFoundError(f"No normal data at {base_normal}.")
        X_normal_df = pd.read_csv(base_normal).astype(np.float32)

    if len(X_normal_df) < 100:
        raise ValueError(
            f"Need at least 100 normal samples for retraining, found {len(X_normal_df)}.\n"
            "Capture more traffic: python live_capture.py --dataset "
            f"{profile.name} --interface \"Wi-Fi\""
        )

    if save_merged and merge_live:
        merged_path = os.path.join(config.DATA_FOLDER, "X_train_normal_autoencoder_merged.csv")
        X_normal_df.to_csv(merged_path, index=False)
        print(f"Saved merged normal dataset: {merged_path}")

    print("=" * 70)
    print(f"RETRAIN AUTOENCODER — {profile.display_name}")
    print("=" * 70)
    setup_training_devices()
    print(f"Model output: {config.MODEL_FOLDER}")
    print(f"Normal samples: {len(X_normal_df)}")
    if merge_live and live_oversample > 1:
        print(f"Live oversample factor: {live_oversample}")
    print(f"Threshold metric: {threshold_metric}")

    X_normal_np = X_normal_df.values
    X_validation_np, y_validation_np, X_test_np, y_test_np = _load_validation_test()

    label_encoder = load_label_encoder()
    validation_binary_true = convert_to_binary_labels(y_validation_np, label_encoder)
    test_binary_true = convert_to_binary_labels(y_test_np, label_encoder)

    autoencoder = build_autoencoder(X_normal_np.shape[1])
    compile_autoencoder(autoencoder)
    history = train_autoencoder(autoencoder, X_normal_np)
    save_autoencoder(autoencoder)
    plot_autoencoder_loss(history)

    normal_errors, validation_errors, test_errors = compute_reconstruction_errors(
        autoencoder, X_normal_np, X_validation_np, X_test_np
    )
    threshold = determine_threshold(
        normal_errors,
        validation_errors=validation_errors,
        validation_binary_true=validation_binary_true,
        threshold_metric=threshold_metric,
    )

    val_pred = detect_anomalies(validation_errors, threshold)
    test_pred = detect_anomalies(test_errors, threshold)
    val_metrics = evaluate_autoencoder(validation_binary_true, val_pred, "validation")
    test_metrics = evaluate_autoencoder(test_binary_true, test_pred, "test")

    results = {
        "dataset": config.ACTIVE_DATASET,
        "retrained_on_live": merge_live or bool(normal_data_path),
        "normal_samples": int(len(X_normal_np)),
        "live_oversample": int(live_oversample) if merge_live else 1,
        "threshold_metric": threshold_metric,
        "threshold": float(threshold),
        "validation": val_metrics,
        "test": test_metrics,
    }
    results_path = os.path.join(config.MODEL_FOLDER, "retrain_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nRetraining complete. Threshold: {threshold:.6f}")
    print(f"Test accuracy: {test_metrics['accuracy']:.4f} | Test F1: {test_metrics['f1']:.4f}")
    print(f"Results saved: {results_path}")
    print(f"Models saved: {os.path.abspath(config.MODEL_FOLDER)}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Retrain autoencoder on normal traffic (optionally merged with live capture)"
    )
    parser.add_argument(
        "--dataset",
        "-d",
        choices=VALID_DATASETS,
        default=None,
        help="Dataset profile (default: nsl_kdd)",
    )
    parser.add_argument(
        "--data",
        help="Processed normal-traffic CSV (overrides --merge-live)",
    )
    parser.add_argument(
        "--merge-live",
        action="store_true",
        help="Merge live captured normal flows into dataset normal training data",
    )
    parser.add_argument(
        "--save-merged",
        action="store_true",
        help="Save merged normal CSV alongside retraining",
    )
    parser.add_argument(
        "--live-oversample",
        type=int,
        default=5,
        help="Repeat live normal samples N times when merging (default: 5)",
    )
    parser.add_argument(
        "--threshold-metric",
        choices=("f1", "accuracy", "balanced"),
        default="balanced",
        help="Validation metric for threshold tuning (default: balanced)",
    )
    args = parser.parse_args()

    configure_project(args.dataset)
    retrain_autoencoder(
        normal_data_path=args.data,
        merge_live=args.merge_live,
        save_merged=args.save_merged,
        live_oversample=args.live_oversample,
        threshold_metric=args.threshold_metric,
    )


if __name__ == "__main__":
    main()
