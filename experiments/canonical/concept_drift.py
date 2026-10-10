"""
experiments/canonical/concept_drift.py
======================================
Concept Drift Monitoring Suite:
1. Kolmogorov-Smirnov Test (D_KS = sup_x |F1(x) - F2(x)|)
2. Population Stability Index (PSI = sum_i (A_i - E_i) * ln(A_i / E_i))
3. Jensen-Shannon Divergence (JSD)
4. Evaluate over temporal windows in CSE-CIC-IDS2018.
5. Save paper/tables/drift_results.csv and paper/figures/drift.png.
"""

from __future__ import annotations

import json
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp
from scipy.spatial.distance import jensenshannon

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between reference and current distribution."""
    # Compute quantiles on expected baseline
    eps = 1e-4
    quantiles = np.linspace(0, 100, num_buckets + 1)
    bins = np.percentile(expected, quantiles)
    bins = np.unique(bins)
    if len(bins) < 2:
        return 0.0
    bins[0] = -np.inf
    bins[-1] = np.inf
    
    e_counts, _ = np.histogram(expected, bins=bins)
    a_counts, _ = np.histogram(actual, bins=bins)
    
    e_pct = (e_counts + eps) / (len(expected) + eps * len(e_counts))
    a_pct = (a_counts + eps) / (len(actual) + eps * len(a_counts))
    
    psi_val = np.sum((a_pct - e_pct) * np.log(a_pct / e_pct))
    return float(psi_val)

def calculate_jsd(p: np.ndarray, q: np.ndarray, num_bins: int = 20) -> float:
    """Calculate Jensen-Shannon Divergence (JSD) between two distributions."""
    min_val = min(np.min(p), np.min(q))
    max_val = max(np.max(p), np.max(q))
    if min_val == max_val:
        return 0.0
    bins = np.linspace(min_val, max_val, num_bins + 1)
    p_hist, _ = np.histogram(p, bins=bins, density=True)
    q_hist, _ = np.histogram(q, bins=bins, density=True)
    
    eps = 1e-6
    p_prob = (p_hist + eps) / np.sum(p_hist + eps)
    q_prob = (q_hist + eps) / np.sum(q_hist + eps)
    
    return float(jensenshannon(p_prob, q_prob))

def run_concept_drift_study() -> dict:
    print("=" * 70)
    print("STEP 16: CONCEPT DRIFT ANALYSIS (KS, PSI, JSD) - CICIDS2018")
    print("=" * 70)
    
    tables_dir = os.path.join(PROJECT_ROOT, "paper", "tables")
    figures_dir = os.path.join(PROJECT_ROOT, "paper", "figures")
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    
    # Load chronological splits or cleaned arrays
    data_dir = os.path.join(PROJECT_ROOT, "data", "cleaned", "cicids2018")
    X_train_normal = np.load(os.path.join(data_dir, "X_train_normal.npy"))
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    
    # Split test set into 5 consecutive temporal windows
    n_test = len(X_test)
    window_size = n_test // 5
    
    # Select key representative features (e.g., Flow Duration, Packet Length Mean, Flow Pkts/s)
    with open(os.path.join(PROJECT_ROOT, "metadata", "cicids2018_features.json"), "r") as f:
        feat_meta = json.load(f)
    features = feat_meta["features"]
    
    key_features = ["Flow Duration", "Flow Packets/s", "Total Length of Fwd Packets", "Fwd Packet Length Mean", "Init_Win_bytes_forward"]
    feat_indices = [features.index(f) for f in key_features if f in features]
    if not feat_indices:
        feat_indices = [0, 1, 2, 3, 4]
        
    print(f"Monitoring drift across 5 consecutive time windows for top features: {[features[i] for i in feat_indices]}...")
    
    drift_records = []
    
    for w in range(5):
        w_start = w * window_size
        w_end = (w + 1) * window_size if w < 4 else n_test
        X_window = X_test[w_start:w_end]
        
        ks_stats = []
        psi_stats = []
        jsd_stats = []
        
        for idx in feat_indices:
            ref_data = X_train_normal[:10000, idx]
            win_data = X_window[:, idx]
            
            # KS Test
            res_ks = ks_2samp(ref_data, win_data)
            ks_stats.append(res_ks.statistic)
            
            # PSI
            psi_val = calculate_psi(ref_data, win_data)
            psi_stats.append(psi_val)
            
            # JSD
            jsd_val = calculate_jsd(ref_data, win_data)
            jsd_stats.append(jsd_val)
            
        avg_ks = float(np.mean(ks_stats))
        avg_psi = float(np.mean(psi_stats))
        avg_jsd = float(np.mean(jsd_stats))
        
        drift_status = "No Drift (PSI < 0.1)" if avg_psi < 0.1 else ("Moderate Drift (0.1 <= PSI < 0.25)" if avg_psi < 0.25 else "Significant Drift (PSI >= 0.25)")
        
        drift_records.append({
            "Window": f"T{w+1}",
            "Window Flows": len(X_window),
            "Mean KS Statistic": avg_ks,
            "Mean PSI": avg_psi,
            "Mean JSD": avg_jsd,
            "Drift Assessment": drift_status,
        })
        print(f"  Window T{w+1}: KS={avg_ks:.4f} | PSI={avg_psi:.4f} | JSD={avg_jsd:.4f} -> {drift_status}")
        
    df_drift = pd.DataFrame(drift_records)
    df_drift.to_csv(os.path.join(tables_dir, "drift_results.csv"), index=False)
    print(f"[OK] Saved drift metrics to paper/tables/drift_results.csv")
    
    # Plot Drift Metric Trajectories
    plt.figure(figsize=(7, 4.8))
    windows = [r["Window"] for r in drift_records]
    psis = [r["Mean PSI"] for r in drift_records]
    kss = [r["Mean KS Statistic"] for r in drift_records]
    jsds = [r["Mean JSD"] for r in drift_records]
    
    plt.plot(windows, psis, marker="o", linewidth=2, color="#d62728", label="Mean PSI")
    plt.plot(windows, kss, marker="s", linewidth=2, color="#1f77b4", label="Mean KS Stat")
    plt.plot(windows, jsds, marker="^", linewidth=2, color="#2ca02c", label="Mean JSD")
    plt.axhline(0.1, color="gray", linestyle="--", alpha=0.7, label="PSI Warning Threshold (0.1)")
    plt.axhline(0.25, color="black", linestyle=":", alpha=0.7, label="PSI Action Threshold (0.25)")
    
    plt.xlabel("Consecutive Temporal Windows", fontsize=11)
    plt.ylabel("Divergence Metric Value", fontsize=11)
    plt.title("Statistical Concept Drift Monitoring Across Time Windows (CICIDS2018)", fontsize=11, pad=12)
    plt.legend(loc="upper left")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "drift.png"), dpi=300)
    plt.close()
    print(f"[OK] Saved drift visualization to paper/figures/drift.png")
    
    return {"drift_records": drift_records}

if __name__ == "__main__":
    run_concept_drift_study()
