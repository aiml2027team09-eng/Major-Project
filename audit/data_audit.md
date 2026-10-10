# Data Audit Report
**Project:** Hybrid Intrusion Detection System (`hybrid_ids`)  
**Auditor:** Research-Grade NIDS Audit Team  
**Date:** 2026-10-10  
**Scope:** Dataset schemas, volume, label integrity, and feature distributions  

---

## 1. Dataset Profiles Overview

| Dataset Attribute | Primary: CSE-CIC-IDS2018 | Secondary: NSL-KDD |
| :--- | :--- | :--- |
| **Origin / Source** | Canadian Institute for Cybersecurity (UNB) | University of New Brunswick (KDD'99 revision) |
| **Raw Storage** | `cic.csv` (Single file Friday-16-02-2018) | `NSL-KDD/nsl-kdd/KDDTrain+.txt`, `KDDTest+.txt` |
| **Raw Size** | 358.2 MB | Train: 125,973 rows / Test: 22,544 rows |
| **Total Features** | 79 flow features + 1 label | 41 connection features + 1 label + difficulty |
| **Classes Present** | 3 (`Benign`, `FTP-BruteForce`, `SSH-Bruteforce`) | 5 high-level (`normal`, `dos`, `probe`, `r2l`, `u2r`) from 39 raw labels |

---

## 2. Primary Dataset Audit: CSE-CIC-IDS2018

### 2.1 File Scope & Class Distribution
The repository contains a single file representing the brute-force attack day (`Friday-16-02-2018.csv` renamed to `cic.csv`).
- **Raw Class Breakdown**:
  - `Benign`: 667,626 (63.67%)
  - `FTP-BruteForce`: 193,360 (18.44%)
  - `SSH-Bruteforce`: 187,589 (17.89%)
- **Total Samples**: 1,048,575 rows.
- **Scientific Limitation**: The project literature currently refers to evaluating the "CSE-CIC-IDS2018 dataset", but only evaluates 2 attack classes from 1 day. Papers cannot claim full CSE-CIC-IDS2018 benchmark coverage without explicit clarification that only the Brute-Force subset is evaluated.

### 2.2 Numerical Integrity & Cleaning
- **Infinity / Missing Values**: Columns `Flow Byts/s` and `Flow Pkts/s` contain `Infinity` and `NaN` values corresponding to zero-duration microflows.
- **Constant / Invalid Columns**: Several columns exhibit zero variance across the entire session (`Bwd PSH Flags`, `Fwd URG Flags`, `Bwd URG Flags`, `CWE Flag Count`, `Fwd Byts/b Avg`, `Fwd Pkts/b Avg`, `Fwd Blk Rate Avg`, `Bwd Byts/b Avg`, `Bwd Pkts/b Avg`, `Bwd Blk Rate Avg`).

---

## 3. Secondary Dataset Audit: NSL-KDD

### 3.1 Split Composition & Attack Heterogeneity
- **Training File (`KDDTrain+.txt`)**: 125,973 samples, 23 raw attack classes.
- **Test File (`KDDTest+.txt`)**: 22,544 samples, 38 raw attack classes.
- **Distribution Shift & Novel Attacks**:
  - 17 attack classes appear **exclusively** in the test set:
    `{apache2, httptunnel, mailbomb, mscan, named, processtable, ps, saint, sendmail, snmpgetattack, snmpguess, sqlattack, udpstorm, worm, xlock, xsnoop, xterm}`.
  - This design was intentionally constructed by the dataset creators to test generalization, but it causes naive supervised classifiers to suffer sharp performance drops on test splits.

### 3.2 Imbalance Analysis
- In training:
  - `normal`: 67,343
  - `dos`: 45,927
  - `probe`: 11,656
  - `r2l`: 975
  - `u2r`: 72
- Ratio of `normal` to `u2r` is **935:1**. Without proper class weighting or stratified oversampling, `u2r` precision and recall collapse to near 0%.

---

## 4. Live Captured Network Data Audit

- Live files stored in `captured_data/`:
  - `cicids2018/live_flows_raw.csv`: 23 captured flows.
  - `nsl_kdd/live_flows_raw.csv`: 562 captured flows.
- **Audit Findings**:
  - All captured flows are labeled `Benign` / `normal`.
  - Feature distributions between real-time Scapy flows and historical CICFlowMeter/KDD features exhibit noticeable variance in flow duration granularity and header length calculations, driving elevated false alarm rates.
