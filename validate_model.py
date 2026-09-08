#!/usr/bin/env python
"""
Validate the hybrid IDS when live traffic has no attacks.

Live networks are mostly normal — you cannot prove attack detection from live
capture alone. This script validates the model using:

  1. Full held-out test set (standard benchmark)
  2. Benign-only subset  → false positive rate (simulates your normal live network)
  3. Attack-only subset  → detection recall (proves the model catches attacks)
  4. Live captured normal flows (if available) → false alarms on YOUR network

Usage:
  python validate_model.py --dataset nsl_kdd
  python validate_model.py --dataset both
  python validate_model.py --dataset cicids2018 --include-live
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from xgboost import XGBClassifier

from dataset_config import VALID_DATASETS, configure_project, get_profile, processed_live_folder
from hybrid_ids.anomaly_detection import calculate_reconstruction_error, detect_anomalies
from hybrid_ids.binary_labels import convert_to_binary_labels, load_label_encoder
import hybrid_ids.config as config


def _load_threshold(model_folder: str) -> float:
    with open(os.path.join(model_folder, "threshold.json"), encoding="utf-8") as f:
        return float(json.load(f)["threshold"])


def _metrics(binary_true, binary_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(binary_true, binary_pred)),
        "precision": float(precision_score(binary_true, binary_pred, zero_division=0)),
        "recall": float(recall_score(binary_true, binary_pred, zero_division=0)),
        "f1": float(f1_score(binary_true, binary_pred, zero_division=0)),
    }


def _false_positive_rate(binary_true, binary_pred) -> float:
    """Fraction of normal samples incorrectly flagged as attack."""
    normal_mask = binary_true == 0
    if normal_mask.sum() == 0:
        return 0.0
    return float((binary_pred[normal_mask] == 1).mean())


def _attack_detection_rate(binary_true, binary_pred) -> float:
    """Fraction of attacks correctly flagged (same as recall on attacks)."""
    attack_mask = binary_true == 1
    if attack_mask.sum() == 0:
        return 0.0
    return float((binary_pred[attack_mask] == 1).mean())


def validate_dataset(include_live: bool = True) -> dict:
    profile = get_profile(config.ACTIVE_DATASET)
    model_folder = config.MODEL_FOLDER

    X_test = pd.read_csv(os.path.join(config.DATA_FOLDER, "X_test.csv")).astype(np.float32)
    y_test = pd.read_csv(os.path.join(config.DATA_FOLDER, "y_test.csv"))["Label"].values
    X_test_np = X_test.values

    label_encoder = load_label_encoder()
    binary_true = convert_to_binary_labels(y_test, label_encoder)

    autoencoder = tf.keras.models.load_model(os.path.join(model_folder, "autoencoder.keras"))
    xgb = XGBClassifier()
    xgb.load_model(os.path.join(model_folder, "xgboost_model.json"))
    threshold = _load_threshold(model_folder)

    errors = calculate_reconstruction_error(autoencoder, X_test_np)
    ae_pred = detect_anomalies(errors, threshold)

    benign_code = next(
        i
        for i, label in enumerate(label_encoder.classes_)
        if str(label).upper() in ("BENIGN", "NORMAL")
    )

    # --- Full test set ---
    full_ae = _metrics(binary_true, ae_pred)

    hybrid_pred = np.full(len(y_test), benign_code, dtype=int)
    anomaly_idx = np.where(ae_pred == 1)[0]
    if len(anomaly_idx) > 0:
        hybrid_pred[anomaly_idx] = xgb.predict(X_test_np[anomaly_idx])

    full_hybrid_acc = float(accuracy_score(y_test, hybrid_pred))

    # --- Benign-only (simulates live network with no attacks) ---
    benign_mask = binary_true == 0
    benign_ae = _metrics(binary_true[benign_mask], ae_pred[benign_mask])
    benign_fpr = _false_positive_rate(binary_true[benign_mask], ae_pred[benign_mask])

    # --- Attack-only (proves detection works offline) ---
    attack_mask = binary_true == 1
    attack_ae = _metrics(binary_true[attack_mask], ae_pred[attack_mask])
    attack_detection = _attack_detection_rate(binary_true[attack_mask], ae_pred[attack_mask])

    report = {
        "dataset": config.ACTIVE_DATASET,
        "validated_at": datetime.now().isoformat(timespec="seconds"),
        "threshold": threshold,
        "test_samples": int(len(y_test)),
        "benign_samples": int(benign_mask.sum()),
        "attack_samples": int(attack_mask.sum()),
        "full_test_set": {
            "autoencoder": full_ae,
            "hybrid_accuracy": full_hybrid_acc,
        },
        "benign_only_simulation": {
            "description": "Simulates live network with no attacks — lower FPR is better",
            "autoencoder": benign_ae,
            "false_positive_rate": benign_fpr,
            "false_alarms": int((ae_pred[benign_mask] == 1).sum()),
            "total_benign": int(benign_mask.sum()),
        },
        "attack_only_validation": {
            "description": "Proves model detects known attacks offline — higher detection rate is better",
            "autoencoder": attack_ae,
            "attack_detection_rate": attack_detection,
            "attacks_detected": int((ae_pred[attack_mask] == 1).sum()),
            "total_attacks": int(attack_mask.sum()),
        },
    }

    if include_live:
        live_path = os.path.join(
            processed_live_folder(profile), "X_normal_autoencoder.csv"
        )
        if os.path.exists(live_path):
            X_live = pd.read_csv(live_path).astype(np.float32).values
            live_errors = calculate_reconstruction_error(autoencoder, X_live)
            live_pred = detect_anomalies(live_errors, threshold)
            live_fpr = float(live_pred.mean())
            report["live_captured_normal"] = {
                "description": "Your captured live normal traffic — should have ~0% false alarms",
                "samples": int(len(X_live)),
                "false_alarms": int(live_pred.sum()),
                "false_positive_rate": live_fpr,
            }
        else:
            report["live_captured_normal"] = {
                "description": "No live capture yet",
                "hint": f"Run: python live_capture.py --dataset {profile.name} --interface \"Wi-Fi\" --duration 120",
            }

    return report


def _print_report(report: dict) -> None:
    ds = report["dataset"]
    print("\n" + "=" * 70)
    print(f"VALIDATION REPORT — {ds.upper()}")
    print("=" * 70)

    print("\n[1] FULL TEST SET (standard benchmark)")
    ae = report["full_test_set"]["autoencoder"]
    print(f"    AE accuracy={ae['accuracy']:.4f}  precision={ae['precision']:.4f}  "
          f"recall={ae['recall']:.4f}  F1={ae['f1']:.4f}")
    print(f"    Hybrid accuracy={report['full_test_set']['hybrid_accuracy']:.4f}")

    sim = report["benign_only_simulation"]
    print("\n[2] BENIGN-ONLY (simulates your normal live network)")
    print(f"    False positive rate: {sim['false_positive_rate']:.4f}  "
          f"({sim['false_alarms']}/{sim['total_benign']} false alarms)")
    print("    -> Lower is better. Retrain on live normal traffic to reduce this.")

    atk = report["attack_only_validation"]
    print("\n[3] ATTACK-ONLY (offline proof that detection works)")
    print(f"    Attack detection rate: {atk['attack_detection_rate']:.4f}  "
          f"({atk['attacks_detected']}/{atk['total_attacks']} attacks caught)")
    print("    -> Higher is better. Use this in viva when live network has no attacks.")

    live = report.get("live_captured_normal", {})
    print("\n[4] LIVE CAPTURED NORMAL TRAFFIC")
    if "false_positive_rate" in live:
        print(f"    False positive rate: {live['false_positive_rate']:.4f}  "
              f"({live['false_alarms']}/{live['samples']} false alarms)")
    else:
        print(f"    {live.get('hint', live.get('description', 'N/A'))}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate IDS when live network has no anomalies"
    )
    parser.add_argument(
        "--dataset", "-d", choices=[*VALID_DATASETS, "both"], default="both"
    )
    parser.add_argument(
        "--include-live",
        action="store_true",
        default=True,
        help="Include live captured normal flows if available (default: on)",
    )
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="Skip live captured normal evaluation",
    )
    args = parser.parse_args()

    datasets = list(VALID_DATASETS) if args.dataset == "both" else [args.dataset]
    include_live = args.include_live and not args.no_live
    all_reports = {}

    for name in datasets:
        configure_project(name)
        report = validate_dataset(include_live=include_live)
        all_reports[name] = report
        _print_report(report)

        out_path = os.path.join(
            config.MODEL_FOLDER, "validation_report.json"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nSaved: {out_path}")

    combined_path = os.path.join("result_images", "validation_summary.json")
    os.makedirs("result_images", exist_ok=True)
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_reports, f, indent=2)

    print("\n" + "=" * 70)
    print("HOW TO IMPROVE WHEN LIVE NETWORK HAS NO ATTACKS")
    print("=" * 70)
    print("""
  1. Reduce false positives (benign-only FPR):
     python live_capture.py --dataset nsl_kdd --interface "Wi-Fi" --duration 180
     python retrain_from_live.py --dataset nsl_kdd --skip-capture --threshold-metric accuracy

  2. Validate attack detection offline (attack-only rate above).

  3. Optional controlled lab: run nmap/hydra on YOUR VM, then live_monitor.py.

  4. Dashboard: python run_dashboard.py
""")


if __name__ == "__main__":
    main()
