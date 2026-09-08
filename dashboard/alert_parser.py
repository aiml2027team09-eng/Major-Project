"""Parse live IDS alert logs into structured DataFrames."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ALERT_LINE_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s*\[(?P<dataset>[^\]]+)\]\s*ANOMALY\s*\|\s*"
    r"(?P<flow>.+?)\s*\|\s*error=(?P<error>[\d.]+)\s*\|\s*"
    r"class=(?P<predicted_label>[^|]+?)\s*\|\s*confidence=(?P<confidence>[\d.]+)\s*$"
)

FLOW_RE = re.compile(
    r"(?P<src_ip>[\d.]+):(?P<src_port>\d+)\s*->\s*"
    r"(?P<dst_ip>[\d.]+):(?P<dst_port>\d+)\s*proto=(?P<protocol>\d+)"
)

NORMAL_LABELS = {"normal", "benign", "Normal", "Benign", "NORMAL", "BENIGN"}


def _parse_flow(flow_text: str) -> dict:
    match = FLOW_RE.search(flow_text.strip())
    if not match:
        return {
            "src_ip": None,
            "src_port": None,
            "dst_ip": None,
            "dst_port": None,
            "protocol": None,
        }
    return {
        "src_ip": match.group("src_ip"),
        "src_port": int(match.group("src_port")),
        "dst_ip": match.group("dst_ip"),
        "dst_port": int(match.group("dst_port")),
        "protocol": int(match.group("protocol")),
    }


def _protocol_name(proto) -> str:
    if proto is None or (isinstance(proto, float) and pd.isna(proto)):
        return "Unknown"
    try:
        proto = int(proto)
    except (TypeError, ValueError):
        return "Unknown"
    if proto == 6:
        return "TCP"
    if proto == 17:
        return "UDP"
    if proto == 1:
        return "ICMP"
    return "Other"


def _normalize_dataset(name: str) -> str:
    key = name.strip().lower().replace("-", "_")
    if "cicids" in key or key == "cic":
        return "cicids2018"
    if "nsl" in key or key == "kdd":
        return "nsl_kdd"
    return key


def load_alerts_from_jsonl(path: str | Path) -> pd.DataFrame:
    """Load alerts from JSONL file written by LiveHybridDetector."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()

    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return _alerts_to_dataframe(rows)


def load_alerts_from_log(path: str | Path) -> pd.DataFrame:
    """Parse text alert log lines into a DataFrame."""
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()

    rows = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or "ANOMALY" not in line:
                continue
            match = ALERT_LINE_RE.match(line)
            if not match:
                continue
            row = match.groupdict()
            row["reconstruction_error"] = float(row.pop("error"))
            row["confidence"] = float(row["confidence"])
            rows.append(row)

    return _alerts_to_dataframe(rows)


def _alerts_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if "flow" in df.columns:
        flow_parts = df["flow"].apply(_parse_flow).apply(pd.Series)
        # JSONL rows may already include protocol/fwd_pkts — avoid duplicate columns
        new_cols = [c for c in flow_parts.columns if c not in df.columns]
        if new_cols:
            df = pd.concat([df, flow_parts[new_cols]], axis=1)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "dataset" in df.columns:
        df["dataset_key"] = df["dataset"].apply(_normalize_dataset)

    if "protocol" in df.columns:
        proto_col = df["protocol"]
        if isinstance(proto_col, pd.DataFrame):
            proto_col = proto_col.iloc[:, 0]
        df["protocol_name"] = proto_col.apply(_protocol_name)

    if "predicted_label" in df.columns:
        df["predicted_label"] = df["predicted_label"].astype(str).str.strip()
        df["likely_false_positive"] = df["predicted_label"].isin(NORMAL_LABELS)

    if "reconstruction_error" in df.columns and "threshold" in df.columns:
        df["error_above_threshold"] = df["reconstruction_error"] - df["threshold"]
    elif "reconstruction_error" in df.columns:
        df["error_above_threshold"] = None

    df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    return df


def load_all_alerts(project_root: str | Path) -> pd.DataFrame:
    """Load alerts from JSONL (preferred) or text logs for all datasets."""
    project_root = Path(project_root)
    frames = []

    for dataset in ("nsl_kdd", "cicids2018"):
        jsonl = project_root / f"live_alerts_{dataset}.jsonl"
        log = project_root / f"live_alerts_{dataset}.log"

        if jsonl.exists():
            df = load_alerts_from_jsonl(jsonl)
        elif log.exists():
            df = load_alerts_from_log(log)
        else:
            continue

        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True).sort_values(
        "timestamp", ascending=False
    ).reset_index(drop=True)
