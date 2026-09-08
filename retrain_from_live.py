#!/usr/bin/env python
"""
Capture live normal traffic, preprocess, and retrain the autoencoder.

Usage:
  python retrain_from_live.py --dataset both --capture-seconds 120
  python retrain_from_live.py --dataset nsl_kdd --skip-capture --merge-live
  python retrain_from_live.py --dataset cicids2018 --interface "Wi-Fi"
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

from dataset_config import VALID_DATASETS, captured_raw_csv, configure_project, get_profile

DATASET_CHOICES = VALID_DATASETS + ("both",)


def _save_baseline_metrics(dataset_name):
    """Copy current metrics before retrain for before/after comparison."""
    src = os.path.join("result_images", dataset_name, "metrics_summary.json")
    dst = os.path.join("result_images", dataset_name, "metrics_summary_before_retrain.json")
    if os.path.exists(src):
        shutil.copy2(src, dst)
        return json.load(open(src))
    return None


def _run_one_dataset(args, dataset_name):
    profile = configure_project(dataset_name)
    merge_live = not args.no_merge_live
    raw_csv = captured_raw_csv(profile)

    baseline = _save_baseline_metrics(dataset_name)
    if baseline:
        print(f"\nBaseline test accuracy ({profile.display_name}): "
              f"{baseline['Autoencoder'].get('test_accuracy', 0):.4f}")

    if not args.skip_capture:
        interface = args.interface
        if interface is None:
            from live_ids.flow_tracker import pick_default_interface

            interface = pick_default_interface()
        if interface is None:
            raise RuntimeError(
                "No capture interface. Run PowerShell as Administrator, "
                "pass --interface, or use --skip-capture."
            )

        print(f"\nCapturing {args.capture_seconds}s on '{interface}' ({profile.display_name})...")
        result = subprocess.run(
            [
                sys.executable,
                "live_capture.py",
                "--dataset",
                dataset_name,
                "--interface",
                interface,
                "--duration",
                str(args.capture_seconds),
            ],
            check=False,
        )
        if result.returncode != 0:
            print(f"Warning: capture exited with code {result.returncode}")

    if not os.path.exists(raw_csv):
        raise FileNotFoundError(
            f"No captured data at {raw_csv}.\n"
            f"Run as Administrator:\n"
            f"  python live_capture.py --dataset {dataset_name} --interface \"Wi-Fi\""
        )

    import live_ids.config as live_config

    print("\n" + "=" * 70)
    print(f"PREPROCESSING CAPTURED FLOWS — {profile.display_name}")
    print("=" * 70)

    from live_ids.prepare_training import preprocess_captured_for_training

    preprocess_captured_for_training(
        raw_csv_path=raw_csv,
        output_folder=live_config.PROCESSED_LIVE_FOLDER,
        update_autoencoder_normal=False,
    )

    print("\n" + "=" * 70)
    print(f"RETRAINING AUTOENCODER — {profile.display_name}")
    print("=" * 70)

    configure_project(dataset_name)
    from retrain_autoencoder import retrain_autoencoder

    results = retrain_autoencoder(
        merge_live=merge_live,
        save_merged=True,
        live_oversample=args.live_oversample,
        threshold_metric=args.threshold_metric,
    )

    print("\nRegenerating result images...")
    subprocess.run(
        [sys.executable, "generate_result_images.py", "--dataset", dataset_name],
        check=False,
    )

    after_path = os.path.join("result_images", dataset_name, "metrics_summary.json")
    after = json.load(open(after_path)) if os.path.exists(after_path) else None

    if baseline and after:
        b_acc = baseline["Autoencoder"]["test_accuracy"]
        a_acc = after["Autoencoder"]["test_accuracy"]
        b_f1 = baseline["Autoencoder"]["test_f1"]
        a_f1 = after["Autoencoder"]["test_f1"]
        delta_acc = a_acc - b_acc
        delta_f1 = a_f1 - b_f1
        print(
            f"\n{profile.display_name} - AE test accuracy: {b_acc:.4f} -> {a_acc:.4f} "
            f"({delta_acc:+.4f}) | F1: {b_f1:.4f} -> {a_f1:.4f} ({delta_f1:+.4f})"
        )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Capture live normal traffic and retrain autoencoder"
    )
    parser.add_argument(
        "--dataset",
        "-d",
        choices=DATASET_CHOICES,
        default="both",
    )
    parser.add_argument("--interface", "-i", default=None)
    parser.add_argument(
        "--capture-seconds",
        type=int,
        default=120,
        help="Capture duration in seconds (default: 120)",
    )
    parser.add_argument(
        "--skip-capture",
        action="store_true",
        help="Use existing captured_data CSV",
    )
    parser.add_argument(
        "--no-merge-live",
        action="store_true",
        help="Retrain only on captured flows (do not merge with dataset normal data)",
    )
    parser.add_argument(
        "--live-oversample",
        type=int,
        default=5,
        help="Repeat live normal samples when merging (default: 5)",
    )
    parser.add_argument(
        "--threshold-metric",
        choices=("f1", "accuracy", "balanced"),
        default="balanced",
        help="Validation metric for threshold tuning (default: balanced)",
    )
    args = parser.parse_args()

    datasets = list(VALID_DATASETS) if args.dataset == "both" else [args.dataset]
    all_results = {}

    for dataset_name in datasets:
        all_results[dataset_name] = _run_one_dataset(args, dataset_name)

    if len(datasets) > 1:
        print("\nGenerating combined comparison images...")
        subprocess.run(
            [sys.executable, "generate_result_images.py", "--dataset", "both"],
            check=False,
        )

    summary_path = os.path.join("result_images", "retrain_comparison.json")
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nRetrain summary saved: {summary_path}")
    print(f"Done. Monitor: python live_monitor.py --dataset both --interface \"Wi-Fi\"")


if __name__ == "__main__":
    main()
