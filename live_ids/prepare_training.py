"""Preprocess captured live flows into training-ready datasets."""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from live_ids.capture_dataset import load_raw_captured_csv
from live_ids.config import CAPTURED_RAW_CSV, DATA_FOLDER, FEATURE_SET, PROCESSED_LIVE_FOLDER
from live_ids.preprocess_live import get_raw_feature_columns, load_preprocessor


def _clean_raw_dataframe(df):
    """Apply the same basic cleaning steps as preprocessing.py."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    if "Label" not in df.columns:
        raise ValueError("Captured CSV must contain a 'Label' column.")

    df["Label"] = df["Label"].astype(str).str.strip()
    df = df[~df["Label"].isin(["", "nan", "NaN", "None", "null"])]

    feature_columns = get_raw_feature_columns()
    feature_cols = [col for col in feature_columns if col in df.columns]
    missing = set(feature_columns) - set(feature_cols)
    if missing:
        for col in missing:
            if col in ("protocol_type", "service", "flag"):
                df[col] = "private" if col == "service" else "tcp"
            else:
                df[col] = 0.0
        feature_cols = feature_columns

    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan)
    before = len(df)
    df = df.dropna(subset=feature_cols)
    dropped_nan = before - len(df)

    before = len(df)
    df = df.drop_duplicates(subset=feature_cols + ["Label"])
    dropped_dupes = before - len(df)

    return df, dropped_nan, dropped_dupes


def preprocess_captured_for_training(
    raw_csv_path=None,
    output_folder=None,
    train_size=0.70,
    validation_size=0.15,
    random_state=42,
    update_autoencoder_normal=False,
):
    """
    Transform captured raw flows using the saved preprocessor and
    write training-ready CSV files.

    Outputs to processed_live/ by default:
      - X_train.csv, y_train.csv
      - X_validation.csv, y_validation.csv
      - X_test.csv, y_test.csv
      - X_normal_autoencoder.csv  (Benign flows only, processed)
      - preprocessing_summary.csv
    """
    raw_csv_path = raw_csv_path or CAPTURED_RAW_CSV
    output_folder = output_folder or PROCESSED_LIVE_FOLDER
    os.makedirs(output_folder, exist_ok=True)

    print("=" * 70)
    print("PREPROCESS CAPTURED LIVE FLOWS FOR TRAINING")
    print("=" * 70)
    print(f"\nInput:  {raw_csv_path}")
    print(f"Output: {output_folder}")

    df, dropped_nan, dropped_dupes = _clean_raw_dataframe(load_raw_captured_csv(raw_csv_path))
    print(f"\nRows after cleaning: {len(df)}")
    print(f"  Removed (NaN):      {dropped_nan}")
    print(f"  Removed (duplicates): {dropped_dupes}")
    print("\nClass distribution:")
    print(df["Label"].value_counts())

    if len(df) < 3:
        raise ValueError(
            "Not enough captured flows to preprocess (need at least 3). "
            "Capture more traffic with live_capture.py."
        )

    feature_columns = get_raw_feature_columns()
    print(f"\nDataset feature set: {FEATURE_SET}")
    print(f"Raw feature columns: {len(feature_columns)}")

    X = df[feature_columns]
    y = df["Label"]

    preprocessor = load_preprocessor()
    X_processed = preprocessor.transform(X).astype(np.float32)

    feature_names = preprocessor.get_feature_names_out()
    X_processed_df = pd.DataFrame(X_processed, columns=feature_names)

    label_encoder_path = os.path.join(DATA_FOLDER, "label_encoder.pkl")
    if os.path.exists(label_encoder_path):
        label_encoder = joblib.load(label_encoder_path)
        known = set(label_encoder.classes_)
        unknown = sorted(set(y.unique()) - known)
        if unknown:
            print(
                "\nWarning: labels not in existing encoder will be skipped:",
                unknown,
            )
            mask = y.isin(known)
            X_processed_df = X_processed_df[mask].reset_index(drop=True)
            y = y[mask].reset_index(drop=True)
        y_encoded = label_encoder.transform(y)
    else:
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        joblib.dump(label_encoder, os.path.join(output_folder, "label_encoder.pkl"))

    test_ratio = 1.0 - train_size - validation_size
    if test_ratio <= 0:
        raise ValueError("train_size + validation_size must be less than 1.0")

    X_train, X_temp, y_train, y_temp = train_test_split(
        X_processed_df,
        y_encoded,
        test_size=(1.0 - train_size),
        random_state=random_state,
        stratify=y_encoded if len(np.unique(y_encoded)) > 1 else None,
    )
    relative_val = validation_size / (validation_size + test_ratio)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=(1.0 - relative_val),
        random_state=random_state,
        stratify=y_temp if len(np.unique(y_temp)) > 1 else None,
    )

    X_train.to_csv(os.path.join(output_folder, "X_train.csv"), index=False)
    pd.DataFrame({"Label": y_train}).to_csv(
        os.path.join(output_folder, "y_train.csv"), index=False
    )
    X_val.to_csv(os.path.join(output_folder, "X_validation.csv"), index=False)
    pd.DataFrame({"Label": y_val}).to_csv(
        os.path.join(output_folder, "y_validation.csv"), index=False
    )
    X_test.to_csv(os.path.join(output_folder, "X_test.csv"), index=False)
    pd.DataFrame({"Label": y_test}).to_csv(
        os.path.join(output_folder, "y_test.csv"), index=False
    )

    normal_labels = [
        label
        for label in label_encoder.classes_
        if str(label).upper() in ("BENIGN", "NORMAL")
    ]
    if normal_labels:
        normal_code = list(label_encoder.classes_).index(normal_labels[0])
        normal_mask = y_encoded == normal_code
        X_normal = X_processed_df[normal_mask].reset_index(drop=True)
        X_normal.to_csv(
            os.path.join(output_folder, "X_normal_autoencoder.csv"),
            index=False,
        )
        print(f"\nNormal flows for autoencoder: {len(X_normal)}")

        if update_autoencoder_normal:
            main_normal_path = os.path.join(
                DATA_FOLDER, "X_train_normal_autoencoder.csv"
            )
            if os.path.exists(main_normal_path):
                existing = pd.read_csv(main_normal_path)
                combined = pd.concat([existing, X_normal], ignore_index=True)
                combined = combined.drop_duplicates()
            else:
                combined = X_normal
            combined.to_csv(main_normal_path, index=False)
            print(f"Updated autoencoder training file: {main_normal_path}")
            print(f"  Total normal samples: {len(combined)}")

    summary = pd.DataFrame(
        {
            "Metric": [
                "Source file",
                "Rows after cleaning",
                "Training samples",
                "Validation samples",
                "Testing samples",
                "Processed features",
                "Number of classes",
            ],
            "Value": [
                raw_csv_path,
                len(df),
                len(X_train),
                len(X_val),
                len(X_test),
                X_processed_df.shape[1],
                len(label_encoder.classes_),
            ],
        }
    )
    summary.to_csv(
        os.path.join(output_folder, "preprocessing_summary.csv"),
        index=False,
    )

    print("\n" + "=" * 70)
    print("CAPTURED DATA PREPROCESSING COMPLETE")
    print("=" * 70)
    print(f"\nProcessed files saved in:\n{os.path.abspath(output_folder)}")
    print("\nNext steps:")
    print("  1. Retrain autoencoder on captured normal traffic:")
    print("     python retrain_autoencoder.py --data <processed_live>/X_normal_autoencoder.csv")

    return output_folder
