# ================================================================
# CICIDS2018 DATA PREPROCESSING PIPELINE
# ================================================================
#
# This program:
#
# 1. Loads a CICIDS2018 CSV file
# 2. Cleans column names
# 3. Removes duplicate rows
# 4. Handles infinity and missing values
# 5. Removes invalid/constant columns
# 6. Separates features and target
# 7. Splits data into train/validation/test
# 8. Encodes categorical features
# 9. Scales numerical features
# 10. Applies SMOTE ONLY to training data
# 11. Creates normal-only data for Autoencoder
# 12. Saves all processed datasets
# 13. Saves preprocessing objects
#
# ================================================================


# ================================================================
# 1. IMPORT LIBRARIES
# ================================================================

import gc
import os
import warnings
import joblib

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (
    StandardScaler,
    OneHotEncoder,
    LabelEncoder
)
from sklearn.compose import ColumnTransformer

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

import matplotlib.pyplot as plt


warnings.filterwarnings("ignore")


# ================================================================
# 2. USER CONFIGURATION
# ================================================================

# ------------------------------------------------
# PUT YOUR CSV FILE PATH HERE
# ------------------------------------------------
#
# Windows example:
#
# r"C:\Users\Ansh\Downloads\CICIDS2018.csv"
#
# Another example:
#
# r"D:\Projects\IDS\Friday-16-02-2018.csv"
#
# ------------------------------------------------

CSV_FILE = r"D:\Users\anshp\Final year project\Major-Project\cic.csv"


# ------------------------------------------------
# OUTPUT FOLDER
# ------------------------------------------------

OUTPUT_FOLDER = "processed_CICIDS2018"


# ------------------------------------------------
# TRAIN / VALIDATION / TEST SPLIT
# ------------------------------------------------

TRAIN_SIZE = 0.70
VALIDATION_SIZE = 0.15
TEST_SIZE = 0.15


# ------------------------------------------------
# RANDOM STATE
# ------------------------------------------------

RANDOM_STATE = 42

# Cap samples per class before SMOTE to avoid memory errors on large datasets.
# Benign is undersampled to this limit; then SMOTE balances all classes equally.
SMOTE_MAX_SAMPLES_PER_CLASS = 80000

# Memory-efficient CSV loading (rows per chunk). Lower if RAM is limited.
CHUNK_SIZE = 100_000

# Optional row limit for low-RAM systems (None = use full file).
# Example: MAX_ROWS = 500_000
MAX_ROWS = None

INVALID_LABELS = ["", "nan", "NaN", "None", "null"]
LABEL_CANDIDATES = ["Label", "label", "LABEL"]


def _find_label_column(columns):
    for column in LABEL_CANDIDATES:
        if column in columns:
            return column
    return None


def _downcast_numeric_frame(df):
    """Reduce memory by using float32/int32 where possible."""
    for column in df.select_dtypes(include=["float64"]).columns:
        df[column] = df[column].astype(np.float32)
    for column in df.select_dtypes(include=["int64"]).columns:
        df[column] = pd.to_numeric(df[column], downcast="integer")
    return df


def load_and_clean_csv(csv_path):
    """
    Load large CSV files in chunks to avoid memory errors.
    Cleans labels, handles inf/nan, deduplicates, returns a DataFrame.
    """
    temp_clean = os.path.join(OUTPUT_FOLDER, "_temp_clean.csv")
    temp_dedup = os.path.join(OUTPUT_FOLDER, "_temp_dedup.csv")

    for path in (temp_clean, temp_dedup):
        if os.path.exists(path):
            os.remove(path)

    label_column = None
    total_read = 0
    total_written = 0
    first_write = True
    class_counts = {}

    print("\n[1/15] Loading CSV file in chunks (memory-efficient)...")

    for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, low_memory=True):
        if MAX_ROWS is not None and total_read >= MAX_ROWS:
            break
        if MAX_ROWS is not None:
            chunk = chunk.head(MAX_ROWS - total_read)

        total_read += len(chunk)
        chunk.columns = chunk.columns.astype(str).str.strip()

        if label_column is None:
            label_column = _find_label_column(chunk.columns)
            if label_column is None:
                raise ValueError(
                    "\nCould not find the Label column.\n\n"
                    "Available columns are:\n"
                    + str(chunk.columns.tolist())
                )
            print("Label column:", label_column)

        chunk[label_column] = chunk[label_column].astype(str).str.strip()
        chunk = chunk[~chunk[label_column].isin(INVALID_LABELS)]

        for label, count in chunk[label_column].value_counts().items():
            class_counts[label] = class_counts.get(label, 0) + int(count)

        numeric_columns = chunk.select_dtypes(include=np.number).columns
        if len(numeric_columns) > 0:
            chunk[numeric_columns] = chunk[numeric_columns].replace(
                [np.inf, -np.inf], np.nan
            )

        chunk = chunk.dropna()
        chunk.to_csv(temp_clean, mode="a", header=first_write, index=False)
        first_write = False
        total_written += len(chunk)

        del chunk
        gc.collect()

    print("CSV loaded successfully.")
    print(f"Rows read: {total_read:,} | Rows after cleaning: {total_written:,}")

    print("\n[4/15] Removing duplicate rows (chunked)...")
    seen_hashes = set()
    duplicate_count = 0
    kept_rows = 0
    first_dedup = True

    for chunk in pd.read_csv(temp_clean, chunksize=CHUNK_SIZE, low_memory=True):
        row_hashes = pd.util.hash_pandas_object(chunk, index=False)
        keep_mask = []
        for row_hash in row_hashes:
            if row_hash in seen_hashes:
                keep_mask.append(False)
                duplicate_count += 1
            else:
                seen_hashes.add(row_hash)
                keep_mask.append(True)

        chunk = chunk.loc[keep_mask]
        if len(chunk) > 0:
            chunk.to_csv(temp_dedup, mode="a", header=first_dedup, index=False)
            first_dedup = False
            kept_rows += len(chunk)

        del chunk, row_hashes, keep_mask
        gc.collect()

    print("Duplicate rows found:", duplicate_count)
    print("Shape after duplicate removal:", (kept_rows, "columns pending"))

    print("\nLoading cleaned dataset into memory...")
    df = pd.read_csv(temp_dedup, low_memory=True)
    df = _downcast_numeric_frame(df)

    for path in (temp_clean, temp_dedup):
        if os.path.exists(path):
            os.remove(path)

    gc.collect()
    class_distribution = pd.Series(class_counts).sort_values(ascending=False)
    return df, label_column, class_distribution, duplicate_count


# ================================================================
# 3. CREATE OUTPUT FOLDER
# ================================================================

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


# ================================================================
# 4. CHECK FILE
# ================================================================

if not os.path.exists(CSV_FILE):

    raise FileNotFoundError(
        "\nCSV file was not found.\n\n"
        "Please check the CSV_FILE path in the code.\n\n"
        "Example:\n"
        r'C:\Users\Ansh\Downloads\CICIDS2018.csv'
    )


print("=" * 70)
print("CICIDS2018 PREPROCESSING")
print("=" * 70)


# ================================================================
# 5–10. LOAD AND CLEAN CSV (chunked, memory-efficient)
# ================================================================

df, label_column, class_distribution_before, duplicate_count = load_and_clean_csv(
    CSV_FILE
)

print("\nOriginal dataset shape:")
print(df.shape)

print("\n[2/15] Column names cleaned during chunked load.")

print("\n[3/15] Labels cleaned during chunked load.")

print("\nOriginal class distribution:")
print(class_distribution_before)

class_distribution_before.to_csv(
    os.path.join(OUTPUT_FOLDER, "class_distribution_before.csv")
)

print("\n[5/15] Infinite values handled during chunked load.")
print("\n[6/15] Missing values handled during chunked load.")

print("\nChecking remaining missing values...")

missing_values = (
    df.isnull()
    .sum()
    .sort_values(
        ascending=False
    )
)

missing_values = (
    missing_values[
        missing_values > 0
    ]
)

if len(missing_values) > 0:

    print("\nColumns with missing values:")

    print(
        missing_values.head(20)
    )

else:

    print(
        "No missing values found."
    )


# ================================================================
# 13. REMOVE COMPLETELY EMPTY COLUMNS
# ================================================================

empty_columns = (
    df.columns[
        df.isnull().all()
    ].tolist()
)

if len(empty_columns) > 0:

    print(
        "\nCompletely empty columns:"
    )

    print(
        empty_columns
    )

    df = df.drop(
        columns=empty_columns
    )


# ================================================================
# 14. REMOVE ROWS WITH MISSING VALUES
# ================================================================

before_nan = len(df)

df = (
    df
    .dropna()
    .reset_index(drop=True)
)

after_nan = len(df)

print(
    "\nRows removed due to missing values:",
    before_nan - after_nan
)


# ================================================================
# 15. REMOVE TIMESTAMP
# ================================================================

print("\n[7/15] Handling Timestamp...")

timestamp_column = None

for column in df.columns:

    if column.lower() == "timestamp":

        timestamp_column = column
        break


if timestamp_column is not None:

    print(
        "Timestamp column found:",
        timestamp_column
    )

    # Save timestamp separately.
    #
    # We may need this later for temporal
    # generalization / concept drift experiments.

    timestamp_data = (
        df[timestamp_column]
        .copy()
    )

    df = df.drop(
        columns=[timestamp_column]
    )

else:

    timestamp_data = None

    print(
        "No Timestamp column found."
    )


# ================================================================
# 16. SEPARATE FEATURES AND TARGET
# ================================================================

print("\n[8/15] Separating features and labels...")

X = df.drop(
    columns=[label_column]
)

y = df[label_column]

original_row_count = len(df)
del df
gc.collect()


print(
    "Number of samples:",
    len(X)
)

print(
    "Number of features:",
    X.shape[1]
)


# ================================================================
# 17. REMOVE CONSTANT FEATURES
# ================================================================

print("\n[9/15] Checking constant features...")

constant_columns = []

for column in X.columns:

    if X[column].nunique() <= 1:

        constant_columns.append(
            column
        )


if len(constant_columns) > 0:

    print(
        "Constant columns found:"
    )

    print(
        constant_columns
    )

    X = X.drop(
        columns=constant_columns
    )

else:

    print(
        "No constant columns found."
    )


# ================================================================
# 18. IDENTIFY NUMERICAL AND CATEGORICAL FEATURES
# ================================================================

numerical_columns = (
    X.select_dtypes(
        include=np.number
    ).columns.tolist()
)

categorical_columns = (
    X.select_dtypes(
        include=[
            "object",
            "category"
        ]
    ).columns.tolist()
)


print("\nNumerical features:")
print(
    len(numerical_columns)
)

print(
    numerical_columns
)

print("\nCategorical features:")
print(
    len(categorical_columns)
)

print(
    categorical_columns
)


# ================================================================
# 19. SPLIT DATA
# ================================================================

print("\n[10/15] Splitting dataset...")

# First split:
#
# 70% TRAIN
# 30% TEMPORARY

X_train, X_temp, y_train, y_temp = (
    train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=y
    )
)


# Second split:
#
# TEMPORARY = 30%
#
# Half → validation = 15%
# Half → test       = 15%

X_val, X_test, y_val, y_test = (
    train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=y_temp
    )
)


print(
    "\nTraining samples:",
    len(X_train)
)

print(
    "Validation samples:",
    len(X_val)
)

print(
    "Testing samples:",
    len(X_test)
)


# ================================================================
# 20. CREATE PREPROCESSING PIPELINE
# ================================================================

print(
    "\n[11/15] Creating preprocessing pipeline..."
)


# Numerical features:
#
# StandardScaler converts features roughly to:
#
# mean = 0
# standard deviation = 1

numeric_transformer = StandardScaler()


# Categorical features:
#
# Convert categories into binary columns.

if len(categorical_columns) > 0:

    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

else:

    categorical_transformer = "drop"


# Create ColumnTransformer

preprocessor = ColumnTransformer(

    transformers=[

        (
            "numerical",
            numeric_transformer,
            numerical_columns
        ),

        (
            "categorical",
            categorical_transformer,
            categorical_columns
        )

    ],

    remainder="drop"
)


# ================================================================
# 21. FIT ONLY ON TRAINING DATA
# ================================================================

print(
    "\n[12/15] Fitting preprocessing on TRAINING data..."
)


X_train_processed = (
    preprocessor
    .fit_transform(X_train)
)


# IMPORTANT:
#
# Validation and test are transformed,
# but NOT fitted again.

X_val_processed = (
    preprocessor
    .transform(X_val)
)

X_test_processed = (
    preprocessor
    .transform(X_test)
)


print(
    "Training processed shape:",
    X_train_processed.shape
)

print(
    "Validation processed shape:",
    X_val_processed.shape
)

print(
    "Testing processed shape:",
    X_test_processed.shape
)


# ================================================================
# 22. GET PROCESSED FEATURE NAMES
# ================================================================

try:

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

except Exception:

    feature_names = [
        f"feature_{i}"
        for i in range(
            X_train_processed.shape[1]
        )
    ]


# Convert NumPy arrays to DataFrames

X_train_processed = pd.DataFrame(
    X_train_processed,
    columns=feature_names
)

X_val_processed = pd.DataFrame(
    X_val_processed,
    columns=feature_names
)

X_test_processed = pd.DataFrame(
    X_test_processed,
    columns=feature_names
)


# ================================================================
# 23. ENCODE TARGET LABELS
# ================================================================

print(
    "\n[13/15] Encoding attack labels..."
)

label_encoder = LabelEncoder()


y_train_encoded = (
    label_encoder
    .fit_transform(y_train)
)

y_val_encoded = (
    label_encoder
    .transform(y_val)
)

y_test_encoded = (
    label_encoder
    .transform(y_test)
)


print(
    "\nLabel mapping:"
)

for number, label in enumerate(
    label_encoder.classes_
):

    print(
        number,
        "->",
        label
    )


# ================================================================
# 24. APPLY SMOTE ONLY TO TRAINING DATA
# ================================================================

print(
    "\n[14/15] Applying SMOTE to training data..."
)


print(
    "\nClass distribution BEFORE SMOTE:"
)

print(
    pd.Series(
        y_train_encoded
    ).value_counts()
)

# Use float32 to reduce memory during resampling
X_train_processed = np.asarray(X_train_processed, dtype=np.float32)
X_val_processed = np.asarray(X_val_processed, dtype=np.float32)
X_test_processed = np.asarray(X_test_processed, dtype=np.float32)

class_counts = pd.Series(y_train_encoded).value_counts()
majority_class = class_counts.idxmax()
majority_count = int(class_counts.max())

if majority_count > SMOTE_MAX_SAMPLES_PER_CLASS:
    print(
        f"\nUndersampling majority class ({majority_class}) "
        f"from {majority_count} to {SMOTE_MAX_SAMPLES_PER_CLASS} ..."
    )
    undersampler = RandomUnderSampler(
        sampling_strategy={majority_class: SMOTE_MAX_SAMPLES_PER_CLASS},
        random_state=RANDOM_STATE,
    )
    X_train_balanced, y_train_balanced = undersampler.fit_resample(
        X_train_processed,
        y_train_encoded,
    )
else:
    X_train_balanced, y_train_balanced = X_train_processed, y_train_encoded

print("\nClass distribution before SMOTE (after optional undersampling):")
print(pd.Series(y_train_balanced).value_counts())

smote = SMOTE(
    random_state=RANDOM_STATE,
)

X_train_smote, y_train_smote = (
    smote.fit_resample(
        X_train_balanced,
        y_train_balanced,
    )
)

# Convert back to DataFrames for saving
X_train_smote = pd.DataFrame(X_train_smote, columns=feature_names)
X_val_processed = pd.DataFrame(X_val_processed, columns=feature_names)
X_test_processed = pd.DataFrame(X_test_processed, columns=feature_names)
X_train_processed = pd.DataFrame(X_train_processed, columns=feature_names)


print(
    "\nClass distribution AFTER SMOTE:"
)

print(
    pd.Series(
        y_train_smote
    ).value_counts()
)


# ================================================================
# 25. CREATE NORMAL-ONLY DATA FOR AUTOENCODER
# ================================================================
#
# IMPORTANT:
#
# The Autoencoder should learn normal traffic.
#
# Therefore, we DON'T use the SMOTE dataset for
# Autoencoder training.
#
# We use only BENIGN samples from the ORIGINAL
# TRAINING split.
#
# ================================================================

print(
    "\nCreating normal-only data for Autoencoder..."
)


# Find the numerical label representing BENIGN

benign_candidates = [
    i
    for i, label in enumerate(
        label_encoder.classes_
    )
    if label.upper() == "BENIGN"
]


if len(benign_candidates) == 0:

    print(
        "\nWARNING:"
    )

    print(
        "BENIGN class was not found."
    )

    print(
        "Autoencoder normal-data file will not be created."
    )

    X_train_normal = pd.DataFrame()

else:

    benign_label = (
        benign_candidates[0]
    )

    normal_mask = (
        y_train_encoded
        == benign_label
    )

    X_train_normal = (
        X_train_processed[
            normal_mask
        ]
        .reset_index(drop=True)
    )

    print(
        "Normal training samples:",
        len(X_train_normal)
    )


# ================================================================
# 26. SAVE DATASETS
# ================================================================

print(
    "\n[15/15] Saving processed datasets..."
)


# -------------------------------
# Training data after SMOTE
# -------------------------------

X_train_smote.to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "X_train_smote.csv"
    ),
    index=False
)

pd.DataFrame(
    {
        "Label": y_train_smote
    }
).to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "y_train_smote.csv"
    ),
    index=False
)


# -------------------------------
# Validation data
# -------------------------------

X_val_processed.to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "X_validation.csv"
    ),
    index=False
)

pd.DataFrame(
    {
        "Label": y_val_encoded
    }
).to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "y_validation.csv"
    ),
    index=False
)


# -------------------------------
# Test data
# -------------------------------

X_test_processed.to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "X_test.csv"
    ),
    index=False
)

pd.DataFrame(
    {
        "Label": y_test_encoded
    }
).to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "y_test.csv"
    ),
    index=False
)


# -------------------------------
# Normal data for Autoencoder
# -------------------------------

if len(X_train_normal) > 0:

    X_train_normal.to_csv(
        os.path.join(
            OUTPUT_FOLDER,
            "X_train_normal_autoencoder.csv"
        ),
        index=False
    )


# ================================================================
# 27. SAVE PREPROCESSING OBJECTS
# ================================================================

joblib.dump(
    preprocessor,
    os.path.join(
        OUTPUT_FOLDER,
        "preprocessor.pkl"
    )
)

joblib.dump(
    label_encoder,
    os.path.join(
        OUTPUT_FOLDER,
        "label_encoder.pkl"
    )
)


# ================================================================
# 28. SAVE FEATURE NAMES
# ================================================================

pd.DataFrame(
    {
        "Feature": feature_names
    }
).to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "feature_names.csv"
    ),
    index=False
)


# ================================================================
# 29. CREATE FINAL SUMMARY
# ================================================================

summary = {

    "Original rows": original_row_count,

    "Original features":
        X.shape[1],

    "Training samples":
        len(X_train),

    "Validation samples":
        len(X_val),

    "Testing samples":
        len(X_test),

    "Training samples after SMOTE":
        len(X_train_smote),

    "Number of processed features":
        X_train_processed.shape[1],

    "Number of classes":
        len(label_encoder.classes_),

    "Duplicate rows removed":
        duplicate_count,

    "Rows removed due to NaN":
        before_nan - after_nan
}


summary_df = pd.DataFrame(
    list(summary.items()),
    columns=[
        "Metric",
        "Value"
    ]
)


summary_df.to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "preprocessing_summary.csv"
    ),
    index=False
)


# ================================================================
# 30. CREATE CLASS DISTRIBUTION GRAPH
# ================================================================

plt.figure(
    figsize=(12, 6)
)

class_distribution_before.plot(
    kind="bar"
)

plt.title(
    "CICIDS2018 Class Distribution Before SMOTE"
)

plt.xlabel(
    "Attack Class"
)

plt.ylabel(
    "Number of Samples"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_FOLDER,
        "class_distribution_before_smote.png"
    ),
    dpi=300
)

plt.close()


# ================================================================
# 31. FINAL OUTPUT
# ================================================================

print("\n")
print("=" * 70)
print("PREPROCESSING COMPLETED SUCCESSFULLY")
print("=" * 70)

print(
    "\nProcessed files saved in:"
)

print(
    os.path.abspath(
        OUTPUT_FOLDER
    )
)


print("\nFiles created:")

for file in sorted(
    os.listdir(
        OUTPUT_FOLDER
    )
):

    print(
        " -",
        file
    )


print("\nFinal dataset summary:")
print(
    summary_df.to_string(
        index=False
    )
)


print("\n")
print("=" * 70)
print("NEXT STEP: MODEL TRAINING")
print("=" * 70)