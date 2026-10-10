# Experiment Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Evaluation methodologies, baseline rigor, ablation integrity, and experimental scripts  

---

## 1. Existing Evaluation Scripts & Pipelines

The project contains several evaluation entry points:
1. `hybrid_ids_model.py`: Legacy training script covering Autoencoder + XGBoost.
2. `run_full_evaluation.py`: Monolithic 10-step evaluation orchestrator covering baselines, ablation, SHAP, drift, and latency.
3. `validate_model.py`: Offline evaluation script generating binary confusion matrices and test metrics.
4. `generate_result_images.py`: Image and metrics regeneration script.
5. `evaluation/*.py`: Sub-modules for ablation, drift, baselines, unseen attack, temporal, and metrics.

---

## 2. Experimental Rigor Deficiencies

### 2.1 Conflicting Metric Artifacts
- `result_images/nsl_kdd/metrics_summary.json` reports:
  - Hybrid Test Accuracy: **69.84%**
  - Overall Test Accuracy: **75.56%**
- Meanwhile, earlier terminal logs and historical summaries recorded:
  - Hybrid Accuracy: **71.48%**
  - Overall Accuracy: **73.77%**
- Root Cause: Multiple scripts independently calculate and overwrite metric summaries with differing thresholds and differing anomaly subsets without semantic versioning or experiment tracking IDs.

### 2.2 Baseline Implementation Inconsistencies
- `evaluation/baseline_comparison.py` trains Logistic Regression, Random Forest, LinearSVC, MLP, Standalone XGBoost, Standalone Autoencoder, and AE + XGBoost.
- However, baseline comparisons were frequently skipped using `--skip-slow`.
- Classifiers did not systematically enforce uniform hyperparameter search or cross-validation on identical data partitions.

### 2.3 Ablation Study Evaluation
- `evaluation/ablation.py` defines 7 model variants (A1 through A7).
- In actual execution, Variant F (with SHAP) and Variant G (Full system with drift and temporal) were evaluated sequentially rather than under rigorous, controlled computational resource tracking.

### 2.4 Unseen Attack Evaluation
- `evaluation/unseen_attack.py` implemented a leave-one-class-out test for Autoencoders.
- Defect: Rather than implementing a full Leave-One-Attack-Out cross-validation loop across every eligible attack category, it was only executed as a single-run test on arbitrary classes without recording multi-seed confidence intervals.

---

## 3. Required Standardized Experiment Framework

All experimental runs must be unified under a single canonical harness:
```text
experiments/canonical/
├── run_all.py
├── config.yaml
├── seed.py
├── dataset.py
├── preprocessing.py
├── train.py
├── evaluate.py
└── save_results.py
```
Old conflicting runs must be isolated to `results/archived/DO_NOT_USE_FOR_PAPER`.
