"""Live hybrid IDS monitor — capture, detect, classify."""

import os
import threading
import time

from live_ids.config import ALERT_LOG, FLOW_FLUSH_INTERVAL
from live_ids.detector import LiveHybridDetector
from live_ids.flow_tracker import LiveFlowTracker, list_interfaces, pick_default_interface


def run_live_monitor(interface=None):
    """Start live packet capture and hybrid anomaly detection."""
    if interface is None:
        interface = pick_default_interface()

    if interface is None:
        raise RuntimeError(
            "No capture interface found. Run as Administrator or pass --interface."
        )

    os.makedirs(os.path.dirname(ALERT_LOG) or ".", exist_ok=True)

    print("=" * 70)
    print("LIVE HYBRID INTRUSION DETECTION")
    print("=" * 70)

    detector = LiveHybridDetector()
    pending = []
    pending_lock = threading.Lock()

    def on_flow_complete(flow, feature_row):
        with pending_lock:
            pending.append((flow, feature_row))

    tracker = LiveFlowTracker(interface=interface, on_flow_complete=on_flow_complete)

    def analysis_loop():
        while tracker._running:
            time.sleep(FLOW_FLUSH_INTERVAL)
            with pending_lock:
                if not pending:
                    batch = []
                else:
                    batch = pending.copy()
                    pending.clear()
            if batch:
                alerts = detector.analyze_flows(batch)
                tracker.stats["flows_analyzed"] += len(batch)
                if alerts:
                    print(f"  -> {len(alerts)} anomaly alert(s) in this batch")

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
