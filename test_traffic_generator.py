# test_traffic_generator.py
"""Generate test anomalous network traffic across either Wi-Fi or Loopback."""

import argparse
import random
import socket
import time


def get_default_ip():
    """Detect local IP on the active Wi-Fi or Ethernet adapter."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def simulate_port_scan(target_ip, num_ports=120):
    """Simulate reconnaissance/probe traffic (unusual port access frequency)."""
    print(f"\n[+] Generating Port Scan (Probe) against {target_ip} across {num_ports} ports...")
    success = 0
    for port in range(21, 21 + num_ports):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.04)
            s.connect_ex((target_ip, port))
            s.close()
            success += 1
        except Exception:
            pass
        time.sleep(0.01)
    print(f"[✓] Sent {num_ports} connection attempts to {target_ip}.")


def simulate_udp_burst(target_ip, count=250):
    """Simulate high-rate UDP packet burst anomaly."""
    print(f"\n[+] Generating UDP packet burst against {target_ip} ({count} packets)...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = random.randbytes(512)
    for i in range(count):
        port = random.randint(10000, 60000)
        try:
            # Send at least 2 packets per destination port to form valid bidirectional flow
            s.sendto(payload, (target_ip, port))
            s.sendto(payload, (target_ip, port))
        except Exception:
            pass
        time.sleep(0.005)
    s.close()
    print(f"[✓] Sent {count * 2} UDP packets to {target_ip}.")


def main():
    parser = argparse.ArgumentParser(description="Generate anomalous traffic for Live IDS testing")
    parser.add_argument(
        "--target",
        "-t",
        default=None,
        help="Target IP address (default: your local machine IP)",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["scan", "burst", "both"],
        default=None,
        help="Traffic mode to generate",
    )
    args = parser.parse_args()

    target_ip = args.target or get_default_ip()
    print("=" * 60)
    print("HYBRID IDS TRAFFIC GENERATOR")
    print(f"Target Destination: {target_ip}")
    print("=" * 60)

    mode = args.mode
    if not mode:
        print("Choose test traffic to generate:")
        print("  1. Port Scan (Probe / Reconnaissance)")
        print("  2. UDP Burst (Flooding / Anomaly)")
        print("  3. Both (Full Anomaly Suite)")
        choice = input("\nEnter choice (1/2/3) [default: 3]: ").strip()
        if choice == "1":
            mode = "scan"
        elif choice == "2":
            mode = "burst"
        else:
            mode = "both"

    if mode in ("scan", "both"):
        simulate_port_scan(target_ip)
    if mode in ("burst", "both"):
        simulate_udp_burst(target_ip)

    print("\n[✓] Traffic generation completed.")
    print("Give the live monitor 5-10 seconds to flush flows and log alerts!")


if __name__ == "__main__":
    main()
