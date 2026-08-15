import os

import numpy as np
import tensorflow as tf

DATA_FOLDER = "processed_CICIDS2018"
MODEL_FOLDER = "trained_models"

os.makedirs(MODEL_FOLDER, exist_ok=True)

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

EPOCHS = 50
BATCH_SIZE = 256
LEARNING_RATE = 0.001

THRESHOLD_PERCENTILE = 95
