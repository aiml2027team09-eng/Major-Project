#!/usr/bin/env python
"""
Live Hybrid IDS Monitor

Capture live network packets, extract flow features, and run
autoencoder anomaly detection + XGBoost attack classification.

Supports NSL-KDD, CICIDS2018, or both pipelines at once.

Usage:
  python live_monitor.py --list-interfaces
  python live_monitor.py --dataset nsl_kdd --interface "Wi-Fi"
  python live_monitor.py --dataset cicids2018 --interface "Wi-Fi"
  python live_monitor.py --dataset both --interface "Wi-Fi"
"""

import argparse
import os

from dataset_config import VALID_DATASETS, configure_project, get_profile, resolve_model_folder

LIVE_DATASET_CHOICES = (*VALID_DATASETS, "both")


def _validate_models(dataset_name):
    if dataset_name == "both":
        missing = []
        for name in VALID_DATASETS:
            profile = get_profile(name)
            model_path = os.path.join(
                resolve_model_folder(profile), "autoencoder.keras"
            )
            if not os.path.exists(model_path):
                missing.append(
                    f"{profile.display_name}: train with "
                    f"python {profile.preprocess_script} && "
                    f"python hybrid_ids_model.py --dataset {profile.name}"
                )
        if missing:
            raise FileNotFoundError(
                "Cannot run dual monitoring — missing models:\n"
                + "\n".join(f"  - {line}" for line in missing)
            )
        return

    profile = get_profile(dataset_name)
    model_path = os.path.join(resolve_model_folder(profile), "autoencoder.keras")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No trained model for {profile.display_name} at {model_path}\n"
            f"Run: python {profile.preprocess_script}\n"
            f"     python hybrid_ids_model.py --dataset {profile.name}"
        )


def main():
    parser = argparse.ArgumentParser(description="Live Hybrid IDS packet monitor")
    parser.add_argument(
        "--dataset",
        "-d",
        choices=LIVE_DATASET_CHOICES,
        default=None,
        help="Trained model dataset, or 'both' to run NSL-KDD + CICIDS2018 (default: nsl_kdd)",
    )
    parser.add_argument(
        "--interface",
        "-i",
        help="Network interface name (use --list-interfaces to see options)",
    )
    parser.add_argument(
        "--list-interfaces",
        action="store_true",
        help="List available capture interfaces and exit",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=5,
        help="Flow idle timeout in seconds before analysis (default: 5s)",
    )
    args = parser.parse_args()

    import live_ids.config as live_config
    if args.timeout:
        live_config.FLOW_IDLE_TIMEOUT = args.timeout

    if args.list_interfaces:
        from live_ids.main import print_interfaces

        print_interfaces()
        return

    dataset = args.dataset or "nsl_kdd"
    _validate_models(dataset)

    if dataset == "both":
        configure_project("nsl_kdd")
        from live_ids.main import run_dual_live_monitor

        print("Mode: dual pipeline (single capture, both models)\n")
        run_dual_live_monitor(interface=args.interface)
        return

    profile = configure_project(dataset)
    from live_ids.main import run_live_monitor

    print(f"Dataset: {profile.display_name}")
    print(f"Feature set: {profile.feature_set}")
    print(f"Models: {resolve_model_folder(profile)}\n")
    run_live_monitor(interface=args.interface)


if __name__ == "__main__":
    main()
