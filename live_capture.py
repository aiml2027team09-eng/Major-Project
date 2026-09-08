#!/usr/bin/env python

"""

Capture live network flows and save raw features to CSV for training.



Use this to collect training data from your network, then preprocess with:

  python preprocess_captured.py --dataset <nsl_kdd|cicids2018>



Prerequisites:

  1. Npcap installed (Windows)

  2. Run PowerShell as Administrator

  3. Preprocessing already run once for the chosen dataset



Usage:

  python live_capture.py --list-interfaces

  python live_capture.py --dataset nsl_kdd --interface "Wi-Fi"

  python live_capture.py --dataset cicids2018 --interface "Wi-Fi" --label Benign

"""



import argparse

from dataset_config import VALID_DATASETS, configure_project





def main():

    parser = argparse.ArgumentParser(

        description="Capture live flows and save raw features for training"

    )

    parser.add_argument(

        "--dataset",

        "-d",

        choices=VALID_DATASETS,

        default=None,

        help="Dataset profile (default: nsl_kdd)",

    )

    parser.add_argument("--interface", "-i", help="Network interface name")

    parser.add_argument(

        "--list-interfaces",

        action="store_true",

        help="List capture interfaces and exit",

    )

    parser.add_argument(

        "--label",

        help="Label for captured flows (default: normal/Benign per dataset)",

    )

    parser.add_argument(

        "--output",

        "-o",

        help="Output CSV path (default: captured_data/<dataset>/live_flows_raw.csv)",

    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Stop capture after N seconds (default: run until Ctrl+C)",
    )

    args = parser.parse_args()

    if args.list_interfaces:
        from live_ids.run_capture import print_interfaces

        print_interfaces()
        return

    profile = configure_project(args.dataset)
    from live_ids.run_capture import run_capture

    label = args.label or profile.normal_label

    run_capture(
        interface=args.interface,
        label=label,
        output_path=args.output,
        duration=args.duration,
    )





if __name__ == "__main__":

    main()

