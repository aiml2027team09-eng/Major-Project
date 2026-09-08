"""Shared dataset profiles for NSL-KDD and CICIDS2018 pipelines."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

DatasetName = Literal["nsl_kdd", "cicids2018"]

DEFAULT_DATASET: DatasetName = "nsl_kdd"
VALID_DATASETS = ("nsl_kdd", "cicids2018")
CAPTURED_DATA_ROOT = "captured_data"
PROCESSED_LIVE_ROOT = "processed_live"


@dataclass(frozen=True)
class DatasetProfile:
    name: DatasetName
    display_name: str
    data_folder: str
    model_folder: str
    feature_set: str
    normal_label: str
    alert_log: str
    preprocess_script: str
    captured_subfolder: str


PROFILES: dict[DatasetName, DatasetProfile] = {
    "nsl_kdd": DatasetProfile(
        name="nsl_kdd",
        display_name="NSL-KDD",
        data_folder="processed_NSL_KDD",
        model_folder="trained_models/nsl_kdd",
        feature_set="nsl_kdd",
        normal_label="normal",
        alert_log="live_alerts_nsl_kdd.log",
        preprocess_script="preprocessing_nsl_kdd.py",
        captured_subfolder="nsl_kdd",
    ),
    "cicids2018": DatasetProfile(
        name="cicids2018",
        display_name="CICIDS2018",
        data_folder="processed_CICIDS2018",
        model_folder="trained_models/cicids2018",
        feature_set="cicids2018",
        normal_label="Benign",
        alert_log="live_alerts_cicids2018.log",
        preprocess_script="preprocessing.py",
        captured_subfolder="cicids2018",
    ),
}


def normalize_dataset_name(name: str | None) -> DatasetName:
    if name is None:
        return DEFAULT_DATASET
    key = name.strip().lower().replace("-", "_")
    aliases = {
        "nsl_kdd": "nsl_kdd",
        "nslkdd": "nsl_kdd",
        "nsl": "nsl_kdd",
        "cicids2018": "cicids2018",
        "cicids": "cicids2018",
        "cic": "cicids2018",
    }
    if key not in aliases:
        raise ValueError(
            f"Unknown dataset '{name}'. Choose from: {', '.join(VALID_DATASETS)}"
        )
    return aliases[key]  # type: ignore[return-value]


def get_profile(name: str | None = None) -> DatasetProfile:
    return PROFILES[normalize_dataset_name(name)]


def resolve_model_folder(profile: DatasetProfile) -> str:
    """Use dataset subfolder; fall back to legacy flat trained_models/ for NSL-KDD."""
    if os.path.exists(os.path.join(profile.model_folder, "autoencoder.keras")):
        return profile.model_folder

    legacy_folder = "trained_models"
    legacy_model = os.path.join(legacy_folder, "autoencoder.keras")
    if profile.name == "nsl_kdd" and os.path.exists(legacy_model):
        return legacy_folder

    return profile.model_folder


def captured_raw_csv(profile: DatasetProfile) -> str:
    return os.path.join(
        CAPTURED_DATA_ROOT, profile.captured_subfolder, "live_flows_raw.csv"
    )


def processed_live_folder(profile: DatasetProfile) -> str:
    return os.path.join(PROCESSED_LIVE_ROOT, profile.captured_subfolder)


def apply_training_profile(profile: DatasetProfile) -> None:
    import hybrid_ids.config as train_config

    train_config.ACTIVE_DATASET = profile.name
    train_config.DATA_FOLDER = profile.data_folder
    train_config.MODEL_FOLDER = resolve_model_folder(profile)
    os.makedirs(train_config.MODEL_FOLDER, exist_ok=True)


def apply_live_profile(profile: DatasetProfile) -> None:
    import live_ids.config as live_config

    live_config.ACTIVE_DATASET = profile.name
    live_config.DATA_FOLDER = profile.data_folder
    live_config.MODEL_FOLDER = resolve_model_folder(profile)
    live_config.FEATURE_SET = profile.feature_set
    live_config.DEFAULT_CAPTURE_LABEL = profile.normal_label
    live_config.ALERT_LOG = profile.alert_log
    live_config.CAPTURED_RAW_CSV = captured_raw_csv(profile)
    live_config.PROCESSED_LIVE_FOLDER = processed_live_folder(profile)
    os.makedirs(os.path.dirname(live_config.CAPTURED_RAW_CSV), exist_ok=True)
    os.makedirs(live_config.PROCESSED_LIVE_FOLDER, exist_ok=True)


def configure_project(dataset_name: str | None = None) -> DatasetProfile:
    """Apply the selected dataset profile to training and live config modules."""
    profile = get_profile(dataset_name)
    apply_training_profile(profile)
    apply_live_profile(profile)
    return profile


def init_training_config(dataset_name: str | None = None) -> DatasetProfile:
    profile = get_profile(dataset_name)
    apply_training_profile(profile)
    return profile


def init_live_config(dataset_name: str | None = None) -> DatasetProfile:
    profile = get_profile(dataset_name)
    apply_live_profile(profile)
    return profile
