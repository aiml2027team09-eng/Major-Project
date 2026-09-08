"""Build NSL-KDD raw feature rows from live flow statistics."""

import json
import os
from collections import deque

# NSL-KDD connection window (seconds) used for count / host-based features
CONNECTION_WINDOW_SEC = 2.0

# Well-known port -> NSL-KDD service name
PORT_TO_SERVICE = {
    20: "ftp_data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "domain_u",
    80: "http",
    110: "pop_3",
    143: "imap",
    443: "http",
    445: "private",
    3306: "sql_net",
    8080: "http",
}

RAW_FEATURE_COLUMNS = None


def _load_raw_columns(data_folder=None):
    global RAW_FEATURE_COLUMNS
    if data_folder is None:
        from live_ids.config import DATA_FOLDER

        data_folder = DATA_FOLDER

    metadata_path = os.path.join(data_folder, "live_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
        return metadata["raw_feature_columns"]

    # Fallback if metadata missing (constant column already dropped)
    RAW_FEATURE_COLUMNS = [
        "duration",
        "protocol_type",
        "service",
        "flag",
        "src_bytes",
        "dst_bytes",
        "land",
        "wrong_fragment",
        "urgent",
        "hot",
        "num_failed_logins",
        "logged_in",
        "num_compromised",
        "root_shell",
        "su_attempted",
        "num_root",
        "num_file_creations",
        "num_shells",
        "num_access_files",
        "is_host_login",
        "is_guest_login",
        "count",
        "srv_count",
        "serror_rate",
        "srv_serror_rate",
        "rerror_rate",
        "srv_rerror_rate",
        "same_srv_rate",
        "diff_srv_rate",
        "srv_diff_host_rate",
        "dst_host_count",
        "dst_host_srv_count",
        "dst_host_same_srv_rate",
        "dst_host_diff_srv_rate",
        "dst_host_same_src_port_rate",
        "dst_host_srv_diff_host_rate",
        "dst_host_serror_rate",
        "dst_host_srv_serror_rate",
        "dst_host_rerror_rate",
        "dst_host_srv_rerror_rate",
    ]
    return RAW_FEATURE_COLUMNS


def _protocol_type(proto_num):
    if proto_num == 6:
        return "tcp"
    if proto_num == 17:
        return "udp"
    if proto_num == 1:
        return "icmp"
    return "tcp"


def _service_from_port(port):
    if port in PORT_TO_SERVICE:
        return PORT_TO_SERVICE[port]
    if port == 0:
        return "other"
    if port < 1024:
        return "private"
    return "private"


def _tcp_flag_label(flow):
    if flow.protocol != 6:
        return "OTH"

    has_syn = flow.syn_cnt > 0
    has_ack = flow.ack_cnt > 0
    has_rst = flow.rst_cnt > 0
    has_fin = flow.fin_cnt > 0

    if has_rst and not has_ack:
        return "REJ"
    if has_syn and not has_ack:
        return "S0"
    if has_syn and has_ack and has_fin:
        return "SF"
    if has_syn and has_ack:
        return "S1"
    if has_rst:
        return "RSTO"
    if has_fin:
        return "SF"
    return "OTH"


def _rate(count, total):
    if total <= 0:
        return 0.0
    return float(count) / float(total)


class ConnectionWindowTracker:
    """Track recent connections for NSL-KDD count / host-based features."""

    def __init__(self, window_sec=CONNECTION_WINDOW_SEC):
        self.window_sec = window_sec
        self._history = deque()

    def _prune(self, now):
        cutoff = now - self.window_sec
        while self._history and self._history[0]["time"] < cutoff:
            self._history.popleft()

    def snapshot_for_flow(self, flow):
        """Return connection stats for flow using prior window (exclude current)."""
        now = flow.last_time
        self._prune(now)

        dst_ip = flow.dst_ip
        service = _service_from_port(flow.dst_port)
        src_port = flow.src_port

        same_host = [e for e in self._history if e["dst_ip"] == dst_ip]
        same_service = [e for e in same_host if e["service"] == service]
        same_src_port = [e for e in same_host if e["src_port"] == src_port]

        count = len(same_host) + 1
        srv_count = len(same_service) + 1
        dst_host_count = count

        host_services = {e["service"] for e in same_host}
        host_services.add(service)
        diff_srv = max(len(host_services) - 1, 0)

        same_srv_rate = _rate(len(same_service), count)
        diff_srv_rate = _rate(diff_srv, count)
        srv_diff_host_rate = 0.0

        dst_host_srv_count = srv_count
        dst_host_same_srv_rate = same_srv_rate
        dst_host_diff_srv_rate = diff_srv_rate
        dst_host_same_src_port_rate = _rate(len(same_src_port), dst_host_count)
        dst_host_srv_diff_host_rate = srv_diff_host_rate

        return {
            "count": count,
            "srv_count": srv_count,
            "same_srv_rate": same_srv_rate,
            "diff_srv_rate": diff_srv_rate,
            "srv_diff_host_rate": srv_diff_host_rate,
            "dst_host_count": dst_host_count,
            "dst_host_srv_count": dst_host_srv_count,
            "dst_host_same_srv_rate": dst_host_same_srv_rate,
            "dst_host_diff_srv_rate": dst_host_diff_srv_rate,
            "dst_host_same_src_port_rate": dst_host_same_src_port_rate,
            "dst_host_srv_diff_host_rate": dst_host_srv_diff_host_rate,
        }

    def register_flow(self, flow):
        self._prune(flow.last_time)
        self._history.append(
            {
                "time": flow.last_time,
                "dst_ip": flow.dst_ip,
                "service": _service_from_port(flow.dst_port),
                "src_port": flow.src_port,
            }
        )


def build_nsl_kdd_feature_row(flow, connection_tracker=None):
    """Map a completed FlowRecord to NSL-KDD raw columns."""
    columns = _load_raw_columns()
    service = _service_from_port(flow.dst_port)
    flag = _tcp_flag_label(flow)

    if connection_tracker is not None:
        conn_stats = connection_tracker.snapshot_for_flow(flow)
        connection_tracker.register_flow(flow)
    else:
        conn_stats = {
            "count": 1,
            "srv_count": 1,
            "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0,
            "srv_diff_host_rate": 0.0,
            "dst_host_count": 1,
            "dst_host_srv_count": 1,
            "dst_host_same_srv_rate": 1.0,
            "dst_host_diff_srv_rate": 0.0,
            "dst_host_same_src_port_rate": 1.0,
            "dst_host_srv_diff_host_rate": 0.0,
        }

    row = {
        "duration": max(flow.flow_duration_sec, 0.0),
        "protocol_type": _protocol_type(flow.protocol),
        "service": service,
        "flag": flag,
        "src_bytes": float(flow.totlen_fwd),
        "dst_bytes": float(flow.totlen_bwd),
        "land": 1 if flow.src_ip == flow.dst_ip else 0,
        "wrong_fragment": 0,
        "urgent": 0,
        "hot": 0,
        "num_failed_logins": 0,
        "logged_in": 1 if flow.tot_fwd_pkts > 0 and flow.tot_bwd_pkts > 0 else 0,
        "num_compromised": 0,
        "root_shell": 0,
        "su_attempted": 0,
        "num_root": 0,
        "num_file_creations": 0,
        "num_shells": 0,
        "num_access_files": 0,
        "is_host_login": 0,
        "is_guest_login": 0,
        "serror_rate": 0.0,
        "srv_serror_rate": 0.0,
        "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0,
        **conn_stats,
        "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0,
        "dst_host_rerror_rate": 0.0,
        "dst_host_srv_rerror_rate": 0.0,
    }

    return {col: row.get(col, 0) for col in columns}
