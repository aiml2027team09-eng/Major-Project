"""Save captured live flows to CSV for later training preprocessing."""

import os
import threading
from datetime import datetime

import pandas as pd

import live_ids.config as config
from live_ids.preprocess_live import get_raw_feature_columns

METADATA_COLUMNS = [
    "capture_timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
]


class FlowDatasetWriter:
    """Append completed flow features to a raw CSV dataset (thread-safe)."""

    def __init__(self, output_path=None, default_label=None):
        self.output_path = output_path or config.CAPTURED_RAW_CSV
        self.default_label = default_label or config.DEFAULT_CAPTURE_LABEL
        self._lock = threading.Lock()
        self._buffer = []
        self.total_saved = 0
        os.makedirs(os.path.dirname(self.output_path) or config.CAPTURED_DATA_FOLDER, exist_ok=True)

    def add_flow(self, flow, feature_row, label=None):
        """Queue one completed flow for writing."""
        row = dict(feature_row)
        row["Label"] = label or self.default_label
        row["capture_timestamp"] = datetime.now().isoformat(timespec="seconds")
        row["src_ip"] = flow.src_ip
        row["dst_ip"] = flow.dst_ip
        row["src_port"] = flow.src_port
        row["dst_port"] = flow.dst_port

        with self._lock:
            self._buffer.append(row)

    def flush(self):
        """Write buffered flows to CSV."""
        with self._lock:
            if not self._buffer:
                return 0
            batch = self._buffer.copy()
            self._buffer.clear()

        df = pd.DataFrame(batch)
        write_header = not os.path.exists(self.output_path)
        df.to_csv(self.output_path, mode="a", header=write_header, index=False)
        self.total_saved += len(batch)
        return len(batch)


def load_raw_captured_csv(path=None):
    """Load raw captured flow CSV."""
    path = path or config.CAPTURED_RAW_CSV
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No captured data at {path}. Run live_capture.py first."
        )
    return pd.read_csv(path)


def get_feature_columns(include_metadata=False):
    """Return feature column list for the active dataset."""
    columns = list(get_raw_feature_columns())
    if include_metadata:
        columns = METADATA_COLUMNS + columns + ["Label"]
    return columns
