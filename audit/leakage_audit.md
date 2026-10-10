# Data Leakage Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Verification of sample isolation, feature extraction, scaling, and threshold boundaries  

---

## 1. Executive Summary: Confirmed Leakage Findings

The repository was subjected to cryptographic hash-based sample intersection tests and code execution pathway inspection. **Severe and confirmed data leakage vectors were detected**, rendering current test metrics scientifically invalid for publication without complete data isolation.

| Leakage Vector | CICIDS2018 Status | NSL-KDD Status | Severity |
| :--- | :--- | :--- | :--- |
| **Test-Train Sample Contamination** | **FAIL** (362 overlapping hashes) | **FAIL** (38 overlapping hashes) | **Critical** |
| **Preprocessing & Scaler Leakage** | **PASS / WARN** (fitted on train split, but duplicates contaminated test) | **PASS** (fitted on train split) | **Medium** |
| **Oversampling (SMOTE) Leakage** | **PASS** (applied strictly to train split) | **PASS** (applied strictly to train split) | **None** |
| **Threshold Selection Leakage** | **WARN** (validation tuned, but manual overrides tested test set) | **WARN** (manual test calibration performed) | **High** |
| **Label Encoding Leakage** | **PASS** | **PASS** | **None** |
| **Temporal Sequence Leakage** | **FAIL** (random shuffling across continuous capture sessions) | **FAIL** (static benchmark without time index) | **High** |

---

## 2. Deep Dive into Contamination Vectors

### 2.1 Test-Train Sample Overlap (Contamination)
- **Empirical Evidence**:
  - In `processed_CICIDS2018`: Comparing row hashes of `X_train_smote.csv` against `X_test.csv` on a 10,000-sample test slice reveals **362 identical feature vectors** present in both splits.
  - In `processed_NSL_KDD`: Comparing row hashes of `X_train_smote.csv` against `X_test.csv` on a 10,000-sample test slice reveals **38 identical feature vectors** present in both splits.
- **Root Cause**:
  1. Network traffic inherently generates repetitive identical flows (e.g. repeated NTP polls, identical TCP handshake resets, repeated periodic probes).
  2. While `df.drop_duplicates()` was executed within chunks or prior to random splitting, samples that are identical in feature space were randomly allocated to *both* the training partition and the testing partition.
  3. Consequently, the supervised models memorized exact flow signatures during training and reproduced them on the test set, inflating accuracy metrics.

### 2.2 Threshold Tuning Leakage
- **Mechanism**: In `hybrid_ids/anomaly_detection.py`, the threshold $\tau$ was designed to be tuned on `X_validation`. However, in recent tuning operations, test error distributions were directly queried in scratch evaluation to set thresholds maximizing test F1/accuracy.
- **Academic Requirement**: The threshold selection algorithm must strictly and exclusively operate on `X_validation_normal` (or `X_val_all`) with zero exposure to `X_test`.

### 2.3 Temporal Sequence Leakage
- **Mechanism**: In `preprocessing.py`, the CICIDS2018 dataset is partitioned using `train_test_split(..., shuffle=True, random_state=42)`.
- **Flaw**: Because network traffic is a non-stationary time series, random shuffling mixes packets from minute $t$ into training and packets from minute $t-1$ into testing. This creates unrealistic temporal leakage where the model uses "future" session contexts to classify "past" session flows.

---

## 3. Mandatory Elimination Protocol

To achieve a 100% clean, journal-grade pipeline:
1. **Global Deduplication & Unique ID Stamping**:
   - Assign immutable `sample_id` and SHA-256 row hash to every raw record.
   - Remove all exact feature duplicates globally *before* splitting.
2. **Strict Disjoint Partitioning**:
   - Partition into Train (70%), Validation (15%), Test (15%) such that:
     $$\text{Train} \cap \text{Validation} = \emptyset, \quad \text{Train} \cap \text{Test} = \emptyset, \quad \text{Validation} \cap \text{Test} = \emptyset$$
3. **Strict Directional Pipeline Fitting**:
   - `preprocessor.fit(X_train)`
   - `X_val_processed = preprocessor.transform(X_val)`
   - `X_test_processed = preprocessor.transform(X_test)`
4. **Automated Zero-Tolerance Assertion**:
   - Implement an automated hash-intersection verification step in `evaluation/leakage_audit.py` that halts pipeline execution immediately if any overlap is discovered.
