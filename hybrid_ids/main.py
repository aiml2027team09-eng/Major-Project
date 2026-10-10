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
from hybrid_ids.device_config import setup_training_devices
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
    setup_training_devices()

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

    # Step 4: Reconstruction error and tuned anomaly threshold
    normal_errors, validation_errors, test_errors = compute_reconstruction_errors(
        autoencoder, X_normal_np, X_validation_np, X_test_np
    )

    label_encoder = load_label_encoder()
    validation_binary_true = convert_to_binary_labels(y_validation_np, label_encoder)
    test_binary_true = convert_to_binary_labels(y_test_np, label_encoder)

    threshold = determine_threshold(
        normal_errors,
        validation_errors=validation_errors,
        validation_binary_true=validation_binary_true,
    )

    # Step 4b: Adaptive threshold comparison (new)
    _run_adaptive_threshold_analysis(
        normal_errors, validation_errors, test_errors,
        validation_binary_true, test_binary_true,
    )

    # Step 5: Anomaly detection on validation and test sets
    validation_anomaly_predictions = detect_anomalies(validation_errors, threshold)
    test_anomaly_predictions = detect_anomalies(test_errors, threshold)

    # Step 6: Evaluate autoencoder (with enhanced metrics)
    autoencoder_validation_metrics = evaluate_autoencoder(
        validation_binary_true, validation_anomaly_predictions, "validation"
    )
    autoencoder_test_metrics = evaluate_autoencoder(
        test_binary_true, test_anomaly_predictions, "test"
    )

    # Step 6b: Enhanced binary metrics with FPR/FNR/ROC-AUC
    _print_enhanced_ae_metrics(test_binary_true, test_errors, threshold)

    # Step 7: XGBoost — create, train, save
    number_of_classes = len(label_encoder.classes_)
    print_class_mapping(label_encoder)
    xgb_model = create_xgboost_model(number_of_classes)
    train_xgboost(
        xgb_model, X_train_np, y_train_np, X_validation_np, y_validation_np
    )
    save_xgboost_model(xgb_model)

    # Step 8: Evaluate XGBoost
    _, xgboost_validation_metrics = evaluate_xgboost_split(
        xgb_model, X_validation_np, y_validation_np, label_encoder, "validation"
    )
    test_xgb_predictions, xgboost_test_metrics = evaluate_xgboost_split(
        xgb_model, X_test_np, y_test_np, label_encoder, "test"
    )
    plot_confusion_matrix(y_test_np, test_xgb_predictions, label_encoder)

    # Step 8b: Enhanced multi-class metrics (macro-F1, ROC-AUC OvR)
    _print_enhanced_xgb_metrics(
        y_test_np, test_xgb_predictions,
        xgb_model.predict_proba(X_test_np),
        list(label_encoder.classes_),
    )

    # Step 9: Hybrid pipeline evaluation
    hybrid_metrics = evaluate_hybrid_pipeline(
        xgb_model,
        X_test_np,
        y_test_np,
        test_anomaly_predictions,
        label_encoder,
    )

    # Step 10: Save results and print summary
    save_results(
        threshold,
        autoencoder_validation_metrics,
        autoencoder_test_metrics,
        xgboost_validation_metrics,
        xgboost_test_metrics,
        hybrid_metrics,
    )
    print_final_summary(autoencoder_test_metrics, xgboost_test_metrics)

    # Step 11: Reconstruction error analysis plots
    _run_reconstruction_analysis(
        autoencoder, X_normal_np, X_test_np, y_test_np,
        label_encoder, threshold,
    )

    # Step 12: Data leakage audit
    _run_leakage_audit()

    print("\n")
    print("=" * 70)
    print("TRAINING COMPLETE")
    print("Run full evaluation with:")
    print("  python run_full_evaluation.py --dataset cicids2018")
    print("  python run_full_evaluation.py --dataset cicids2018 --skip-slow")
    print("=" * 70)


# ─────────────────────────────────────────────
#  Enhancement helpers (non-breaking additions)
# ─────────────────────────────────────────────

def _run_adaptive_threshold_analysis(
    normal_errors, val_errors, test_errors,
    val_binary, test_binary,
):
    """Run adaptive threshold comparison and print results."""
    try:
        from models.adaptive_threshold import compare_all_thresholds
        import hybrid_ids.config as config
        import os

        print("\n" + "=" * 70)
        print("ADAPTIVE THRESHOLD ANALYSIS")
        print("=" * 70)

        compare_all_thresholds(
            normal_errors, test_errors, test_binary,
            output_dir=os.path.join(config.MODEL_FOLDER, "threshold_analysis"),
        )
    except Exception as e:
        print(f"  [Adaptive threshold] Skipped: {e}")


def _print_enhanced_ae_metrics(y_binary, errors, threshold):
    """Print FPR, FNR, and ROC-AUC for the autoencoder."""
    try:
        from evaluation.metrics import compute_binary_metrics, compute_roc_auc
        import numpy as np

        preds = (errors > threshold).astype(int)
        m     = compute_binary_metrics(y_binary, preds)
        roc   = compute_roc_auc(y_binary, errors)

        print("\n=== Autoencoder Enhanced Metrics (Test Set) ===")
        print(f"  Accuracy : {m['accuracy']:.4f}")
        print(f"  Precision: {m['precision']:.4f}")
        print(f"  Recall   : {m['recall']:.4f}")
        print(f"  F1       : {m['f1']:.4f}")
        print(f"  FPR      : {m['fpr']:.4f}  (false alarm rate)")
        print(f"  FNR      : {m['fnr']:.4f}  (missed attack rate)")
        print(f"  ROC-AUC  : {roc['roc_auc']:.4f}")
        print(f"  PR-AUC   : {roc['pr_auc']:.4f}")
        print(f"  TP={m['tp']}  FP={m['fp']}  TN={m['tn']}  FN={m['fn']}")
    except Exception as e:
        print(f"  [Enhanced AE metrics] Skipped: {e}")


def _print_enhanced_xgb_metrics(y_true, y_pred, y_prob, class_names):
    """Print macro-F1 and ROC-AUC OvR for XGBoost."""
    try:
        from evaluation.metrics import compute_multiclass_metrics

        m = compute_multiclass_metrics(y_true, y_pred, class_names, y_prob)

        print("\n=== XGBoost Enhanced Metrics (Test Set) ===")
        print(f"  Accuracy            : {m['accuracy']:.4f}")
        print(f"  F1 (weighted)       : {m['f1_weighted']:.4f}")
        print(f"  F1 (macro)          : {m['f1_macro']:.4f}")
        print(f"  Precision (weighted): {m['precision_weighted']:.4f}")
        print(f"  Recall (weighted)   : {m['recall_weighted']:.4f}")
        if m.get("roc_auc_ovr") is not None:
            print(f"  ROC-AUC (OvR macro) : {m['roc_auc_ovr']:.4f}")
    except Exception as e:
        print(f"  [Enhanced XGB metrics] Skipped: {e}")


def _run_reconstruction_analysis(autoencoder, X_normal, X_test, y_test,
                                  label_encoder, threshold):
    """Generate reconstruction error plots."""
    try:
        from evaluation.reconstruction_analysis import (
            compute_errors,
            plot_error_distributions,
            plot_roc_curve,
            plot_pr_curve,
        )
        from hybrid_ids.binary_labels import convert_to_binary_labels
        import hybrid_ids.config as config
        import os

        out_dir = os.path.join(config.MODEL_FOLDER, "reconstruction")
        os.makedirs(out_dir, exist_ok=True)

        normal_errors = compute_errors(autoencoder, X_normal)
        test_errors   = compute_errors(autoencoder, X_test)
        y_binary      = convert_to_binary_labels(y_test, label_encoder)

        plot_error_distributions(
            {"Benign (normal train)": normal_errors, "Test (all)": test_errors},
            threshold,
            os.path.join(out_dir, "error_distribution.png"),
        )
        plot_roc_curve(
            y_binary, test_errors, threshold,
            os.path.join(out_dir, "roc_curve.png"),
        )
        plot_pr_curve(
            y_binary, test_errors,
            os.path.join(out_dir, "pr_curve.png"),
        )

        print(f"  Reconstruction plots saved → {out_dir}")
    except Exception as e:
        print(f"  [Reconstruction analysis] Skipped: {e}")


def _run_leakage_audit():
    """Run data leakage audit after training."""
    try:
        from evaluation.leakage_audit import run_full_leakage_audit
        import hybrid_ids.config as config
        import os

        run_full_leakage_audit(
            data_folder=config.DATA_FOLDER,
            model_folder=config.MODEL_FOLDER,
            output_path=os.path.join(config.MODEL_FOLDER, "leakage_audit.json"),
        )
    except Exception as e:
        print(f"  [Leakage audit] Skipped: {e}")


if __name__ == "__main__":
    run_pipeline()
