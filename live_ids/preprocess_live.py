"""Apply saved preprocessing pipeline to live flow features."""

import os

import joblib
import numpy as np
import pandas as pd

from live_ids.config import DATA_FOLDER
from live_ids.feature_builder import FEATURE_COLUMNS


def load_preprocessor():
    path = os.path.join(DATA_FOLDER, "preprocessor.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Preprocessor not found at {path}. Run preprocessing.py first."
        )
    return joblib.load(path)


def load_label_encoder():
    path = os.path.join(DATA_FOLDER, "label_encoder.pkl")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Label encoder not found at {path}. Run preprocessing.py first."
        )
    return joblib.load(path)


def features_to_dataframe(feature_rows):
    """Convert list of feature dicts to DataFrame with correct column order."""
    df = pd.DataFrame(feature_rows)
    for column in FEATURE_COLUMNS:
        if column not in df.columns:
            df[column] = 0.0
    return df[FEATURE_COLUMNS]


def preprocess_live_flows(preprocessor, feature_rows):
    """Transform live flow features using the fitted preprocessor."""
    if not feature_rows:
        return np.array([])

    df = features_to_dataframe(feature_rows)
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    processed = preprocessor.transform(df)
    return processed.astype(np.float32)
