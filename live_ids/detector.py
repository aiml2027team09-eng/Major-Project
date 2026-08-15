"""Load trained models and run live hybrid IDS inference."""

import json
import os
from datetime import datetime

import joblib
import numpy as np
import tensorflow as tf
from xgboost import XGBClassifier

from hybrid_ids.anomaly_detection import calculate_reconstruction_error, detect_anomalies
from live_ids.config import ALERT_LOG, DATA_FOLDER, MODEL_FOLDER
from live_ids.preprocess_live import load_label_encoder, load_preprocessor, preprocess_live_flows


class LiveHybridDetector:
    """Run autoencoder anomaly detection + XGBoost classification on live flows."""

    def __init__(self):
        self._validate_artifacts()
        self.preprocessor = load_preprocessor()
        self.label_encoder = load_label_encoder()
        self.autoencoder = tf.keras.models.load_model(
            os.path.join(MODEL_FOLDER, "autoencoder.keras")
        )
        self.xgb_model = XGBClassifier()
        self.xgb_model.load_model(os.path.join(MODEL_FOLDER, "xgboost_model.json"))

        with open(os.path.join(MODEL_FOLDER, "threshold.json")) as f:
            self.threshold = json.load(f)["threshold"]

        print("Loaded models:")
        print(f"  Autoencoder: {MODEL_FOLDER}/autoencoder.keras")
        print(f"  XGBoost:     {MODEL_FOLDER}/xgboost_model.json")
        print(f"  Threshold:   {self.threshold:.6f}")
        print(f"  Classes:     {list(self.label_encoder.classes_)}\n")

    def _validate_artifacts(self):
        required = [
            os.path.join(MODEL_FOLDER, "autoencoder.keras"),
            os.path.join(MODEL_FOLDER, "xgboost_model.json"),
            os.path.join(MODEL_FOLDER, "threshold.json"),
            os.path.join(DATA_FOLDER, "preprocessor.pkl"),
            os.path.join(DATA_FOLDER, "label_encoder.pkl"),
        ]
        missing = [path for path in required if not os.path.exists(path)]
        if missing:
            raise FileNotFoundError(
                "Missing trained artifacts:\n"
                + "\n".join(f"  - {p}" for p in missing)
                + "\n\nRun: python preprocessing.py && python hybrid_ids_model.py"
            )

    def analyze_flows(self, flow_feature_pairs):
        """
        Analyze completed flows.
        flow_feature_pairs: list of (FlowRecord, feature_dict)
        Returns list of alert dicts.
        """
        if not flow_feature_pairs:
            return []

        flows = [pair[0] for pair in flow_feature_pairs]
        feature_rows = [pair[1] for pair in flow_feature_pairs]
        X = preprocess_live_flows(self.preprocessor, feature_rows)

        if len(X) == 0:
            return []

        errors = calculate_reconstruction_error(self.autoencoder, X)
        anomaly_flags = detect_anomalies(errors, self.threshold)
        alerts = []

        for idx, (flow, error, is_anomaly) in enumerate(
            zip(flows, errors, anomaly_flags)
        ):
            if not is_anomaly:
                continue

            xgb_pred = self.xgb_model.predict(X[idx : idx + 1])[0]
            attack_label = self.label_encoder.inverse_transform([int(xgb_pred)])[0]

            alert = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "flow": flow.summary(),
                "reconstruction_error": float(error),
                "threshold": float(self.threshold),
                "predicted_label": attack_label,
                "protocol": flow.protocol,
                "fwd_pkts": flow.tot_fwd_pkts,
                "bwd_pkts": flow.tot_bwd_pkts,
            }
            alerts.append(alert)
            self._log_alert(alert)

        return alerts

    def _log_alert(self, alert):
        line = (
            f"[{alert['timestamp']}] ANOMALY | {alert['flow']} | "
            f"error={alert['reconstruction_error']:.4f} | "
            f"class={alert['predicted_label']}"
        )
        print(line)
        with open(ALERT_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
