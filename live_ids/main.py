"""Live hybrid IDS monitor — capture, detect, classify."""

import os
import threading
import time

from dataset_config import VALID_DATASETS, get_profile
import live_ids.config as config
from live_ids.detector import LiveHybridDetector, load_detectors_for_datasets
from live_ids.flow_tracker import LiveFlowTracker, list_interfaces, pick_default_interface


def _split_dual_batch(batch):
    """Split a dual-feature batch into per-dataset (flow, feature_row) lists."""
    split = {name: [] for name in VALID_DATASETS}
    for flow, feature_row in batch:
        if isinstance(feature_row, dict):
            for name in VALID_DATASETS:
                if name in feature_row:
                    split[name].append((flow, feature_row[name]))
        else:
            split[config.ACTIVE_DATASET].append((flow, feature_row))
    return split


def run_live_monitor(interface=None, feature_set=None):
    """Start live packet capture and hybrid anomaly detection (single dataset)."""
    if interface is None:
        interface = pick_default_interface()

    if interface is None:
        raise RuntimeError(
            "No capture interface found. Run as Administrator or pass --interface."
        )

    profile = get_profile(config.ACTIVE_DATASET)
    os.makedirs(os.path.dirname(config.ALERT_LOG) or ".", exist_ok=True)

    print("=" * 70)
    print("LIVE HYBRID INTRUSION DETECTION")
    print(f"Dataset: {profile.display_name}")
    print("=" * 70)

    detector = LiveHybridDetector(profile=profile)
    _run_capture_loop(
        interface=interface,
        detectors=[detector],
        feature_set=feature_set or profile.feature_set,
    )


def run_dual_live_monitor(interface=None):
    """Capture once and run NSL-KDD + CICIDS2018 models on every flow."""
    if interface is None:
        interface = pick_default_interface()

    if interface is None:
        raise RuntimeError(
            "No capture interface found. Run as Administrator or pass --interface."
        )

    print("=" * 70)
    print("LIVE HYBRID INTRUSION DETECTION — DUAL PIPELINE")
    print("Models: NSL-KDD + CICIDS2018")
    print("=" * 70)

    detectors = load_detectors_for_datasets(VALID_DATASETS)
    _run_capture_loop(interface=interface, detectors=detectors, feature_set="both")


def _run_capture_loop(interface, detectors, feature_set):
    pending = []
    pending_lock = threading.Lock()
    detector_by_key = {detector.dataset_key: detector for detector in detectors}

    def on_flow_complete(flow, feature_row):
        with pending_lock:
            pending.append((flow, feature_row))

    tracker = LiveFlowTracker(
        interface=interface,
        on_flow_complete=on_flow_complete,
        feature_set=feature_set,
    )

    def analysis_loop():
        while tracker._running:
            time.sleep(config.FLOW_FLUSH_INTERVAL)
            with pending_lock:
                if not pending:
                    batch = []
                else:
                    batch = pending.copy()
                    pending.clear()

            if batch:
                if feature_set == "both":
                    split = _split_dual_batch(batch)
                    total_alerts = 0
                    for name, pairs in split.items():
                        if not pairs:
                            continue
                        alerts = detector_by_key[name].analyze_flows(pairs)
                        total_alerts += len(alerts)
                    if total_alerts:
                        print(f"  -> {total_alerts} anomaly alert(s) in this batch")
                else:
                    alerts = detectors[0].analyze_flows(batch)
                    if alerts:
                        print(f"  -> {len(alerts)} anomaly alert(s) in this batch")

                tracker.stats["flows_analyzed"] += len(batch)

            print(
                f"[stats] packets={tracker.stats['packets_captured']} "
                f"flows_done={tracker.stats['flows_completed']} "
                f"analyzed={tracker.stats['flows_analyzed']}"
            )

    tracker.start()
    threading.Thread(target=analysis_loop, daemon=True).start()
    tracker.run_until_interrupt()


def print_interfaces():
    interfaces = list_interfaces()
    print("Available network interfaces:")
    if not interfaces:
        print("  (none found — run PowerShell as Administrator)")
        return
    for name in interfaces:
        print(f"  - {name}")
