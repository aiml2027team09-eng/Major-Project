import os

import numpy as np
import pandas as pd

import hybrid_ids.config as config


def load_datasets():
    """Load preprocessed train, validation, test, and normal-only datasets."""
    print("=" * 70)
    print("HYBRID AUTOENCODER + XGBOOST IDS")
    print("=" * 70)
    print(f"\nDataset: {config.ACTIVE_DATASET}")
    print(f"Data folder: {config.DATA_FOLDER}")
    print("\nLoading datasets...")

    X_train = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "X_train_smote.csv")
    )
    y_train = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "y_train_smote.csv")
    )["Label"]

    X_validation = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "X_validation.csv")
    )
    y_validation = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "y_validation.csv")
    )["Label"]

    X_test = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "X_test.csv")
    )
    y_test = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "y_test.csv")
    )["Label"]

    X_normal = pd.read_csv(
        os.path.join(config.DATA_FOLDER, "X_train_normal_autoencoder.csv")
    )

    print("\nDataset shapes:")
    print("Training:", X_train.shape)
    print("Validation:", X_validation.shape)
    print("Testing:", X_test.shape)
    print("Normal Autoencoder:", X_normal.shape)

    return X_train, y_train, X_validation, y_validation, X_test, y_test, X_normal


def convert_to_numpy(X_train, y_train, X_validation, y_validation, X_test, y_test, X_normal):
    """Convert pandas DataFrames/Series to numpy arrays."""
    X_train_np = X_train.astype(np.float32).values
    X_validation_np = X_validation.astype(np.float32).values
    X_test_np = X_test.astype(np.float32).values
    X_normal_np = X_normal.astype(np.float32).values

    y_train_np = y_train.values
    y_validation_np = y_validation.values
    y_test_np = y_test.values

    return (
        X_train_np,
        y_train_np,
        X_validation_np,
        y_validation_np,
        X_test_np,
        y_test_np,
        X_normal_np,
    )
