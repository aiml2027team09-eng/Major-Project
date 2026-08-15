import warnings

from hybrid_ids.anomaly_detection import (
    compute_reconstruction_errors,
    detect_anomalies,
    determine_threshold,
)
from hybrid_ids.autoencoder import (
    build_autoencoder,
    compile_autoencoder,
    plot_autoencoder_loss,
    save_autoencoder,
    train_autoencoder,
)
from hybrid_ids.binary_labels import convert_to_binary_labels, load_label_encoder
from hybrid_ids.evaluate_autoencoder import evaluate_autoencoder
from hybrid_ids.evaluate_xgboost import evaluate_xgboost_split, plot_confusion_matrix
from hybrid_ids.hybrid_pipeline import evaluate_hybrid_pipeline
from hybrid_ids.load_data import convert_to_numpy, load_datasets
from hybrid_ids.save_results import print_final_summary, save_results
from hybrid_ids.xgboost_classifier import (
    create_xgboost_model,
    print_class_mapping,
    save_xgboost_model,
    train_xgboost,
)

warnings.filterwarnings("ignore")


def run_pipeline():
    """Run the full hybrid autoencoder + XGBoost IDS pipeline."""
    # Step 1: Load data
    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
        X_normal,
    ) = load_datasets()

    # Step 2: Convert to numpy
    (
        X_train_np,
        y_train_np,
        X_validation_np,
        y_validation_np,
        X_test_np,
        y_test_np,
        X_normal_np,
    ) = convert_to_numpy(
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
        X_normal,
    )

    # Step 3: Autoencoder — build, compile, train, save, plot
    input_dimension = X_normal_np.shape[1]
    autoencoder = build_autoencoder(input_dimension)
    compile_autoencoder(autoencoder)
    history = train_autoencoder(autoencoder, X_normal_np)
    save_autoencoder(autoencoder)
    plot_autoencoder_loss(history)

    # Step 4: Reconstruction error and anomaly threshold
    normal_errors, validation_errors, test_errors = compute_reconstruction_errors(
        autoencoder, X_normal_np, X_validation_np, X_test_np
    )
    threshold = determine_threshold(normal_errors)

    # Step 5: Anomaly detection on validation and test sets
    validation_anomaly_predictions = detect_anomalies(validation_errors, threshold)
    test_anomaly_predictions = detect_anomalies(test_errors, threshold)

    # Step 6: Binary labels for autoencoder evaluation
    label_encoder = load_label_encoder()
    validation_binary_true = convert_to_binary_labels(y_validation_np, label_encoder)
    test_binary_true = convert_to_binary_labels(y_test_np, label_encoder)

    # Step 7: Evaluate autoencoder
    autoencoder_validation_metrics = evaluate_autoencoder(
        validation_binary_true, validation_anomaly_predictions, "validation"
    )
    autoencoder_test_metrics = evaluate_autoencoder(
        test_binary_true, test_anomaly_predictions, "test"
    )

    # Step 8: XGBoost — create, train, save
    number_of_classes = len(label_encoder.classes_)
    print_class_mapping(label_encoder)
    xgb_model = create_xgboost_model(number_of_classes)
    train_xgboost(
        xgb_model, X_train_np, y_train_np, X_validation_np, y_validation_np
    )
    save_xgboost_model(xgb_model)

    # Step 9: Evaluate XGBoost
    _, xgboost_validation_metrics = evaluate_xgboost_split(
        xgb_model, X_validation_np, y_validation_np, label_encoder, "validation"
    )
    test_xgb_predictions, xgboost_test_metrics = evaluate_xgboost_split(
        xgb_model, X_test_np, y_test_np, label_encoder, "test"
    )
    plot_confusion_matrix(y_test_np, test_xgb_predictions, label_encoder)

    # Step 10: Hybrid pipeline evaluation
    hybrid_metrics = evaluate_hybrid_pipeline(
        xgb_model,
        X_test_np,
        y_test_np,
        test_anomaly_predictions,
        label_encoder,
    )

    # Step 11: Save results and print summary
    save_results(
        threshold,
        autoencoder_validation_metrics,
        autoencoder_test_metrics,
        xgboost_validation_metrics,
        xgboost_test_metrics,
        hybrid_metrics,
    )
    print_final_summary(autoencoder_test_metrics, xgboost_test_metrics)


if __name__ == "__main__":
    run_pipeline()
