from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def evaluate_autoencoder(binary_true, anomaly_predictions, split_name):
    """Compute and print autoencoder binary classification metrics."""
    print("\n")
    print("=" * 70)
    print(f"AUTOENCODER {split_name.upper()} RESULTS")
    print("=" * 70)

    accuracy = accuracy_score(binary_true, anomaly_predictions)
    precision = precision_score(binary_true, anomaly_predictions, zero_division=0)
    recall = recall_score(binary_true, anomaly_predictions, zero_division=0)
    f1 = f1_score(binary_true, anomaly_predictions, zero_division=0)

    print("\nAccuracy:", accuracy)
    print("Precision:", precision)
    print("Recall:", recall)
    print("F1 Score:", f1)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
