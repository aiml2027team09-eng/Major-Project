"""Build CICIDS2018-compatible feature rows from aggregated flow statistics."""

import numpy as np

# Must match preprocessor.pkl numerical columns exactly
FEATURE_COLUMNS = [
    "Dst Port",
    "Protocol",
    "Flow Duration",
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "TotLen Fwd Pkts",
    "TotLen Bwd Pkts",
    "Fwd Pkt Len Max",
    "Fwd Pkt Len Min",
    "Fwd Pkt Len Mean",
    "Fwd Pkt Len Std",
    "Bwd Pkt Len Max",
    "Bwd Pkt Len Min",
    "Bwd Pkt Len Mean",
    "Bwd Pkt Len Std",
    "Flow Byts/s",
    "Flow Pkts/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Tot",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Tot",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd PSH Flags",
    "Fwd Header Len",
    "Bwd Header Len",
    "Fwd Pkts/s",
    "Bwd Pkts/s",
    "Pkt Len Min",
    "Pkt Len Max",
    "Pkt Len Mean",
    "Pkt Len Std",
    "Pkt Len Var",
    "FIN Flag Cnt",
    "SYN Flag Cnt",
    "RST Flag Cnt",
    "PSH Flag Cnt",
    "ACK Flag Cnt",
    "URG Flag Cnt",
    "ECE Flag Cnt",
    "Down/Up Ratio",
    "Pkt Size Avg",
    "Fwd Seg Size Avg",
    "Bwd Seg Size Avg",
    "Subflow Fwd Pkts",
    "Subflow Fwd Byts",
    "Subflow Bwd Pkts",
    "Subflow Bwd Byts",
    "Init Fwd Win Byts",
    "Init Bwd Win Byts",
    "Fwd Act Data Pkts",
    "Fwd Seg Size Min",
    "Active Mean",
    "Active Std",
    "Active Max",
    "Active Min",
    "Idle Mean",
    "Idle Std",
    "Idle Max",
    "Idle Min",
]


def _safe_stat(values, fn, default=0.0):
    if not values:
        return default
    return float(fn(values))


def _iat_stats(timestamps):
    if len(timestamps) < 2:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    iats = np.diff(np.sort(timestamps))
    iats_us = iats * 1_000_000  # convert seconds to microseconds (CIC scale)
    return (
        float(np.sum(iats_us)),
        float(np.mean(iats_us)),
        float(np.std(iats_us)) if len(iats_us) > 1 else 0.0,
        float(np.max(iats_us)),
        float(np.min(iats_us)),
    )


def _packet_stats(lengths):
    if not lengths:
        return 0, 0, 0.0, 0.0
    arr = np.array(lengths, dtype=float)
    return (
        int(np.min(arr)),
        int(np.max(arr)),
        float(np.mean(arr)),
        float(np.std(arr)) if len(arr) > 1 else 0.0,
    )


def build_feature_row(flow):
    """
    Convert a finalized FlowRecord into a dict matching CICIDS2018 columns.
    flow: FlowRecord from flow_tracker.py
    """
    duration_us = max(flow.flow_duration_sec * 1_000_000, 1.0)
    total_bytes = flow.totlen_fwd + flow.totlen_bwd
    total_pkts = flow.tot_fwd_pkts + flow.tot_bwd_pkts

    fwd_min, fwd_max, fwd_mean, fwd_std = _packet_stats(flow.fwd_pkt_lens)
    bwd_min, bwd_max, bwd_mean, bwd_std = _packet_stats(flow.bwd_pkt_lens)
    all_lens = flow.fwd_pkt_lens + flow.bwd_pkt_lens
    pkt_min, pkt_max, pkt_mean, pkt_std = _packet_stats(all_lens)
    pkt_var = pkt_std ** 2

    flow_iat_tot, flow_iat_mean, flow_iat_std, flow_iat_max, flow_iat_min = _iat_stats(
        flow.all_timestamps
    )
    fwd_iat_tot, fwd_iat_mean, fwd_iat_std, fwd_iat_max, fwd_iat_min = _iat_stats(
        flow.fwd_timestamps
    )
    bwd_iat_tot, bwd_iat_mean, bwd_iat_std, bwd_iat_max, bwd_iat_min = _iat_stats(
        flow.bwd_timestamps
    )

    down_up = (
        float(flow.tot_bwd_pkts / flow.tot_fwd_pkts)
        if flow.tot_fwd_pkts > 0
        else 0.0
    )
    pkt_size_avg = total_bytes / total_pkts if total_pkts > 0 else 0.0
    fwd_seg_avg = flow.totlen_fwd / flow.tot_fwd_pkts if flow.tot_fwd_pkts > 0 else 0.0
    bwd_seg_avg = flow.totlen_bwd / flow.tot_bwd_pkts if flow.tot_bwd_pkts > 0 else 0.0
    fwd_act_data = sum(1 for length in flow.fwd_pkt_lens if length > 0)

    active_mean = active_std = active_max = active_min = 0.0
    idle_mean = idle_std = idle_max = idle_min = 0.0
    if len(flow.all_timestamps) >= 2:
        gaps = np.diff(np.sort(flow.all_timestamps)) * 1_000_000
        active_mean = float(np.mean(gaps))
        active_std = float(np.std(gaps)) if len(gaps) > 1 else 0.0
        active_max = float(np.max(gaps))
        active_min = float(np.min(gaps))
        idle_mean, idle_std, idle_max, idle_min = (
            active_mean,
            active_std,
            active_max,
            active_min,
        )

    row = {
        "Dst Port": flow.dst_port,
        "Protocol": flow.protocol,
        "Flow Duration": duration_us,
        "Tot Fwd Pkts": flow.tot_fwd_pkts,
        "Tot Bwd Pkts": flow.tot_bwd_pkts,
        "TotLen Fwd Pkts": flow.totlen_fwd,
        "TotLen Bwd Pkts": flow.totlen_bwd,
        "Fwd Pkt Len Max": fwd_max,
        "Fwd Pkt Len Min": fwd_min,
        "Fwd Pkt Len Mean": fwd_mean,
        "Fwd Pkt Len Std": fwd_std,
        "Bwd Pkt Len Max": bwd_max,
        "Bwd Pkt Len Min": bwd_min,
        "Bwd Pkt Len Mean": bwd_mean,
        "Bwd Pkt Len Std": bwd_std,
        "Flow Byts/s": (total_bytes / duration_us) * 1_000_000 if duration_us > 0 else 0.0,
        "Flow Pkts/s": (total_pkts / duration_us) * 1_000_000 if duration_us > 0 else 0.0,
        "Flow IAT Mean": flow_iat_mean,
        "Flow IAT Std": flow_iat_std,
        "Flow IAT Max": flow_iat_max,
        "Flow IAT Min": flow_iat_min,
        "Fwd IAT Tot": fwd_iat_tot,
        "Fwd IAT Mean": fwd_iat_mean,
        "Fwd IAT Std": fwd_iat_std,
        "Fwd IAT Max": fwd_iat_max,
        "Fwd IAT Min": fwd_iat_min,
        "Bwd IAT Tot": bwd_iat_tot,
        "Bwd IAT Mean": bwd_iat_mean,
        "Bwd IAT Std": bwd_iat_std,
        "Bwd IAT Max": bwd_iat_max,
        "Bwd IAT Min": bwd_iat_min,
        "Fwd PSH Flags": flow.fwd_psh_flags,
        "Fwd Header Len": flow.fwd_header_len,
        "Bwd Header Len": flow.bwd_header_len,
        "Fwd Pkts/s": (flow.tot_fwd_pkts / duration_us) * 1_000_000 if duration_us > 0 else 0.0,
        "Bwd Pkts/s": (flow.tot_bwd_pkts / duration_us) * 1_000_000 if duration_us > 0 else 0.0,
        "Pkt Len Min": pkt_min,
        "Pkt Len Max": pkt_max,
        "Pkt Len Mean": pkt_mean,
        "Pkt Len Std": pkt_std,
        "Pkt Len Var": pkt_var,
        "FIN Flag Cnt": flow.fin_cnt,
        "SYN Flag Cnt": flow.syn_cnt,
        "RST Flag Cnt": flow.rst_cnt,
        "PSH Flag Cnt": flow.psh_cnt,
        "ACK Flag Cnt": flow.ack_cnt,
        "URG Flag Cnt": flow.urg_cnt,
        "ECE Flag Cnt": flow.ece_cnt,
        "Down/Up Ratio": down_up,
        "Pkt Size Avg": pkt_size_avg,
        "Fwd Seg Size Avg": fwd_seg_avg,
        "Bwd Seg Size Avg": bwd_seg_avg,
        "Subflow Fwd Pkts": flow.tot_fwd_pkts,
        "Subflow Fwd Byts": flow.totlen_fwd,
        "Subflow Bwd Pkts": flow.tot_bwd_pkts,
        "Subflow Bwd Byts": flow.totlen_bwd,
        "Init Fwd Win Byts": flow.init_fwd_win,
        "Init Bwd Win Byts": flow.init_bwd_win,
        "Fwd Act Data Pkts": fwd_act_data,
        "Fwd Seg Size Min": fwd_min if flow.tot_fwd_pkts > 0 else 0,
        "Active Mean": active_mean,
        "Active Std": active_std,
        "Active Max": active_max,
        "Active Min": active_min,
        "Idle Mean": idle_mean,
        "Idle Std": idle_std,
        "Idle Max": idle_max,
        "Idle Min": idle_min,
    }

    return row
