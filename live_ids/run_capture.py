"""Capture live network flows and save raw features for training."""

import threading
import time

import live_ids.config as config
from live_ids.capture_dataset import FlowDatasetWriter
from live_ids.flow_tracker import LiveFlowTracker, list_interfaces, pick_default_interface


def run_capture(
    interface=None,
    label=None,
    output_path=None,
    duration=None,
    capture_idle_timeout=5,
):
    """
    Capture live packets, extract flow features, and save to CSV.
    Does not run ML inference — use for collecting training data.
    """
    if interface is None:
        interface = pick_default_interface()
    if interface is None:
        raise RuntimeError(
            "No capture interface found. Run as Administrator or pass --interface."
        )

    if capture_idle_timeout is not None:
        config.FLOW_IDLE_TIMEOUT = capture_idle_timeout

    capture_label = label or config.DEFAULT_CAPTURE_LABEL
    writer = FlowDatasetWriter(output_path=output_path, default_label=capture_label)

    print("=" * 70)
    print("LIVE FLOW CAPTURE FOR TRAINING")
    print("=" * 70)
    print(f"Interface: {interface}")
    print(f"Label:     {capture_label}")
    print(f"Output:    {writer.output_path}")
    print("\nPress Ctrl+C to stop capture and save remaining flows.\n")

    def on_flow_complete(flow, feature_row):
        writer.add_flow(flow, feature_row, label=capture_label)

    tracker = LiveFlowTracker(
        interface=interface,
        on_flow_complete=on_flow_complete,
        feature_set=config.FEATURE_SET,
    )

    def save_loop():
        while tracker._running:
            time.sleep(config.CAPTURE_SAVE_INTERVAL)
            saved = writer.flush()
            if saved:
                print(f"[saved] +{saved} flows | total={writer.total_saved}")

    tracker.start()
    threading.Thread(target=save_loop, daemon=True).start()

    try:
        elapsed = 0
        while tracker._running:
            time.sleep(1)
            elapsed += 1
            if duration is not None and elapsed >= duration:
                print(f"\nDuration limit reached ({duration}s). Stopping capture...")
                break
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()
        writer.flush()
        print(f"\nCapture stopped. Total flows saved: {writer.total_saved}")
        print(f"Raw dataset: {writer.output_path}")
        if writer.total_saved == 0:
            print(
                "\nNo flows captured. Run PowerShell as Administrator, "
                "pick the active interface, and generate traffic (browse, ping)."
            )
        else:
            print("\nNext: python preprocess_captured.py")


def print_interfaces():
    interfaces = list_interfaces()
    print("Available network interfaces:")
    if not interfaces:
        print("  (none found — run PowerShell as Administrator)")
        return
    for name in interfaces:
        print(f"  - {name}")
