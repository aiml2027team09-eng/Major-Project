import json
import os

import hybrid_ids.config as config


def save_results(
    threshold,
    autoencoder_validation_metrics,
    autoencoder_test_metrics,
    xgboost_validation_metrics,
    xgboost_test_metrics,
    hybrid_metrics=None,
):
    """Save all model evaluation results to JSON."""
    results = {
        "dataset": config.ACTIVE_DATASET,
        "Autoencoder": {
            "threshold": float(threshold),
            "validation_accuracy": float(autoencoder_validation_metrics["accuracy"]),
            "validation_precision": float(autoencoder_validation_metrics["precision"]),
            "validation_recall": float(autoencoder_validation_metrics["recall"]),
            "validation_f1": float(autoencoder_validation_metrics["f1"]),
            "test_accuracy": float(autoencoder_test_metrics["accuracy"]),
            "test_precision": float(autoencoder_test_metrics["precision"]),
            "test_recall": float(autoencoder_test_metrics["recall"]),
            "test_f1": float(autoencoder_test_metrics["f1"]),
        },
        "XGBoost": {
            "validation_accuracy": float(xgboost_validation_metrics["accuracy"]),
            "validation_precision": float(xgboost_validation_metrics["precision"]),
            "validation_recall": float(xgboost_validation_metrics["recall"]),
            "validation_f1": float(xgboost_validation_metrics["f1"]),
            "test_accuracy": float(xgboost_test_metrics["accuracy"]),
            "test_precision": float(xgboost_test_metrics["precision"]),
            "test_recall": float(xgboost_test_metrics["recall"]),
            "test_f1": float(xgboost_test_metrics["f1"]),
        },
    }

    if hybrid_metrics is not None:
        results["Hybrid"] = {
            "anomalies_detected": hybrid_metrics["anomalies_detected"],
            "classification_accuracy": float(hybrid_metrics["classification_accuracy"]),
            "classification_precision": float(
                hybrid_metrics["classification_precision"]
            ),
            "classification_recall": float(hybrid_metrics["classification_recall"]),
            "classification_f1": float(hybrid_metrics["classification_f1"]),
        }

    with open(os.path.join(config.MODEL_FOLDER, "model_results.json"), "w") as f:
        json.dump(results, f, indent=4)


def print_final_summary(autoencoder_test_metrics, xgboost_test_metrics):
    """Print the final training summary and generated files."""
    print("\n")
    print("=" * 70)
    print("HYBRID IDS TRAINING COMPLETED")
    print("=" * 70)

    print("\nModels saved in:")
    print(os.path.abspath(config.MODEL_FOLDER))

    print("\nGenerated files:")
    for file in sorted(os.listdir(config.MODEL_FOLDER)):
        print(" -", file)

    print("\n")
    print("=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)

    print("\nAUTOENCODER")
    print("Accuracy:", autoencoder_test_metrics["accuracy"])
    print("Precision:", autoencoder_test_metrics["precision"])
    print("Recall:", autoencoder_test_metrics["recall"])
    print("F1:", autoencoder_test_metrics["f1"])

    print("\nXGBOOST")
    print("Accuracy:", xgboost_test_metrics["accuracy"])
    print("Precision:", xgboost_test_metrics["precision"])
    print("Recall:", xgboost_test_metrics["recall"])
    print("F1:", xgboost_test_metrics["f1"])

    print("\n")
    print("=" * 70)
    print("DONE")
    print("=" * 70)
