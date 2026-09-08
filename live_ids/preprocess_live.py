"""Apply saved preprocessing pipeline to live flow features."""

import os

import joblib
import numpy as np
import pandas as pd

import live_ids.config as config


def load_preprocessor(data_folder=None):
    folder = data_folder or config.DATA_FOLDER
    path = os.path.join(folder, "preprocessor.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Preprocessor not found at {path}. Run the dataset preprocessing script first."
        )
    return joblib.load(path)


def load_label_encoder(data_folder=None):
    folder = data_folder or config.DATA_FOLDER
    path = os.path.join(folder, "label_encoder.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Label encoder not found at {path}. Run the dataset preprocessing script first."
        )
    return joblib.load(path)


def _feature_columns(feature_set=None, data_folder=None):
    feature_set = feature_set or config.FEATURE_SET
    if feature_set == "nsl_kdd":
        from live_ids.nsl_kdd_feature_builder import _load_raw_columns

        return _load_raw_columns(data_folder)

    from live_ids.feature_builder import FEATURE_COLUMNS

    return FEATURE_COLUMNS


def get_raw_feature_columns(feature_set=None, data_folder=None):
    """Return raw feature column names expected by the active preprocessor."""
    return _feature_columns(feature_set, data_folder)


def features_to_dataframe(feature_rows, feature_set=None, data_folder=None):
    """Convert list of feature dicts to DataFrame with correct column order."""
    columns = _feature_columns(feature_set, data_folder)
    df = pd.DataFrame(feature_rows)
    for column in columns:
        if column not in df.columns:
            if column in ("protocol_type", "service", "flag"):
                df[column] = "private" if column == "service" else "tcp"
            else:
                df[column] = 0.0
    return df[columns]


def preprocess_live_flows(
    preprocessor, feature_rows, feature_set=None, data_folder=None
):
    """Transform live flow features using the fitted preprocessor."""
    if not feature_rows:
        return np.array([])

    df = features_to_dataframe(feature_rows, feature_set, data_folder)
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    processed = preprocessor.transform(df)
    return processed.astype(np.float32)
