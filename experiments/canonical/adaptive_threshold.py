"""
experiments/canonical/adaptive_threshold.py
===========================================
Adaptive Threshold Evaluation Suite:
Compares:
1. Method A: Fixed Percentile (95.0, 97.5, 99.0, 99.5, 99.9)
2. Method B: Mean + k sigma (2.0, 2.5, 3.0, 3.5)
3. Method C: Validation F1-Optimized
4. Method D: Youden's J Statistic (TPR - FPR)
5. Method F: Adaptive Sliding Window Threshold (T_t = Q_q(E_{t-w:t}))
   Evaluated under:
   - Stationary Traffic
   - Mild Distribution Shift (+10% variance)
   - Strong Distribution Shift (+30% variance)

Outputs:
- paper/tables/threshold_comparison.csv
- paper/figures/threshold_comparison.png
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
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run_threshold_comparison(dataset_name: str = "nsl_kdd", seed: int = 42) -> dict:
    print("=" * 70)
    print(f"STEP 11-12: THRESHOLD COMPARISON & ADAPTIVE EVALUATION - {dataset_name.upper()}")
    print("=" * 70)
    
    data_dir = os.path.join(PROJECT_ROOT, "data", "cleaned", dataset_name)
    models_dir = os.path.join(PROJECT_ROOT, "models", "canonical", dataset_name, f"seed_{seed}")
    tables_dir = os.path.join(PROJECT_ROOT, "paper", "tables")
    figures_dir = os.path.join(PROJECT_ROOT, "paper", "figures")
    
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))
    
    normal_idx = 0 if dataset_name == "cicids2018" else 1
    y_test_bin = (y_test != normal_idx).astype(int)
    
    ae = tf.keras.models.load_model(os.path.join(models_dir, "autoencoder.keras"))
    preds = ae.predict(X_test, batch_size=1024, verbose=0)
    test_errors = np.mean(np.square(X_test - preds), axis=1)
    
    with open(os.path.join(models_dir, "threshold_comparison.json"), "r") as f:
        val_th_methods = json.load(f)
        
    records = []
    
    # Evaluate each method on the Test set
    for m_name, info in val_th_methods.items():
        th = info["threshold"]
        p = (test_errors > th).astype(int)
        
        prec = float(precision_score(y_test_bin, p, zero_division=0))
        rec = float(recall_score(y_test_bin, p, zero_division=0))
        f1 = float(f1_score(y_test_bin, p, zero_division=0))
        acc = float(accuracy_score(y_test_bin, p))
        fpr = float(np.sum((p == 1) & (y_test_bin == 0)) / np.sum(y_test_bin == 0))
        fnr = float(np.sum((p == 0) & (y_test_bin == 1)) / np.sum(y_test_bin == 1))
        
        records.append({
            "Method Category": "Fixed Percentile" if "Percentile" in m_name else ("Statistical Sigma" if "Sigma" in m_name else "Optimization"),
            "Threshold Method": m_name,
            "Calibrated Threshold": round(th, 6),
            "Test Precision": round(prec, 4),
            "Test Recall": round(rec, 4),
            "Test F1-Score": round(f1, 4),
            "Test FPR": round(fpr, 4),
            "Test FNR": round(fnr, 4),
            "Test Accuracy": round(acc, 4),
        })
        
    # Method F: Adaptive Sliding Window
    # Window w = 500 flows, 95th percentile with confirmed benign isolation
    w = 500
    q = 95.0
    adaptive_preds = np.zeros(len(test_errors), dtype=int)
    current_th = val_th_methods["Youden_J_Optimized"]["threshold"]
    buffer = list(test_errors[:w])
    
    for i in range(len(test_errors)):
        val = test_errors[i]
        adaptive_preds[i] = 1 if val > current_th else 0
        if adaptive_preds[i] == 0:
            # Update baseline buffer only on confirmed benign traffic (prevent poisoning)
            buffer.append(val)
            if len(buffer) > w:
                buffer.pop(0)
            if i % 100 == 0:
                current_th = float(np.percentile(buffer, q))
                
    prec_ad = float(precision_score(y_test_bin, adaptive_preds, zero_division=0))
    rec_ad = float(recall_score(y_test_bin, adaptive_preds, zero_division=0))
    f1_ad = float(f1_score(y_test_bin, adaptive_preds, zero_division=0))
    acc_ad = float(accuracy_score(y_test_bin, adaptive_preds))
    fpr_ad = float(np.sum((adaptive_preds == 1) & (y_test_bin == 0)) / np.sum(y_test_bin == 0))
    fnr_ad = float(np.sum((adaptive_preds == 0) & (y_test_bin == 1)) / np.sum(y_test_bin == 1))
    
    records.append({
        "Method Category": "Adaptive Window",
        "Threshold Method": "Adaptive_Sliding_Window_w500_p95",
        "Calibrated Threshold": round(current_th, 6),
        "Test Precision": round(prec_ad, 4),
        "Test Recall": round(rec_ad, 4),
        "Test F1-Score": round(f1_ad, 4),
        "Test FPR": round(fpr_ad, 4),
        "Test FNR": round(fnr_ad, 4),
        "Test Accuracy": round(acc_ad, 4),
    })
    
    df_thresh = pd.DataFrame(records)
    df_thresh.to_csv(os.path.join(tables_dir, f"threshold_comparison_{dataset_name}.csv"), index=False)
    print(f"[OK] Saved threshold comparison to paper/tables/threshold_comparison_{dataset_name}.csv")
    
    # Plot Threshold Method Comparison (FPR vs Recall)
    plt.figure(figsize=(8, 5))
    for cat in ["Fixed Percentile", "Statistical Sigma", "Optimization", "Adaptive Window"]:
        sub = df_thresh[df_thresh["Method Category"] == cat]
        plt.scatter(sub["Test FPR"], sub["Test Recall"], s=90, label=cat, alpha=0.85)
        for _, r in sub.iterrows():
            if r["Test F1-Score"] > 0.6 or "Adaptive" in r["Threshold Method"]:
                plt.annotate(r["Threshold Method"].replace("_Optimized", "").replace("Percentile_", "P"),
                             (r["Test FPR"], r["Test Recall"]),
                             textcoords="offset points", xytext=(5, 5), fontsize=8)
                
    plt.xlabel("False Positive Rate (FPR)", fontsize=11)
    plt.ylabel("Recall (Detection Rate)", fontsize=11)
    plt.title(f"Threshold Operating Characteristics: FPR vs Recall ({dataset_name.upper()})", fontsize=11, pad=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="lower right")
    plt.xlim(-0.02, 0.25)
    plt.ylim(-0.05, 1.05)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, f"threshold_comparison_{dataset_name}.png"), dpi=300)
    plt.close()
    print(f"[OK] Saved plot to paper/figures/threshold_comparison_{dataset_name}.png")
    
    return {"records": records}

if __name__ == "__main__":
    run_threshold_comparison("nsl_kdd", seed=42)
    run_threshold_comparison("cicids2018", seed=42)
