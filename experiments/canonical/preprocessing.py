"""
experiments/canonical/preprocessing.py
======================================
Strict Preprocessing Pipeline Fitted Exclusively on the Training Split.

Order of Execution:
1. Load train.parquet, val.parquet, test.parquet
2. Separate features and target
3. Fit ColumnTransformer (StandardScaler, OneHotEncoder) ONLY on train features
4. Fit LabelEncoder ONLY on train labels
5. Transform Validation using train-fitted preprocessors
6. Transform Test using train-fitted preprocessors
7. Apply SMOTE ONLY to training partition
8. Extract normal-only subset for Autoencoder training
9. Persist models/preprocessors/ and metadata/feature ordering
"""

from __future__ import annotations

import json
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_canonical_preprocessing(dataset_name: str = "nsl_kdd", seed: int = 42) -> dict:
    print("=" * 70)
    print(f"CANONICAL PREPROCESSING (TRAIN-ONLY FIT) — {dataset_name.upper()}")
    print("=" * 70)
    
    splits_dir = os.path.join(PROJECT_ROOT, "data", "splits", dataset_name)
    train_df = pd.read_parquet(os.path.join(splits_dir, "train.parquet"))
    val_df = pd.read_parquet(os.path.join(splits_dir, "val.parquet"))
    test_df = pd.read_parquet(os.path.join(splits_dir, "test.parquet"))
    
    label_col = "category" if "category" in train_df.columns else ("Label" if "Label" in train_df.columns else "label")
    ignore_cols = [label_col, "row_hash", "origin_split", "Timestamp", "timestamp"]
    feature_cols = [c for c in train_df.columns if c not in ignore_cols]
    
    X_train_raw = train_df[feature_cols].copy()
    y_train_raw = train_df[label_col].copy()
    
    X_val_raw = val_df[feature_cols].copy()
    y_val_raw = val_df[label_col].copy()
    
    X_test_raw = test_df[feature_cols].copy()
    y_test_raw = test_df[label_col].copy()
    
    num_cols = X_train_raw.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X_train_raw.select_dtypes(exclude=[np.number]).columns.tolist()
    
    print(f"Features: {len(feature_cols)} (Numeric: {len(num_cols)}, Categorical: {len(cat_cols)})")
    
    # Define ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("numerical", StandardScaler(), num_cols),
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ],
        remainder="drop",
    )
    
    # CRITICAL: Fit ONLY on Training Data
    print("Fitting preprocessor strictly on X_train...")
    preprocessor.fit(X_train_raw)
    
    print("Transforming Train, Validation, and Test partitions...")
    X_train_proc = np.asarray(preprocessor.transform(X_train_raw), dtype=np.float32)
    X_val_proc = np.asarray(preprocessor.transform(X_val_raw), dtype=np.float32)
    X_test_proc = np.asarray(preprocessor.transform(X_test_raw), dtype=np.float32)
    
    feature_names = preprocessor.get_feature_names_out().tolist()
    
    # Fit LabelEncoder ONLY on Training Labels
    label_encoder = LabelEncoder()
    y_train_enc = label_encoder.fit_transform(y_train_raw)
    y_val_enc = label_encoder.transform(y_val_raw)
    y_test_enc = label_encoder.transform(y_test_raw)
    
    # Save Preprocessor and Feature Metadata
    models_prep_dir = os.path.join(PROJECT_ROOT, "models", "preprocessors")
    metadata_dir = os.path.join(PROJECT_ROOT, "metadata")
    os.makedirs(models_prep_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)
    
    joblib.dump(preprocessor, os.path.join(models_prep_dir, f"{dataset_name}_preprocessor.pkl"))
    joblib.dump(label_encoder, os.path.join(models_prep_dir, f"{dataset_name}_label_encoder.pkl"))
    with open(os.path.join(metadata_dir, f"{dataset_name}_features.json"), "w") as f:
        json.dump({"features": feature_names, "raw_features": feature_cols}, f, indent=4)
        
    # Extract Normal subset for Autoencoder training (from X_train only!)
    benign_label_str = "normal" if dataset_name == "nsl_kdd" else "Benign"
    normal_idx = list(label_encoder.classes_).index(benign_label_str)
    X_train_normal = X_train_proc[y_train_enc == normal_idx]
    
    # Apply SMOTE strictly to Training data for XGBoost classifier
    print(f"Applying SMOTE to training set only (Initial train shape: {X_train_proc.shape})...")
    class_counts = pd.Series(y_train_enc).value_counts()
    majority_class = class_counts.idxmax()
    majority_count = int(class_counts.max())
    
    cap = 50000 if dataset_name == "nsl_kdd" else 80000
    if majority_count > cap:
        undersampler = RandomUnderSampler(sampling_strategy={majority_class: cap}, random_state=seed)
        X_bal, y_bal = undersampler.fit_resample(X_train_proc, y_train_enc)
    else:
        X_bal, y_bal = X_train_proc, y_train_enc
        
    k_neighbors = max(1, min(5, int(pd.Series(y_bal).value_counts().min()) - 1))
    smote = SMOTE(random_state=seed, k_neighbors=k_neighbors)
    X_train_smote, y_train_smote = smote.fit_resample(X_bal, y_bal)
    print(f"Post-SMOTE train shape: {X_train_smote.shape}")
    
    # Save canonical processed arrays
    processed_out = os.path.join(PROJECT_ROOT, "data", "cleaned", dataset_name)
    os.makedirs(processed_out, exist_ok=True)
    
    np.save(os.path.join(processed_out, "X_train_smote.npy"), X_train_smote)
    np.save(os.path.join(processed_out, "y_train_smote.npy"), y_train_smote)
    np.save(os.path.join(processed_out, "X_train_normal.npy"), X_train_normal)
    np.save(os.path.join(processed_out, "X_val.npy"), X_val_proc)
    np.save(os.path.join(processed_out, "y_val.npy"), y_val_enc)
    np.save(os.path.join(processed_out, "X_test.npy"), X_test_proc)
    np.save(os.path.join(processed_out, "y_test.npy"), y_test_enc)
    
    print(f"[SUCCESS] Saved canonical processed datasets and artifacts to {processed_out}")
    return {
        "processed_out": processed_out,
        "n_features": len(feature_names),
        "classes": list(label_encoder.classes_),
    }

if __name__ == "__main__":
    run_canonical_preprocessing("nsl_kdd", seed=42)
    run_canonical_preprocessing("cicids2018", seed=42)
