# ================================================================
# NSL-KDD DATA PREPROCESSING PIPELINE
# ================================================================
#
# Uses the official NSL-KDD split:
#   KDDTrain+.txt  -> train + validation
#   KDDTest+.txt   -> test (held-out, full set with category mapping)
#
# Steps:
#   1. Load train/test TXT files
#   2. Drop difficulty score column
#   3. Remove duplicate rows
#   4. Handle inf/NaN, drop constant columns
#   5. Map fine-grained labels to 5 attack categories (better accuracy)
#   6. One-hot encode protocol_type, service, flag
#   7. Scale numerical features (StandardScaler)
#   8. SMOTE on training data only
#   9. Create normal-only data for autoencoder
#  10. Save processed datasets + live-inference metadata
#
# ================================================================

import gc
import json
import os
import warnings

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore")

# ----------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------

NSL_KDD_FOLDER = os.path.join("NSL-KDD", "nsl-kdd")
TRAIN_FILE = os.path.join(NSL_KDD_FOLDER, "KDDTrain+.txt")
TEST_FILE = os.path.join(NSL_KDD_FOLDER, "KDDTest+.txt")
OUTPUT_FOLDER = "processed_NSL_KDD"

VALIDATION_SIZE = 0.15
RANDOM_STATE = 42
SMOTE_MAX_SAMPLES_PER_CLASS = 50000

NSL_KDD_COLUMNS = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty",
]

CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]

# Fine-grained attack -> category (includes test-only attacks for full test evaluation)
ATTACK_TO_CATEGORY = {
    "normal": "normal",
    # DOS
    "back": "dos",
    "land": "dos",
    "neptune": "dos",
    "pod": "dos",
    "smurf": "dos",
    "teardrop": "dos",
    "apache2": "dos",
    "udpstorm": "dos",
    "processtable": "dos",
    "mailbomb": "dos",
    # PROBE
    "ipsweep": "probe",
    "nmap": "probe",
    "portsweep": "probe",
    "satan": "probe",
    "mscan": "probe",
    "saint": "probe",
    "snmpguess": "probe",
    "snmpgetattack": "probe",
    # R2L
    "ftp_write": "r2l",
    "guess_passwd": "r2l",
    "imap": "r2l",
    "multihop": "r2l",
    "phf": "r2l",
    "spy": "r2l",
    "warezclient": "r2l",
    "sendmail": "r2l",
    "named": "r2l",
    "xlock": "r2l",
    "xsnoop": "r2l",
    # U2R
    "buffer_overflow": "u2r",
    "loadmodule": "u2r",
    "perl": "u2r",
    "rootkit": "u2r",
    "warezmaster": "u2r",
    "httptunnel": "u2r",
    "ps": "u2r",
    "sqlattack": "u2r",
    "xterm": "u2r",
    "worm": "u2r",
}


def _validate_files():
    for path in (TRAIN_FILE, TEST_FILE):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"NSL-KDD file not found: {path}\n"
                "Expected layout: NSL-KDD/nsl-kdd/KDDTrain+.txt and KDDTest+.txt"
            )


def _map_to_category(label):
    label = str(label).strip().lower()
    return ATTACK_TO_CATEGORY.get(label, "r2l")


def _load_split(path, split_name):
    print(f"\nLoading {split_name}: {path}")
    df = pd.read_csv(path, names=NSL_KDD_COLUMNS, header=None)
    print(f"  Raw shape: {df.shape}")

    df = df.drop(columns=["difficulty"])
    df["label_fine"] = df["label"].astype(str).str.strip().str.lower()
    df["label"] = df["label_fine"].map(_map_to_category)

    unknown = df["label"].isna().sum()
    if unknown > 0:
        print(f"  Warning: {unknown} rows with unmapped labels -> r2l")
        df["label"] = df["label"].fillna("r2l")

    dupes = df.duplicated().sum()
    if dupes > 0:
        print(f"  Removing {dupes} duplicate rows...")
        df = df.drop_duplicates().reset_index(drop=True)

    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    before = len(df)
    df = df.dropna().reset_index(drop=True)
    if before - len(df) > 0:
        print(f"  Removed {before - len(df)} rows with NaN")

    return df


def _drop_constant_columns(X):
    constant = [col for col in X.columns if X[col].nunique() <= 1]
    if constant:
        print(f"  Dropping constant columns: {constant}")
        X = X.drop(columns=constant)
    return X


def main():
    print("=" * 70)
    print("NSL-KDD PREPROCESSING")
    print("=" * 70)

    _validate_files()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    train_df = _load_split(TRAIN_FILE, "training set")
    test_df = _load_split(TEST_FILE, "test set")

    print("\nTraining category distribution:")
    train_counts = train_df["label"].value_counts()
    print(train_counts)

    print("\nFine-grained attacks in training (mapped to categories):")
    print(train_df["label_fine"].value_counts())

    train_counts.to_csv(
        os.path.join(OUTPUT_FOLDER, "class_distribution_before.csv")
    )

    X_train_full = train_df.drop(columns=["label", "label_fine"])
    y_train_full = train_df["label"]
    X_test = test_df.drop(columns=["label", "label_fine"])
    y_test = test_df["label"]

    X_train_full = _drop_constant_columns(X_train_full)
    test_drop = [c for c in X_test.columns if c not in X_train_full.columns]
    if test_drop:
        X_test = X_test.drop(columns=test_drop)
    X_test = X_test[X_train_full.columns]

    raw_feature_columns = X_train_full.columns.tolist()

    numerical_columns = (
        X_train_full.select_dtypes(include=np.number).columns.tolist()
    )
    categorical_columns = [
        c for c in CATEGORICAL_COLUMNS if c in X_train_full.columns
    ]

    print(f"\nNumerical features: {len(numerical_columns)}")
    print(f"Categorical features: {len(categorical_columns)}")
    print(f"Raw feature columns saved for live monitoring: {len(raw_feature_columns)}")

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full,
        y_train_full,
        test_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_train_full,
    )

    print(f"\nTrain: {len(X_train)} | Validation: {len(X_val)} | Test: {len(X_test)}")

    preprocessor = ColumnTransformer(
        transformers=[
            ("numerical", StandardScaler(), numerical_columns),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_columns,
            ),
        ],
        remainder="drop",
    )

    X_train_processed = preprocessor.fit_transform(X_train)
    X_val_processed = preprocessor.transform(X_val)
    X_test_processed = preprocessor.transform(X_test)

    feature_names = preprocessor.get_feature_names_out()

    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train)
    y_val_encoded = label_encoder.transform(y_val)
    y_test_encoded = label_encoder.transform(y_test)

    print("\nCategory label mapping:")
    for idx, name in enumerate(label_encoder.classes_):
        print(f"  {idx} -> {name}")

    X_train_processed = np.asarray(X_train_processed, dtype=np.float32)
    X_val_processed = np.asarray(X_val_processed, dtype=np.float32)
    X_test_processed = np.asarray(X_test_processed, dtype=np.float32)

    print("\nApplying SMOTE to training data...")
    print("Before SMOTE:", pd.Series(y_train_encoded).value_counts().to_dict())

    class_counts = pd.Series(y_train_encoded).value_counts()
    majority_class = class_counts.idxmax()
    majority_count = int(class_counts.max())

    if majority_count > SMOTE_MAX_SAMPLES_PER_CLASS:
        undersampler = RandomUnderSampler(
            sampling_strategy={majority_class: SMOTE_MAX_SAMPLES_PER_CLASS},
            random_state=RANDOM_STATE,
        )
        X_balanced, y_balanced = undersampler.fit_resample(
            X_train_processed, y_train_encoded
        )
    else:
        X_balanced, y_balanced = X_train_processed, y_train_encoded

    smote_k = max(1, min(5, int(pd.Series(y_balanced).value_counts().min()) - 1))
    print(f"SMOTE k_neighbors: {smote_k}")
    smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=smote_k)
    X_train_smote, y_train_smote = smote.fit_resample(X_balanced, y_balanced)

    print("After SMOTE:", pd.Series(y_train_smote).value_counts().to_dict())

    X_train_smote_df = pd.DataFrame(X_train_smote, columns=feature_names)
    X_val_df = pd.DataFrame(X_val_processed, columns=feature_names)
    X_test_df = pd.DataFrame(X_test_processed, columns=feature_names)
    X_train_df = pd.DataFrame(X_train_processed, columns=feature_names)

    normal_names = [n for n in label_encoder.classes_ if n.lower() == "normal"]
    if not normal_names:
        raise ValueError("'normal' class not found in NSL-KDD labels.")
    normal_code = list(label_encoder.classes_).index(normal_names[0])
    normal_mask = y_train_encoded == normal_code
    X_train_normal = X_train_df[normal_mask].reset_index(drop=True)

    print(f"\nNormal samples for autoencoder: {len(X_train_normal)}")

    X_train_smote_df.to_csv(os.path.join(OUTPUT_FOLDER, "X_train_smote.csv"), index=False)
    pd.DataFrame({"Label": y_train_smote}).to_csv(
        os.path.join(OUTPUT_FOLDER, "y_train_smote.csv"), index=False
    )
    X_val_df.to_csv(os.path.join(OUTPUT_FOLDER, "X_validation.csv"), index=False)
    pd.DataFrame({"Label": y_val_encoded}).to_csv(
        os.path.join(OUTPUT_FOLDER, "y_validation.csv"), index=False
    )
    X_test_df.to_csv(os.path.join(OUTPUT_FOLDER, "X_test.csv"), index=False)
    pd.DataFrame({"Label": y_test_encoded}).to_csv(
        os.path.join(OUTPUT_FOLDER, "y_test.csv"), index=False
    )
    X_train_normal.to_csv(
        os.path.join(OUTPUT_FOLDER, "X_train_normal_autoencoder.csv"), index=False
    )

    joblib.dump(preprocessor, os.path.join(OUTPUT_FOLDER, "preprocessor.pkl"))
    joblib.dump(label_encoder, os.path.join(OUTPUT_FOLDER, "label_encoder.pkl"))
    pd.DataFrame({"Feature": feature_names}).to_csv(
        os.path.join(OUTPUT_FOLDER, "feature_names.csv"), index=False
    )

    live_metadata = {
        "dataset": "NSL-KDD",
        "label_mode": "category",
        "raw_feature_columns": raw_feature_columns,
        "categorical_columns": categorical_columns,
        "numerical_columns": numerical_columns,
        "attack_to_category": ATTACK_TO_CATEGORY,
        "classes": list(label_encoder.classes_),
    }
    with open(os.path.join(OUTPUT_FOLDER, "live_metadata.json"), "w") as f:
        json.dump(live_metadata, f, indent=2)

    plt.figure(figsize=(10, 5))
    train_counts.plot(kind="bar")
    plt.title("NSL-KDD Category Distribution (Before SMOTE)")
    plt.xlabel("Attack Category")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_FOLDER, "class_distribution_before_smote.png"), dpi=300
    )
    plt.close()

    summary = pd.DataFrame(
        {
            "Metric": [
                "Dataset",
                "Label mode",
                "Train file",
                "Test file",
                "Training samples",
                "Validation samples",
                "Testing samples",
                "Training samples after SMOTE",
                "Processed features",
                "Number of classes",
                "Test rows removed (unseen labels)",
                "Raw features for live monitoring",
            ],
            "Value": [
                "NSL-KDD",
                "category (normal/dos/probe/r2l/u2r)",
                TRAIN_FILE,
                TEST_FILE,
                len(X_train),
                len(X_val),
                len(X_test),
                len(X_train_smote),
                len(feature_names),
                len(label_encoder.classes_),
                0,
                len(raw_feature_columns),
            ],
        }
    )
    summary.to_csv(os.path.join(OUTPUT_FOLDER, "preprocessing_summary.csv"), index=False)

    gc.collect()

    print("\n" + "=" * 70)
    print("NSL-KDD PREPROCESSING COMPLETED")
    print("=" * 70)
    print(f"\nSaved to: {os.path.abspath(OUTPUT_FOLDER)}")
    print(f"Classes: {list(label_encoder.classes_)}")
    print(f"Full test set retained: {len(X_test)} rows")
    print("\nNext step:")
    print("  python hybrid_ids_model.py")


if __name__ == "__main__":
    main()
