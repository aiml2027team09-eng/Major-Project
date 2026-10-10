# Research Gap Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Academic positioning, contribution validity, literature alignment, and publication readiness  

---

## 1. Critique of Existing Research Claims

In existing project documentation and comments, several claims were made that would not withstand rigorous peer review in top-tier venues (ACM CCS, IEEE S&P, USENIX Security, IEEE TIFS):

| Vulnerable Existing Claim | Academic Criticism | Required Rigorous Positioning |
| :--- | :--- | :--- |
| *"Novel Autoencoder + XGBoost Intrusion Detection System"* | Autoencoder + XGBoost ensembles are widely documented in literature since 2018–2020. Ensembling them is not an architectural breakthrough. | Frame novelty around **the deployment-oriented integration**: benign manifold reconstruction, adaptive thresholding under concept drift, temporal generalization audit, and operational SHAP explainability. |
| *"Zero-day attack detection capabilities"* | Testing on an arbitrary test partition that contains unseen attacks without a formal Leave-One-Attack-Out cross-validation protocol does not substantiate "zero-day" claims. | Re-term strictly as **Unseen-Attack Generalization** evaluated via rigorous leave-one-class-out protocol. |
| *"Real-time intrusion detection"* | No formal packet queue latency, packet drop rates, or line-rate benchmarks were reported. | Frame as **Evaluated under live flow monitoring conditions with measured inference latency (ms/flow) and throughput (flows/s)**. |
| *"Evaluated on the full CSE-CIC-IDS2018 benchmark"* | Only a single CSV file (`Friday-16-02-2018.csv` with 2 brute-force classes) is in the workspace. | Explicitly define the dataset scope as the **CSE-CIC-IDS2018 Brute-Force attack subset**, clarifying exact class support. |

---

## 2. Research Questions (RQs) and Hypotheses (H)

To elevate the work to journal quality, the experimental framework must directly test and answer the following formal research questions:

- **RQ1**: Does the two-stage hybrid AE + XGBoost pipeline outperform standalone supervised and unsupervised baselines in Macro-F1 and False Positive Rate on identical splits?
- **RQ2**: Does validation-tuned adaptive thresholding improve the trade-off between false alarm rate and recall compared with static percentile thresholds under non-stationary traffic?
- **RQ3**: How much does detection performance degrade when transitioning from random stratified splitting to realistic temporal chronological evaluation?
- **RQ4**: Can the benign-trained Autoencoder reliably detect attack categories that were strictly excluded from supervised classifier training?
- **RQ5**: Does SHAP attribution provide stable, reproducible feature-attribution explanations across samples of the same attack family?
- **RQ6**: What is the measured computational overhead (latency, throughput, memory) of incorporating local SHAP explanations into live alert generation?
- **RQ7**: What causes the live domain-transfer false positive rate penalty when deploying benchmark-trained NIDS models to real network traffic?

---

## 3. Contribution Matrix

| Limitation in Literature | Proposed Methodological Solution | Empirical Validation Protocol |
| :--- | :--- | :--- |
| **Pervasive Data Leakage** | Complete pre-split duplicate removal, isolated scaler fitting, and SHA-256 hash assertions | `evaluation/leakage_audit.py` with zero cross-split overlap |
| **Overfitting via Random Splits** | Temporal Chronological train/validation/test splitting | Chronological split vs Random split degradation measurement |
| **Static Threshold Rigidity** | Multi-metric validation threshold search & sliding window adaptivity | Precision-constrained threshold vs percentile baseline |
| **Black-box Supervised Output** | Local TreeSHAP attribution attached to every generated alert | Top-5 feature attribution and Jaccard explanation stability |
| **Unsubstantiated Operational Claims** | Physical flow-rate benchmarking and latency profiling | Microsecond timing per flow across AE, XGBoost, and SHAP |
