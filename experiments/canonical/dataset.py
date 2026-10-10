"""
experiments/canonical/dataset.py
=================================
Leakage-Free Dataset Loader, Schema Validator, Global De-duplicator,
and Deterministic Splitter.

Order of Execution:
1. Load raw data & validate schema
2. Remove exact duplicates globally
3. Generate immutable sample identifiers and row hashes
4. Partition into Train (70%), Validation (15%), Test (15%)
5. Assert Train ∩ Validation = 0, Train ∩ Test = 0, Validation ∩ Test = 0
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import gc
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def compute_row_hashes(df: pd.DataFrame, feature_cols: list[str]) -> pd.Series:
    """Compute deterministic SHA-256 string hash for every row."""
    # Convert numerical features to stable string representation
    subset = df[feature_cols].copy()
    for col in subset.select_dtypes(include=[np.number]).columns:
        subset[col] = subset[col].round(6).astype(str)
    row_strings = subset.astype(str).agg("||".join, axis=1)
    return row_strings.apply(lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())

def prepare_canonical_nsl_kdd(seed: int = 42) -> dict[str, str]:
    """Load and process NSL-KDD with strict global deduplication and zero leakage."""
    print("=" * 70)
    print("CANONICAL DATASET PREPARATION: NSL-KDD")
    print("=" * 70)
    
    nsl_folder = os.path.join(PROJECT_ROOT, "NSL-KDD", "nsl-kdd")
    train_file = os.path.join(nsl_folder, "KDDTrain+.txt")
    test_file = os.path.join(nsl_folder, "KDDTest+.txt")
    
    columns = [
        "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
        "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
        "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
        "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
        "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
        "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
        "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
        "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
        "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
        "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty",
    ]
    
    df_train_raw = pd.read_csv(train_file, names=columns)
    df_test_raw = pd.read_csv(test_file, names=columns)
    
    df_train_raw["origin_split"] = "train"
    df_test_raw["origin_split"] = "test"
    df_raw = pd.concat([df_train_raw, df_test_raw], ignore_index=True)
    df_raw.drop(columns=["difficulty"], inplace=True)
    
    feature_cols = [c for c in columns if c not in ("label", "difficulty")]
    
    # 1. Map to high-level attack categories
    from preprocessing_nsl_kdd import ATTACK_TO_CATEGORY
    df_raw["label"] = df_raw["label"].astype(str).str.lower().str.strip()
    df_raw["category"] = df_raw["label"].map(lambda l: ATTACK_TO_CATEGORY.get(l, "unknown"))
    
    # Filter out unknowns if any
    df_raw = df_raw[df_raw["category"] != "unknown"].copy()
    
    # 2. Compute stable row hashes
    print("Computing row hashes for deduplication...")
    df_raw["row_hash"] = compute_row_hashes(df_raw, feature_cols)
    
    # 3. Global deduplication (purge cross-split duplicate leakage)
    initial_len = len(df_raw)
    df_clean = df_raw.drop_duplicates(subset=["row_hash"]).copy().reset_index(drop=True)
    dropped = initial_len - len(df_clean)
    print(f"Total raw rows: {initial_len:,} | Exact duplicates purged: {dropped:,} | Unique rows: {len(df_clean):,}")
    
    # 4. Partition into Train (70%), Validation (15%), Test (15%) stratified by category
    train_df, test_val_df = train_test_split(
        df_clean, test_size=0.30, random_state=seed, stratify=df_clean["category"]
    )
    val_df, test_df = train_test_split(
        test_val_df, test_size=0.50, random_state=seed, stratify=test_val_df["category"]
    )
    
    # Verify absolute zero overlap
    train_hashes = set(train_df["row_hash"])
    val_hashes = set(val_df["row_hash"])
    test_hashes = set(test_df["row_hash"])
    
    assert len(train_hashes.intersection(val_hashes)) == 0, "Leakage: Train overlaps with Validation!"
    assert len(train_hashes.intersection(test_hashes)) == 0, "Leakage: Train overlaps with Test!"
    assert len(val_hashes.intersection(test_hashes)) == 0, "Leakage: Validation overlaps with Test!"
    print("[PASS] Strict Zero-Leakage Assertion: PASSED (Train cap Val = 0, Train cap Test = 0, Val cap Test = 0)")
    
    out_dir = os.path.join(PROJECT_ROOT, "data", "splits", "nsl_kdd")
    os.makedirs(out_dir, exist_ok=True)
    
    train_df.to_parquet(os.path.join(out_dir, "train.parquet"), index=False)
    val_df.to_parquet(os.path.join(out_dir, "val.parquet"), index=False)
    test_df.to_parquet(os.path.join(out_dir, "test.parquet"), index=False)
    
    manifest = {
        "dataset_name": "NSL-KDD",
        "seed": seed,
        "total_samples": len(df_clean),
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "feature_count": len(feature_cols),
        "duplicates_removed": dropped,
        "class_distribution_train": train_df["category"].value_counts().to_dict(),
        "class_distribution_test": test_df["category"].value_counts().to_dict(),
    }
    with open(os.path.join(PROJECT_ROOT, "data", "manifests", "nsl_kdd_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Saved canonical NSL-KDD splits to {out_dir}")
    return {"out_dir": out_dir, "manifest": manifest}

def prepare_canonical_cicids2018(seed: int = 42) -> dict[str, str]:
    """Load and process CSE-CIC-IDS2018 with strict global deduplication and zero leakage."""
    print("=" * 70)
    print("CANONICAL DATASET PREPARATION: CSE-CIC-IDS2018")
    print("=" * 70)
    
    raw_csv = os.path.join(PROJECT_ROOT, "cic.csv")
    if not os.path.exists(raw_csv):
        raise FileNotFoundError(f"Missing primary raw dataset at {raw_csv}")
        
    print("Loading raw CICIDS2018 CSV in memory-efficient mode...")
    df = pd.read_csv(raw_csv, low_memory=False)
    df.columns = df.columns.astype(str).str.strip()
    
    # Standardize label
    label_col = "Label" if "Label" in df.columns else "label"
    df[label_col] = df[label_col].astype(str).str.strip()
    df = df[~df[label_col].isin(["", "nan", "NaN", "None", "null"])].copy()
    
    # Handle numeric infinities & NaNs
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        df[num_cols] = df[num_cols].replace([np.inf, -np.inf], np.nan)
    df.dropna(inplace=True)
    
    feature_cols = [c for c in df.columns if c != label_col and c not in ("Timestamp", "timestamp")]
    
    print("Computing row hashes for global deduplication...")
    df["row_hash"] = compute_row_hashes(df, feature_cols)
    
    init_len = len(df)
    df_clean = df.drop_duplicates(subset=["row_hash"]).copy().reset_index(drop=True)
    dropped = init_len - len(df_clean)
    print(f"Total rows read: {init_len:,} | Exact duplicates purged: {dropped:,} | Clean unique rows: {len(df_clean):,}")
    
    # Partition into Train (70%), Validation (15%), Test (15%) stratified by label
    train_df, test_val_df = train_test_split(
        df_clean, test_size=0.30, random_state=seed, stratify=df_clean[label_col]
    )
    val_df, test_df = train_test_split(
        test_val_df, test_size=0.50, random_state=seed, stratify=test_val_df[label_col]
    )
    
    train_hashes = set(train_df["row_hash"])
    val_hashes = set(val_df["row_hash"])
    test_hashes = set(test_df["row_hash"])
    
    assert len(train_hashes.intersection(val_hashes)) == 0, "Leakage: Train overlaps with Validation!"
    assert len(train_hashes.intersection(test_hashes)) == 0, "Leakage: Train overlaps with Test!"
    assert len(val_hashes.intersection(test_hashes)) == 0, "Leakage: Validation overlaps with Test!"
    print("[PASS] Strict Zero-Leakage Assertion: PASSED (Train cap Val = 0, Train cap Test = 0, Val cap Test = 0)")
    
    out_dir = os.path.join(PROJECT_ROOT, "data", "splits", "cicids2018")
    os.makedirs(out_dir, exist_ok=True)
    
    train_df.to_parquet(os.path.join(out_dir, "train.parquet"), index=False)
    val_df.to_parquet(os.path.join(out_dir, "val.parquet"), index=False)
    test_df.to_parquet(os.path.join(out_dir, "test.parquet"), index=False)
    
    manifest = {
        "dataset_name": "CSE-CIC-IDS2018 (Brute-Force Subset)",
        "seed": seed,
        "total_samples": len(df_clean),
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "feature_count": len(feature_cols),
        "duplicates_removed": dropped,
        "class_distribution_train": train_df[label_col].value_counts().to_dict(),
        "class_distribution_test": test_df[label_col].value_counts().to_dict(),
    }
    with open(os.path.join(PROJECT_ROOT, "data", "manifests", "cicids2018_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Saved canonical CICIDS2018 splits to {out_dir}")
    return {"out_dir": out_dir, "manifest": manifest}

if __name__ == "__main__":
    prepare_canonical_nsl_kdd(seed=42)
    prepare_canonical_cicids2018(seed=42)
