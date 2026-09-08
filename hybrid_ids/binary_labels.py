import os

import joblib

import hybrid_ids.config as config


def convert_to_binary_labels(labels, label_encoder):
    """
    Convert multi-class labels to binary labels.
    Normal/BENIGN = 0, anything else = ATTACK (1).
    """
    benign_indices = [
        index
        for index, label in enumerate(label_encoder.classes_)
        if str(label).upper() in ("BENIGN", "NORMAL")
    ]

    if len(benign_indices) == 0:
        raise ValueError("Normal/BENIGN class not found in label encoder.")

    benign_class = benign_indices[0]
    return (labels != benign_class).astype(int)


def load_label_encoder():
    """Load the fitted label encoder from preprocessing."""
    return joblib.load(os.path.join(config.DATA_FOLDER, "label_encoder.pkl"))
