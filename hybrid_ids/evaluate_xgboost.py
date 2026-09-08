import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

import hybrid_ids.config as config


def _compute_metrics(y_true, y_pred):
    """Compute weighted classification metrics."""
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(
            y_true, y_pred, average="weighted", zero_division=0
        ),
        "recall": recall_score(y_true, y_pred, average="weighted", zero_division=0),
        "f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }


def _print_metrics(metrics):
    """Print classification metrics."""
    print("\nAccuracy:", metrics["accuracy"])
    print("Precision:", metrics["precision"])
    print("Recall:", metrics["recall"])
    print("F1 Score:", metrics["f1"])


def evaluate_xgboost_split(xgb_model, X_np, y_np, label_encoder, split_name):
    """Evaluate XGBoost on a given split and print results."""
    print("\n")
    print("=" * 70)
    print(f"XGBOOST {split_name.upper()} RESULTS")
    print("=" * 70)

    predictions = xgb_model.predict(X_np)
    metrics = _compute_metrics(y_np, predictions)
    _print_metrics(metrics)

    print("\nClassification Report:")
    print(
        classification_report(
            y_np,
            predictions,
            target_names=label_encoder.classes_,
            zero_division=0,
        )
    )

    return predictions, metrics


def plot_confusion_matrix(y_true, y_pred, label_encoder):
    """Generate and save the XGBoost confusion matrix heatmap."""
    confusion = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(12, 10))
    sns.heatmap(
        confusion,
        annot=True,
        fmt="d",
        xticklabels=label_encoder.classes_,
        yticklabels=label_encoder.classes_,
    )
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.title("XGBoost Confusion Matrix")
    plt.tight_layout()
    plt.savefig(
        os.path.join(config.MODEL_FOLDER, "xgboost_confusion_matrix.png"),
        dpi=300,
    )
    plt.close()
