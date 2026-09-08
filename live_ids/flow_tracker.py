"""Live packet capture and bidirectional flow aggregation using Scapy."""

import threading
import time
from collections import deque
from dataclasses import dataclass, field

from scapy.all import IP, TCP, UDP, ICMP, sniff

import live_ids.config as config
from live_ids.feature_builder import build_feature_row as build_cicids_feature_row
from live_ids.nsl_kdd_feature_builder import (
    ConnectionWindowTracker,
    build_nsl_kdd_feature_row,
)


@dataclass
class FlowRecord:
    """Aggregated statistics for one network flow."""

    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    start_time: float
    last_time: float
    tot_fwd_pkts: int = 0
    tot_bwd_pkts: int = 0
    totlen_fwd: int = 0
    totlen_bwd: int = 0
    fwd_pkt_lens: list = field(default_factory=list)
    bwd_pkt_lens: list = field(default_factory=list)
    fwd_timestamps: list = field(default_factory=list)
    bwd_timestamps: list = field(default_factory=list)
    all_timestamps: list = field(default_factory=list)
    fwd_header_len: int = 0
    bwd_header_len: int = 0
    fwd_psh_flags: int = 0
    fin_cnt: int = 0
    syn_cnt: int = 0
    rst_cnt: int = 0
    psh_cnt: int = 0
    ack_cnt: int = 0
    urg_cnt: int = 0
    ece_cnt: int = 0
    init_fwd_win: int = -1
    init_bwd_win: int = -1

    @property
    def flow_duration_sec(self):
        return max(self.last_time - self.start_time, 0.0)

    def summary(self):
        return f"{self.src_ip}:{self.src_port} -> {self.dst_ip}:{self.dst_port} proto={self.protocol}"


def _flow_key(src_ip, dst_ip, sport, dport, proto):
    """Canonical bidirectional key so A->B and B->A share one flow."""
    a = (src_ip, sport)
    b = (dst_ip, dport)
    if a <= b:
        return (a[0], a[1], b[0], b[1], proto)
    return (b[0], b[1], a[0], a[1], proto)


def _count_tcp_flag(flag_val, bit):
    return 1 if flag_val & bit else 0


class LiveFlowTracker:
    """Capture packets, aggregate flows, emit completed flows for analysis."""

    def __init__(self, interface=None, on_flow_complete=None, feature_set=None):
        self.interface = interface or config.INTERFACE
        self.on_flow_complete = on_flow_complete
        self.feature_set = feature_set or config.FEATURE_SET
        self._connection_tracker = (
            ConnectionWindowTracker()
            if self.feature_set in ("nsl_kdd", "both")
            else None
        )
        self._flows = {}
        self._flow_direction = {}
        self._completed_queue = deque()
        self._running = False
        self._lock = threading.Lock()
        self.stats = {
            "packets_captured": 0,
            "flows_completed": 0,
            "flows_analyzed": 0,
        }

    def _parse_packet(self, packet):
        if IP not in packet:
            return

        ip_layer = packet[IP]
        proto = int(ip_layer.proto)
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        sport = 0
        dport = 0
        payload_len = int(len(packet))
        header_len = 0
        tcp_flags = None
        window = 0

        if TCP in packet:
            tcp = packet[TCP]
            sport = int(tcp.sport)
            dport = int(tcp.dport)
            header_len = int(tcp.dataofs) * 4
            payload_len = int(len(tcp.payload))
            tcp_flags = int(tcp.flags)
            window = int(tcp.window)
        elif UDP in packet:
            udp = packet[UDP]
            sport = int(udp.sport)
            dport = int(udp.dport)
            header_len = 8
            payload_len = int(len(udp.payload))
        elif ICMP in packet:
            sport = 0
            dport = 0
            header_len = 8
            payload_len = max(int(len(packet)) - 20, 0)

        pkt_len = header_len + payload_len
        now = time.time()
        key = _flow_key(src_ip, dst_ip, sport, dport, proto)

        with self._lock:
            if len(self._flows) >= config.MAX_ACTIVE_FLOWS:
                return

            if key not in self._flows:
                self._flows[key] = FlowRecord(
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=sport,
                    dst_port=dport,
                    protocol=proto,
                    start_time=now,
                    last_time=now,
                )
                self._flow_direction[key] = (src_ip, sport)

            flow = self._flows[key]
            flow.last_time = now
            flow.all_timestamps.append(now)

            is_forward = (src_ip, sport) == self._flow_direction[key]
            if is_forward:
                flow.tot_fwd_pkts += 1
                flow.totlen_fwd += pkt_len
                flow.fwd_pkt_lens.append(pkt_len)
                flow.fwd_timestamps.append(now)
                flow.fwd_header_len += header_len
                if flow.init_fwd_win == -1 and window > 0:
                    flow.init_fwd_win = window
            else:
                flow.tot_bwd_pkts += 1
                flow.totlen_bwd += pkt_len
                flow.bwd_pkt_lens.append(pkt_len)
                flow.bwd_timestamps.append(now)
                flow.bwd_header_len += header_len
                if flow.init_bwd_win == -1 and window > 0:
                    flow.init_bwd_win = window

            if tcp_flags is not None:
                flow.fin_cnt += _count_tcp_flag(tcp_flags, 0x01)
                flow.syn_cnt += _count_tcp_flag(tcp_flags, 0x02)
                flow.rst_cnt += _count_tcp_flag(tcp_flags, 0x04)
                flow.psh_cnt += _count_tcp_flag(tcp_flags, 0x08)
                flow.ack_cnt += _count_tcp_flag(tcp_flags, 0x10)
                flow.urg_cnt += _count_tcp_flag(tcp_flags, 0x20)
                flow.ece_cnt += _count_tcp_flag(tcp_flags, 0x40)
                if is_forward and (tcp_flags & 0x08):
                    flow.fwd_psh_flags += 1

            self.stats["packets_captured"] += 1

    def _flush_idle_flows(self, force=False):
        now = time.time()
        to_remove = []

        with self._lock:
            for key, flow in self._flows.items():
                idle = now - flow.last_time
                total_pkts = flow.tot_fwd_pkts + flow.tot_bwd_pkts
                if total_pkts < config.MIN_PACKETS_PER_FLOW:
                    continue
                if force or idle >= config.FLOW_IDLE_TIMEOUT:
                    to_remove.append(key)

            for key in to_remove:
                flow = self._flows.pop(key)
                self._flow_direction.pop(key, None)
                feature_row = self._build_feature_row(flow)
                self._completed_queue.append((flow, feature_row))
                self.stats["flows_completed"] += 1
                if self.on_flow_complete:
                    self.on_flow_complete(flow, feature_row)

    def _build_feature_row(self, flow):
        if self.feature_set == "both":
            return {
                "nsl_kdd": build_nsl_kdd_feature_row(flow, self._connection_tracker),
                "cicids2018": build_cicids_feature_row(flow),
            }
        if self.feature_set == "nsl_kdd":
            return build_nsl_kdd_feature_row(flow, self._connection_tracker)
        return build_cicids_feature_row(flow)

    def _flush_loop(self):
        while self._running:
            self._flush_idle_flows()
            time.sleep(config.FLOW_FLUSH_INTERVAL)

    def _sniff_loop(self):
        while self._running:
            try:
                sniff(
                    iface=self.interface,
                    prn=self._parse_packet,
                    store=False,
                    timeout=1,
                )
            except OSError as exc:
                print(f"Capture error: {exc}")
                print("Run PowerShell as Administrator and verify Npcap is installed.")
                self._running = False
                break

    def start(self):
        self._running = True
        threading.Thread(target=self._flush_loop, daemon=True).start()
        threading.Thread(target=self._sniff_loop, daemon=True).start()

        print(f"Capturing on interface: {self.interface or '(default)'}")
        print(f"Flow idle timeout: {config.FLOW_IDLE_TIMEOUT}s")
        print("Press Ctrl+C to stop.\n")

    def run_until_interrupt(self):
        """Block until Ctrl+C, then stop capture."""
        self.start()
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping capture...")
            self.stop()

    def stop(self):
        self._running = False
        self._flush_idle_flows(force=True)

    def pop_completed_flows(self):
        items = []
        while self._completed_queue:
            items.append(self._completed_queue.popleft())
        return items


def list_interfaces():
    """Return available network interfaces for capture."""
    from scapy.all import get_if_list

    return get_if_list()


def pick_default_interface():
    """Pick first non-loopback interface."""
    interfaces = list_interfaces()
    for name in interfaces:
        lower = name.lower()
        if "loopback" not in lower and "lo" != lower:
            return name
    return interfaces[0] if interfaces else None
