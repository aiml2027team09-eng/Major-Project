"""Load trained models and run live hybrid IDS inference."""

import json
import os
from datetime import datetime

import numpy as np
import tensorflow as tf
from xgboost import XGBClassifier

from dataset_config import get_profile, resolve_model_folder
from hybrid_ids.anomaly_detection import calculate_reconstruction_error, detect_anomalies
import live_ids.config as config
from live_ids.preprocess_live import (
    load_label_encoder,
    load_preprocessor,
    preprocess_live_flows,
)


class LiveHybridDetector:
    """Run autoencoder anomaly detection + XGBoost classification on live flows."""

    def __init__(
        self,
        profile=None,
        data_folder=None,
        model_folder=None,
        alert_log=None,
        feature_set=None,
        min_confidence=None,
    ):
        if profile is not None:
            self.dataset_name = profile.display_name
            self.dataset_key = profile.name
            self.data_folder = profile.data_folder
            self.model_folder = resolve_model_folder(profile)
            self.alert_log = profile.alert_log
            self.feature_set = profile.feature_set
        else:
            self.dataset_name = config.ACTIVE_DATASET
            self.dataset_key = config.ACTIVE_DATASET
            self.data_folder = data_folder or config.DATA_FOLDER
            self.model_folder = model_folder or config.MODEL_FOLDER
            self.alert_log = alert_log or config.ALERT_LOG
            self.feature_set = feature_set or config.FEATURE_SET

        self.min_confidence = (
            min_confidence
            if min_confidence is not None
            else config.XGBOOST_MIN_CONFIDENCE
        )

        self._validate_artifacts()
        self.preprocessor = load_preprocessor(self.data_folder)
        self.label_encoder = load_label_encoder(self.data_folder)
        self.autoencoder = tf.keras.models.load_model(
            os.path.join(self.model_folder, "autoencoder.keras")
        )
        self.xgb_model = XGBClassifier()
        self.xgb_model.load_model(
            os.path.join(self.model_folder, "xgboost_model.json")
        )

        with open(os.path.join(self.model_folder, "threshold.json")) as f:
            self.threshold = json.load(f)["threshold"]

        print(f"Loaded {self.dataset_name} models:")
        print(f"  Autoencoder: {self.model_folder}/autoencoder.keras")
        print(f"  XGBoost:     {self.model_folder}/xgboost_model.json")
        print(f"  Threshold:   {self.threshold:.6f}")
        print(f"  Classes:     {list(self.label_encoder.classes_)}")
        print(f"  Alerts log:  {self.alert_log}\n")

    def _validate_artifacts(self):
        required = [
            os.path.join(self.model_folder, "autoencoder.keras"),
            os.path.join(self.model_folder, "xgboost_model.json"),
            os.path.join(self.model_folder, "threshold.json"),
            os.path.join(self.data_folder, "preprocessor.pkl"),
            os.path.join(self.data_folder, "label_encoder.pkl"),
        ]
        missing = [path for path in required if not os.path.exists(path)]
        if missing:
            profile = get_profile(self.dataset_key)
            raise FileNotFoundError(
                f"Missing trained artifacts for {self.dataset_name}:\n"
                + "\n".join(f"  - {p}" for p in missing)
                + f"\n\nRun: python {profile.preprocess_script}\n"
                f"     python hybrid_ids_model.py --dataset {profile.name}"
            )

    def analyze_flows(self, flow_feature_pairs):
        """Analyze completed flows. Returns list of alert dicts."""
        if not flow_feature_pairs:
            return []

        flows = [pair[0] for pair in flow_feature_pairs]
        feature_rows = [pair[1] for pair in flow_feature_pairs]
        X = preprocess_live_flows(
            self.preprocessor,
            feature_rows,
            feature_set=self.feature_set,
            data_folder=self.data_folder,
        )

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

            proba = self.xgb_model.predict_proba(X[idx : idx + 1])[0]
            xgb_pred = int(np.argmax(proba))
            confidence = float(np.max(proba))
            if confidence < self.min_confidence:
                continue

            attack_label = self.label_encoder.inverse_transform([xgb_pred])[0]

            alert = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "dataset": self.dataset_name,
                "flow": flow.summary(),
                "reconstruction_error": float(error),
                "threshold": float(self.threshold),
                "predicted_label": attack_label,
                "confidence": confidence,
                "protocol": flow.protocol,
                "fwd_pkts": flow.tot_fwd_pkts,
                "bwd_pkts": flow.tot_bwd_pkts,
            }
            alerts.append(alert)
            self._log_alert(alert)

        return alerts

    def _log_alert(self, alert):
        line = (
            f"[{alert['timestamp']}] [{alert['dataset']}] ANOMALY | {alert['flow']} | "
            f"error={alert['reconstruction_error']:.4f} | "
            f"class={alert['predicted_label']} | "
            f"confidence={alert['confidence']:.2f}"
        )
        print(line)
        log_dir = os.path.dirname(self.alert_log) or "."
        os.makedirs(log_dir, exist_ok=True)
        with open(self.alert_log, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        jsonl_path = os.path.splitext(self.alert_log)[0] + ".jsonl"
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert) + "\n")


def load_detectors_for_datasets(dataset_names):
    """Load one LiveHybridDetector per dataset name."""
    return [LiveHybridDetector(profile=get_profile(name)) for name in dataset_names]
