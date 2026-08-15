#!/usr/bin/env python
"""
Live Hybrid IDS Monitor

Capture live network packets, extract flow features, and run
autoencoder anomaly detection + XGBoost attack classification.

Prerequisites:
  1. Install Npcap: https://npcap.com/#download
  2. pip install -r requirements.txt
  3. python preprocessing.py
  4. python hybrid_ids_model.py
  5. Run PowerShell as Administrator

Usage:
  python live_monitor.py --list-interfaces
  python live_monitor.py --interface "Wi-Fi"
  python live_monitor.py --interface "Ethernet"
"""

import argparse

from live_ids.main import print_interfaces, run_live_monitor


def main():
    parser = argparse.ArgumentParser(description="Live Hybrid IDS packet monitor")
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
    args = parser.parse_args()

    if args.list_interfaces:
        print_interfaces()
        return

    run_live_monitor(interface=args.interface)


if __name__ == "__main__":
    main()
