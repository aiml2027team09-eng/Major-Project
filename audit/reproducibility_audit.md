# Reproducibility Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Seed stability, software environment, deterministic execution, and artifact provenance  

---

## 1. Random State & Seed Stability

- **Global Seeds**: In `hybrid_ids/config.py`, global seeds are defined:
  ```python
  RANDOM_STATE = 42
  np.random.seed(RANDOM_STATE)
  tf.random.set_seed(RANDOM_STATE)
  ```
- **Omissions & Non-determinism**:
  - `OneHotEncoder` and `StandardScaler` are deterministic, but `SMOTE` relies on `random_state`.
  - TensorFlow GPU operations on Windows/WSL2 can introduce non-deterministic floating-point summation unless `tf.config.experimental.enable_op_determinism()` is explicitly called.
  - Multi-seed validation across standard research seeds (`[42, 123, 456, 789, 1024]`) was never executed as a standard batch. All reported figures represent single-point runs.

---

## 2. Environment & Dependency Audit

- **Operating System**: Windows 11 (AMD64).
- **Python Version**: 3.13.3.
- **Core Frameworks**:
  - TensorFlow: >= 2.13.0
  - XGBoost: >= 2.0.0
  - Scikit-learn: >= 1.3.0
  - SHAP: >= 0.43.0
  - Streamlit: >= 1.28.0
- **Identified Risk**:
  - Native Windows lacks native GPU support for TensorFlow >= 2.11 (runs on CPU fallback).
  - Terminal character encoding defaults to Windows `cp1252`, causing crashes on standard UTF-8 console output.
  - No `system_info.json` or locked dependency manifest existed to lock exact package wheels for artifact reproducibility.

---

## 3. Required Reproducibility Framework

1. Implement `seed.py` that fixes Python, NumPy, TensorFlow, PyTorch (if used), and OS environment variable seeds.
2. Automate multi-seed execution (`42, 123, 456, 789, 1024`) reporting `Mean ± Std` and 95% Confidence Intervals.
3. Automatically log exact system hardware/software specifications in `environment/system_info.json`.
