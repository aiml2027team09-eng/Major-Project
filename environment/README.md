# Experimental Environment & Reproducibility Guide

## Hardware & Operating System Specifications
- **Operating System**: Windows 11 (build 10.0.26300)
- **Processor Architecture**: AMD64 Family 25 Model 80 Stepping 0 (AuthenticAMD, Multi-Core)
- **Memory**: 16 GB+ RAM
- **Execution Mode**: Native CPU (TensorFlow oneDNN custom operations enabled)

## Python Runtime & Key Dependencies
- **Python**: 3.13.3 (64-bit)
- **TensorFlow**: 2.21.0
- **XGBoost**: 3.4.0
- **Scikit-Learn**: 1.6.1
- **SHAP**: 0.52.0
- **NumPy**: 2.2.6
- **Pandas**: 2.2.3

## Reproduction Steps
To reproduce all paper tables and figures from scratch:

1. Install dependencies:
   ```bash
   pip install -r environment/requirements.txt
   ```
2. Split datasets with strict deduplication:
   ```bash
   python experiments/canonical/dataset.py
   ```
3. Generate class distribution tables and figures:
   ```bash
   python evaluation/class_distribution.py
   ```
4. Fit preprocessing strictly on train splits:
   ```bash
   python experiments/canonical/preprocessing.py
   ```
5. Train canonical models:
   ```bash
   python experiments/canonical/train.py
   ```
6. Run canonical evaluation harness:
   ```bash
   python experiments/canonical/evaluate.py
   ```
7. Execute all research experiments:
   ```bash
   python experiments/canonical/adaptive_threshold.py
   python experiments/canonical/ablation.py
   python experiments/canonical/temporal_evaluation.py
   python experiments/canonical/unseen_attacks.py
   python experiments/canonical/concept_drift.py
   python experiments/canonical/shap_analysis.py
   python live_monitoring/feature_validator.py
   python evaluation/operational_performance.py
   python evaluation/statistical_validation.py
   ```
8. Verify scientific rigor:
   ```bash
   python evaluation/research_quality_check.py
   ```
