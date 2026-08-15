# ================================================================
# HYBRID AUTOENCODER + XGBOOST INTRUSION DETECTION SYSTEM
# ================================================================
#
# Stage 1:
#   Autoencoder learns BENIGN network traffic.
#
# Stage 2:
#   Reconstruction error identifies anomalous traffic.
#
# Stage 3:
#   XGBoost classifies anomalous traffic into attack categories.
#
# Dataset:
#   CICIDS2018
#
# Pipeline modules live in the hybrid_ids/ package:
#   config.py              - Paths, hyperparameters, random seed
#   load_data.py           - Load and convert datasets
#   autoencoder.py         - Build, train, save autoencoder
#   anomaly_detection.py   - Reconstruction error and threshold
#   binary_labels.py       - BENIGN vs ATTACK label conversion
#   evaluate_autoencoder.py - Autoencoder metrics
#   xgboost_classifier.py  - Build, train, save XGBoost
#   evaluate_xgboost.py    - XGBoost metrics and confusion matrix
#   hybrid_pipeline.py     - Combined AE + XGBoost evaluation
#   save_results.py        - Persist and print results
#   main.py                - Full pipeline orchestration
#
# ================================================================

from hybrid_ids.main import run_pipeline

if __name__ == "__main__":
    run_pipeline()
