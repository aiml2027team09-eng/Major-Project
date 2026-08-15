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
# 5. LOAD CSV
# ================================================================

print("\n[1/15] Loading CSV file...")

df = pd.read_csv(
    CSV_FILE,
    low_memory=False
)

print("CSV loaded successfully.")

print("\nOriginal dataset shape:")
print(df.shape)


# ================================================================
# 6. CLEAN COLUMN NAMES
# ================================================================

print("\n[2/15] Cleaning column names...")

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)


# ================================================================
# 7. FIND LABEL COLUMN
# ================================================================

possible_label_columns = [
    "Label",
    "label",
    "LABEL"
]

label_column = None

for column in possible_label_columns:

    if column in df.columns:

        label_column = column
        break


if label_column is None:

    raise ValueError(
        "\nCould not find the Label column.\n\n"
        "Available columns are:\n"
        + str(df.columns.tolist())
    )


print("Label column:", label_column)


# ================================================================
# 8. CLEAN LABELS
# ================================================================

print("\n[3/15] Cleaning labels...")

df[label_column] = (
    df[label_column]
    .astype(str)
    .str.strip()
)


# Remove empty / invalid labels

invalid_labels = [
    "",
    "nan",
    "NaN",
    "None",
    "null"
]

before_labels = len(df)

df = df[
    ~df[label_column].isin(
        invalid_labels
    )
].copy()

after_labels = len(df)

print(
    "Rows removed because of invalid labels:",
    before_labels - after_labels
)


# ================================================================
# 9. INITIAL CLASS DISTRIBUTION
# ================================================================

print("\nOriginal class distribution:")

class_distribution_before = (
    df[label_column]
    .value_counts()
)

print(
    class_distribution_before
)


# Save original class distribution

class_distribution_before.to_csv(
    os.path.join(
        OUTPUT_FOLDER,
        "class_distribution_before.csv"
    )
)


# ================================================================
# 10. REMOVE DUPLICATES
# ================================================================

print("\n[4/15] Removing duplicate rows...")

duplicate_count = df.duplicated().sum()

print(
    "Duplicate rows found:",
    duplicate_count
)

df = (
    df
    .drop_duplicates()
    .reset_index(drop=True)
)

print(
    "Shape after duplicate removal:",
    df.shape
)


# ================================================================
# 11. HANDLE INFINITE VALUES
# ================================================================

print("\n[5/15] Handling infinite values...")

numeric_columns_temp = (
    df.select_dtypes(
        include=np.number
    ).columns
)

df[numeric_columns_temp] = (
    df[numeric_columns_temp]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
)


# ================================================================
# 12. MISSING VALUE REPORT
# ================================================================

print("\n[6/15] Checking missing values...")

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

    "Original rows": len(df),

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