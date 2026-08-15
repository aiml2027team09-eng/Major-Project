import os

import joblib

from hybrid_ids.config import DATA_FOLDER


def convert_to_binary_labels(labels, label_encoder):
    """
    Convert multi-class labels to binary labels.
    Label 0 = BENIGN, anything else = ATTACK.
    """
    benign_indices = [
        index
        for index, label in enumerate(label_encoder.classes_)
        if label.upper() == "BENIGN"
    ]

    if len(benign_indices) == 0:
        raise ValueError("BENIGN class not found.")

    benign_class = benign_indices[0]
    return (labels != benign_class).astype(int)


def load_label_encoder():
    """Load the fitted label encoder from preprocessing."""
    return joblib.load(os.path.join(DATA_FOLDER, "label_encoder.pkl"))
