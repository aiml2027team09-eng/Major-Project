import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)


def evaluate_hybrid_pipeline(
    xgb_model,
    X_test_np,
    y_test_np,
    test_anomaly_predictions,
    label_encoder,
):
    """
    Evaluate the hybrid pipeline:
    Autoencoder detects anomalies → XGBoost classifies them.
    """
    print("\n")
    print("=" * 70)
    print("HYBRID MODEL EVALUATION")
    print("=" * 70)

    anomaly_indices = np.where(test_anomaly_predictions == 1)[0]

    print("\nTotal test samples:", len(X_test_np))
    print("Samples detected as anomalies:", len(anomaly_indices))

    if len(anomaly_indices) == 0:
        print("\nNo anomalies were detected.")
        return None

    X_test_anomalies = X_test_np[anomaly_indices]
    y_test_anomalies = y_test_np[anomaly_indices]
    hybrid_predictions = xgb_model.predict(X_test_anomalies)

    hybrid_accuracy = accuracy_score(y_test_anomalies, hybrid_predictions)
    hybrid_precision = precision_score(
        y_test_anomalies, hybrid_predictions, average="weighted", zero_division=0
    )
    hybrid_recall = recall_score(
        y_test_anomalies, hybrid_predictions, average="weighted", zero_division=0
    )
    hybrid_f1 = f1_score(
        y_test_anomalies, hybrid_predictions, average="weighted", zero_division=0
    )

    print("\nHybrid Classification Results:")
    print("Accuracy:", hybrid_accuracy)
    print("Precision:", hybrid_precision)
    print("Recall:", hybrid_recall)
    print("F1 Score:", hybrid_f1)

    print("\nHybrid Classification Report:")
    print(
        classification_report(
            y_test_anomalies,
            hybrid_predictions,
            labels=np.unique(y_test_anomalies),
            target_names=label_encoder.inverse_transform(np.unique(y_test_anomalies)),
            zero_division=0,
        )
    )

    return {
        "anomalies_detected": int(len(anomaly_indices)),
        "classification_accuracy": hybrid_accuracy,
        "classification_precision": hybrid_precision,
        "classification_recall": hybrid_recall,
        "classification_f1": hybrid_f1,
    }
