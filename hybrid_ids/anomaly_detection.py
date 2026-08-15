import json
import os

import numpy as np

from hybrid_ids.config import BATCH_SIZE, MODEL_FOLDER, THRESHOLD_PERCENTILE


def calculate_reconstruction_error(model, data):
    """Compute per-sample mean squared reconstruction error."""
    reconstructed = model.predict(data, batch_size=BATCH_SIZE, verbose=0)
    error = np.mean(np.square(data - reconstructed), axis=1)
    return error


def compute_reconstruction_errors(autoencoder, X_normal_np, X_validation_np, X_test_np):
    """Calculate reconstruction errors for normal, validation, and test sets."""
    print("\nCalculating reconstruction errors...")

    normal_errors = calculate_reconstruction_error(autoencoder, X_normal_np)
    validation_errors = calculate_reconstruction_error(autoencoder, X_validation_np)
    test_errors = calculate_reconstruction_error(autoencoder, X_test_np)

    print("\nNormal reconstruction error:")
    print("Mean:", np.mean(normal_errors))
    print("Std:", np.std(normal_errors))
    print("Maximum:", np.max(normal_errors))

    return normal_errors, validation_errors, test_errors


def determine_threshold(normal_errors):
    """
    Determine anomaly threshold using only normal training traffic.
    Uses the configured percentile (default: 95th).
    """
    threshold = np.percentile(normal_errors, THRESHOLD_PERCENTILE)

    print("\nAutoencoder anomaly threshold:")
    print(threshold)

    with open(os.path.join(MODEL_FOLDER, "threshold.json"), "w") as f:
        json.dump(
            {
                "threshold": float(threshold),
                "percentile": THRESHOLD_PERCENTILE,
            },
            f,
            indent=4,
        )

    return threshold


def detect_anomalies(reconstruction_errors, threshold):
    """Return binary anomaly predictions (1 = anomaly, 0 = normal)."""
    return (reconstruction_errors > threshold).astype(int)
