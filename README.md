# Adaptive and Explainable Hybrid Network Intrusion Detection System

> **"An Adaptive and Explainable Hybrid Network Intrusion Detection System Using
> Autoencoder-Based Anomaly Detection and XGBoost Classification
> for Real-Time Network Monitoring"**

Final-year major project and research paper implementation.

---

## System Overview

A two-stage hybrid IDS:
1. **Autoencoder** (trained on benign traffic) → anomaly detection via reconstruction error
2. **XGBoost** (trained on labelled traffic) → attack classification (anomalies only)
3. **Adaptive threshold** (μ + kσ, sliding-window) → reduces false positives
4. **SHAP** → explainable per-alert feature attribution

```
Network Flow
    │
    ▼
┌─────────────┐    Reconstruction     ┌───────────────────┐
│ Autoencoder │ ─── Error > T? ──────►│ XGBoost Classifier│
│  (Benign    │     YES ─────────────►│ (Attack Type)     │
│  Traffic)   │     NO: Benign        └───────────────────┘
└─────────────┘                                │
                                        ┌──────▼──────┐
                                        │ SHAP Alert  │
                                        │ Explanation │
                                        └─────────────┘
```

---

## Research Experiments

| Exp | Name | Description |
|-----|------|-------------|
| A | Conventional Split | Standard stratified 70/15/15 split |
| B | Temporal Split | Time-ordered split — tests generalization |
| C | Unseen Attack | Leave-one-class-out — AE detects unseen attacks |
| D | Ablation Study | Models A→G — component contribution |
| E | Baseline Comparison | LR, RF, SVM, MLP, XGB, AE-only, Hybrid |
| F | Drift Detection | KS, PSI, JSD distribution shift monitoring |
| G | Statistical Validation | Multi-seed experiments, 95% CI, t-tests |

---

## Project Structure

```
Major-Project/
├── preprocessing.py              ← CICIDS2018 cleaning + leakage-free split
├── preprocessing_nsl_kdd.py      ← NSL-KDD preprocessing
├── hybrid_ids_model.py           ← Entry point for training
│
├── hybrid_ids/                   ← Core training pipeline
│   ├── main.py                   ← Orchestrates AE + XGBoost training
│   ├── autoencoder.py            ← AE architecture (128→64→32→16)
│   ├── xgboost_classifier.py     ← XGBoost with early stopping
│   ├── anomaly_detection.py      ← Threshold tuning + RE computation
│   ├── hybrid_pipeline.py        ← End-to-end hybrid evaluation
│   └── ...
│
├── models/
│   └── adaptive_threshold.py     ← Fixed, Statistical (μ+kσ), Sliding-window
│
├── evaluation/
│   ├── metrics.py                ← Full metrics: FPR, FNR, ROC-AUC, PR-AUC
│   ├── reconstruction_analysis.py← RE histograms, ROC/PR curves
│   ├── drift_detection.py        ← KS test, PSI, Jensen-Shannon divergence
│   ├── ablation.py               ← Models A→G ablation study
│   ├── baseline_comparison.py    ← LR, RF, SVM, MLP, XGB, AE-only
│   ├── temporal_evaluation.py    ← Temporal split experiment
│   ├── unseen_attack.py          ← Leave-one-class-out experiment
│   ├── statistical_tests.py      ← Multi-seed, t-test, Wilcoxon, bootstrap CI
│   └── leakage_audit.py          ← 7-point leakage prevention audit
│
├── explainability/
│   └── shap_analysis.py          ← Global + local SHAP, stability analysis
│
├── dashboard/
│   ├── app.py                    ← Streamlit dashboard (12 tabs)
│   └── research_pages.py         ← New research evaluation tabs
│
├── live_ids/                     ← Live packet capture (Scapy)
├── configs/
│   └── config.yaml               ← Central reproducibility config
├── run_full_evaluation.py        ← Master evaluation runner
└── requirements.txt
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Preprocess data (CICIDS2018)
```bash
python preprocessing.py
```

### 3. Train the hybrid model
```bash
python hybrid_ids_model.py --dataset cicids2018
```

### 4. Run full research evaluation
```bash
# All experiments (may take 30–60 min)
python run_full_evaluation.py --dataset cicids2018

# Fast mode (skip SHAP and baselines)
python run_full_evaluation.py --dataset cicids2018 --skip-slow
```

### 5. Run data leakage audit
```bash
python -m evaluation.leakage_audit --dataset cicids2018
```

### 6. Launch dashboard
```bash
python run_dashboard.py
# Open: http://localhost:8501
```

### 7. Live monitoring (requires Scapy + admin)
```bash
python live_monitor.py --interface "Wi-Fi" --dataset cicids2018
```

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| 📊 Overview | Alert summary, class distribution, timeline |
| 🚨 Live Alerts | Real-time alert feed with severity |
| 📈 Model Performance | AE + XGBoost metrics, confusion matrix |
| 🎯 Expected Outcomes | Metric targets vs actual |
| 🔄 Retrain Impact | Before/after retrain comparison |
| 🔬 Ablation Study | Models A→G component contribution |
| 💡 SHAP Explainability | Global + local feature importance |
| 📉 Drift Detection | KS, PSI, JSD drift reports |
| 🔍 Unseen Attacks | Leave-one-class-out detection rates |
| 📋 Baselines | LR/RF/SVM/MLP vs Hybrid comparison |
| ⏱️ Temporal Eval | Generalization gap analysis |
| ⚡ Performance | Latency, throughput, CPU/RAM |

---

## Datasets

| Dataset | Classes | Size | Notes |
|---------|---------|------|-------|
| CSE-CIC-IDS2018 | ~15 attack types | ~16M flows | Primary |
| NSL-KDD | 4 attack categories | ~125K records | Secondary/comparison |

---

## Key Research Contributions

1. **Validation-tuned adaptive thresholding** — μ+kσ statistical threshold with grid-search over (k, q) on validation set only
2. **Rigorous leakage prevention** — 7-point audit covering scaler, SMOTE, threshold, label encoder, test contamination, temporal, feature selection
3. **Temporal generalization evaluation** — quantifies the optimistic bias of random splitting
4. **Unseen attack detection** — Autoencoder flags held-out classes as anomalous without supervised labels
5. **SHAP-embedded explanations** — every alert carries a local SHAP explanation (not post-hoc)
6. **Concept drift monitoring** — KS+PSI+JSD consensus before any threshold recalibration
7. **Statistical validation** — multi-seed results with 95% CI, paired t-tests, Wilcoxon tests

---

## Reproducibility

All random seeds, hyperparameters, split ratios, and experiment configurations are in [`configs/config.yaml`](configs/config.yaml).

```bash
# Use a specific random seed
python -c "
import numpy as np, tensorflow as tf
np.random.seed(42)
tf.random.set_seed(42)
"
```

Multi-seed validation:
```bash
python -c "
from evaluation.statistical_tests import run_multiseed_experiment
# See evaluation/statistical_tests.py for usage
"
```

---

## Limitations (Documented)

1. **Random split optimistic bias** → addressed by Experiment B (temporal split)
2. **"Unseen attack detection"** is not zero-day — the AE has not seen specific attack samples but was trained on the same distribution era
3. **CICIDS2018 artifacts** — some known label noise; cleaning documented in `preprocessing.py`
4. **GPU requirement** — model was trained on GPU; CPU inference is ~3-5× slower
5. **Live capture** — requires root/admin and compatible NIC driver for Scapy

---

## Citation / License

This project is a final-year academic project. Results are experimental and should not be used for production security decisions without further validation.
