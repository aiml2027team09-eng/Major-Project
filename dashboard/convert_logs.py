#!/usr/bin/env python
"""Convert existing text alert logs to JSONL for the dashboard."""

import json
from pathlib import Path

from dashboard.alert_parser import load_alerts_from_log


def convert_log_to_jsonl(log_path: Path) -> int:
    df = load_alerts_from_log(log_path)
    if df.empty:
        return 0

    jsonl_path = log_path.with_suffix(".jsonl")
    with jsonl_path.open("w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            record = {
                "timestamp": row["timestamp"].isoformat()
                if hasattr(row["timestamp"], "isoformat")
                else str(row["timestamp"]),
                "dataset": row.get("dataset", ""),
                "flow": row.get("flow", ""),
                "reconstruction_error": float(row.get("reconstruction_error", 0)),
                "predicted_label": row.get("predicted_label", ""),
                "confidence": float(row.get("confidence", 0)),
                "protocol": row.get("protocol"),
                "fwd_pkts": row.get("fwd_pkts"),
                "bwd_pkts": row.get("bwd_pkts"),
            }
            f.write(json.dumps(record) + "\n")
    return len(df)


def main():
    root = Path(__file__).resolve().parent
    total = 0
    for log in root.glob("live_alerts_*.log"):
        count = convert_log_to_jsonl(log)
        print(f"{log.name} -> {log.with_suffix('.jsonl').name} ({count} alerts)")
        total += count
    print(f"Converted {total} alerts total.")


if __name__ == "__main__":
    main()
