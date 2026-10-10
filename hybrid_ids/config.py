import os



import numpy as np

import tensorflow as tf



from dataset_config import DEFAULT_DATASET, get_profile, resolve_model_folder



_profile = get_profile(DEFAULT_DATASET)

ACTIVE_DATASET = _profile.name

DATA_FOLDER = _profile.data_folder

MODEL_FOLDER = resolve_model_folder(_profile)

os.makedirs(MODEL_FOLDER, exist_ok=True)



RANDOM_STATE = 42

np.random.seed(RANDOM_STATE)

tf.random.set_seed(RANDOM_STATE)



# Set True to use GPU where supported (XGBoost CUDA on Windows; TF needs WSL2)

USE_GPU = True



# Autoencoder training

EPOCHS = 100

BATCH_SIZE = 512

LEARNING_RATE = 0.0005

DROPOUT_RATE = 0.2

EARLY_STOPPING_PATIENCE = 10



# Threshold: fallback percentile if validation tuning is unavailable

THRESHOLD_PERCENTILE = 99



# Validation-based threshold search (optimizes F1 with precision constraint)

THRESHOLD_SEARCH_MIN_PERCENTILE = 80.0

THRESHOLD_SEARCH_MAX_PERCENTILE = 99.5

THRESHOLD_SEARCH_STEPS = 250

MIN_VALIDATION_PRECISION = 0.85


