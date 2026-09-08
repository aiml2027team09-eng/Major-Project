import json
import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

import hybrid_ids.config as config


def calculate_reconstruction_error(model, data):
    """Compute per-sample mean squared reconstruction error."""
    reconstructed = model.predict(data, batch_size=config.BATCH_SIZE, verbose=0)
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


def _evaluate_threshold(validation_errors, validation_binary_true, threshold):
    """Return precision, recall, F1, and accuracy for a candidate threshold."""
    predictions = (validation_errors > threshold).astype(int)
    precision = precision_score(
        validation_binary_true, predictions, zero_division=0
    )
    recall = recall_score(validation_binary_true, predictions, zero_division=0)
    f1 = f1_score(validation_binary_true, predictions, zero_division=0)
    accuracy = accuracy_score(validation_binary_true, predictions)
    return precision, recall, f1, accuracy


def _threshold_score(precision, recall, f1, accuracy, metric="f1"):
    """Pick the scalar used to rank candidate thresholds."""
    if metric == "accuracy":
        return (accuracy, f1, precision, recall)
    if metric == "balanced":
        return ((accuracy + f1) / 2.0, accuracy, f1, precision)
    return (f1, precision, recall, accuracy)


def determine_threshold(
    normal_errors,
    validation_errors=None,
    validation_binary_true=None,
    threshold_metric="f1",
):
    """
    Select anomaly threshold using validation-set tuning.

    Searches percentile-based candidates on normal training errors and picks
    the threshold with the best validation F1 among candidates that meet
    MIN_VALIDATION_PRECISION. Falls back to the configured percentile.
    """
    fallback_threshold = float(
        np.percentile(normal_errors, config.THRESHOLD_PERCENTILE)
    )

    if validation_errors is None or validation_binary_true is None:
        threshold = fallback_threshold
        metadata = {
            "threshold": threshold,
            "method": "percentile_fallback",
            "percentile": config.THRESHOLD_PERCENTILE,
        }
    else:
        percentiles = np.linspace(
            config.THRESHOLD_SEARCH_MIN_PERCENTILE,
            config.THRESHOLD_SEARCH_MAX_PERCENTILE,
            config.THRESHOLD_SEARCH_STEPS,
        )
        candidates = np.unique(np.percentile(normal_errors, percentiles))

        best = None
        best_meets_precision = None

        for candidate in candidates:
            precision, recall, f1, accuracy = _evaluate_threshold(
                validation_errors,
                validation_binary_true,
                candidate,
            )
            score = _threshold_score(precision, recall, f1, accuracy, threshold_metric)
            if precision >= config.MIN_VALIDATION_PRECISION:
                if best_meets_precision is None or score > best_meets_precision["score"]:
                    best_meets_precision = {
                        "threshold": float(candidate),
                        "precision": float(precision),
                        "recall": float(recall),
                        "f1": float(f1),
                        "accuracy": float(accuracy),
                        "score": score,
                    }
            if best is None or score > best["score"]:
                best = {
                    "threshold": float(candidate),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1": float(f1),
                    "accuracy": float(accuracy),
                    "score": score,
                }

        chosen = best_meets_precision or best
        threshold = chosen["threshold"]
        metadata = {
            "threshold": threshold,
            "method": "validation_tuning",
            "threshold_metric": threshold_metric,
            "fallback_percentile": config.THRESHOLD_PERCENTILE,
            "fallback_threshold": fallback_threshold,
            "min_validation_precision": config.MIN_VALIDATION_PRECISION,
            "validation_precision": chosen["precision"],
            "validation_recall": chosen["recall"],
            "validation_f1": chosen["f1"],
            "validation_accuracy": chosen["accuracy"],
            "used_precision_constraint": best_meets_precision is not None,
        }

        _plot_threshold_tuning(
            normal_errors,
            validation_errors,
            validation_binary_true,
            threshold,
        )

    print("\nAutoencoder anomaly threshold:")
    print(threshold)
    if metadata.get("method") == "validation_tuning":
        print(
            f"Selected via validation tuning ({threshold_metric}) | "
            f"accuracy={metadata.get('validation_accuracy', 0):.4f} "
            f"precision={metadata['validation_precision']:.4f} "
            f"recall={metadata['validation_recall']:.4f} "
            f"f1={metadata['validation_f1']:.4f}"
        )

    with open(os.path.join(config.MODEL_FOLDER, "threshold.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    return threshold


def _plot_threshold_tuning(
    normal_errors,
    validation_errors,
    validation_binary_true,
    chosen_threshold,
):
    """Plot precision/recall/F1 vs threshold for the validation search."""
    percentiles = np.linspace(
        config.THRESHOLD_SEARCH_MIN_PERCENTILE,
        config.THRESHOLD_SEARCH_MAX_PERCENTILE,
        config.THRESHOLD_SEARCH_STEPS,
    )
    thresholds = np.unique(np.percentile(normal_errors, percentiles))

    precisions = []
    recalls = []
    f1_scores = []

    for threshold in thresholds:
        precision, recall, f1, _accuracy = _evaluate_threshold(
            validation_errors,
            validation_binary_true,
            threshold,
        )
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1)

    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, precisions, label="Precision")
    plt.plot(thresholds, recalls, label="Recall")
    plt.plot(thresholds, f1_scores, label="F1 Score")
    plt.axvline(
        chosen_threshold,
        color="red",
        linestyle="--",
        label=f"Chosen ({chosen_threshold:.4f})",
    )
    plt.xlabel("Threshold")
    plt.ylabel("Score")
    plt.title("Autoencoder Threshold Tuning (Validation Set)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        os.path.join(config.MODEL_FOLDER, "threshold_tuning.png"),
        dpi=300,
    )
    plt.close()


def detect_anomalies(reconstruction_errors, threshold):
    """Return binary anomaly predictions (1 = anomaly, 0 = normal)."""
    return (reconstruction_errors > threshold).astype(int)
