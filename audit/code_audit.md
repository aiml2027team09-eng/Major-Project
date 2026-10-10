# Code Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Complete repository source code inspection  

---

## 1. Executive Summary

This audit evaluates the codebase of `hybrid_ids` against peer-reviewed academic standards (IEEE S&P, ACM CCS, USENIX Security, IEEE TIFS). The codebase implements a two-tier intrusion detection framework: a benign-trained Autoencoder (AE) for anomaly detection followed by an XGBoost multi-class classifier for known attack attribution, augmented with SHAP explanations and adaptive thresholding mechanisms.

While the conceptual architecture is well-structured, the implementation exhibits critical methodological issues:
1. **Implicit Data Leakage**: In both `preprocessing.py` and `preprocessing_nsl_kdd.py`, duplicate elimination and preprocessing fitting logic create substantial test-train overlap.
2. **Dual Pipeline Discrepancies**: Discrepancies exist between legacy root-level execution scripts (`hybrid_ids_model.py`, `retrain_from_live.py`) and the modular `run_full_evaluation.py`.
3. **Encoding Issues on Windows**: Hardcoded Unicode characters in CLI outputs crash under standard Windows console code pages (`cp1252`).
4. **Decoupled Experiment State**: Multiple uncoordinated scripts overwrite JSON result summaries in `result_images/` without provenance tracking or experiment IDs.

---

## 2. Component-by-Component Source Code Analysis

### 2.1 Preprocessing Modules (`preprocessing.py` & `preprocessing_nsl_kdd.py`)
- **`preprocessing.py` (CICIDS2018)**:
  - *Data Load*: Chunked loading with downcasting.
  - *Defect*: Global duplicate removal occurs before train/val/test splitting, but because flows with identical numerical features exist across collection sessions, cross-split duplicate leakage is observed (362 identical test samples in training).
  - *SMOTE*: Applied only to `X_train`, which is methodologically correct, but undersampling before SMOTE alters natural base rates.
- **`preprocessing_nsl_kdd.py` (NSL-KDD)**:
  - Uses static `KDDTrain+.txt` and `KDDTest+.txt`.
  - *Defect*: Test set has 38 sample hashes overlapping with training data due to duplicate records inherent to the KDD dataset that were not purged across splits.
  - *Attack Mapping*: Grouped into 5 classes (`normal`, `dos`, `probe`, `r2l`, `u2r`).

### 2.2 Deep Learning & Anomaly Detection (`hybrid_ids/autoencoder.py`, `hybrid_ids/anomaly_detection.py`)
- **Autoencoder Architecture**: Symmetric 7-layer dense autoencoder (`Input -> 128 -> 64 -> 32 -> 16 -> 32 -> 64 -> 128 -> Output`).
- **Optimization**: Adam optimizer, MSE loss, EarlyStopping (`patience=10`), ReduceLROnPlateau.
- **Threshold Determination**:
  - `determine_threshold()` scans percentiles on normal training errors and validation errors.
  - *Defect*: A minimum precision constraint (`MIN_VALIDATION_PRECISION = 0.85` or `0.90`) combined with validation F1 search forces the threshold excessively high on skewed distributions, dropping recall on low-intensity attacks.

### 2.3 Supervised Classification (`hybrid_ids/xgboost_classifier.py`)
- Implements `XGBClassifier` with `n_estimators=500`, `max_depth=6`, `learning_rate=0.03`, `subsample=0.9`, `colsample_bytree=0.8`.
- Evaluates on `(X_validation, y_validation)` with early stopping.
- Correctly isolates training from test, but lacks class weighting (`scale_pos_weight` or custom sample weights) for severely imbalanced classes (e.g. `u2r` in NSL-KDD).

### 2.4 Hybrid Pipeline Integration (`hybrid_ids/hybrid_pipeline.py`)
- Gated logic: Autoencoder threshold determines whether a sample is benign or an anomaly. Anomalous samples are forwarded to XGBoost.
- *Defect in metric calculation*: Hybrid pipeline evaluation is calculated strictly on the detected anomaly subset, rather than reporting both gated end-to-end performance and stage-specific metrics, causing confusion between Stage 2 accuracy and full end-to-end system accuracy.

### 2.5 Explainability (`explainability/shap_analysis.py`)
- Implements TreeExplainer on XGBoost.
- High computational complexity when computing background sets; crashes or times out if test samples exceed 500 without sampling.
- Missing exception handling for missing summary JSONs required by Streamlit dashboard.

### 2.6 Live Monitoring & Flow Tracking (`live_ids/`)
- Scapy packet sniffer aggregates bidirectional flows (`FlowRecord`).
- Handled via `_flush_idle_flows()`.
- Timeout was set to 60s, recently shortened to 5s.
- Interface selection logic was vulnerable to picking virtual adapters with no traffic until recent `resolve_interface_name` patch.

---

## 3. Prioritized Codebase Action Items

1. Establish unified canonical experiment module `experiments/canonical/`.
2. Cleanly isolate preprocessing fits to `X_train` strictly after de-duplicated split generation.
3. Fix string encoding in terminal logs to use ASCII/safe UTF-8 wrappers.
4. Unify artifact outputs under structured experiment registry with metadata hashes.
