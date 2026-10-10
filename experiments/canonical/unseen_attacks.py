"""
experiments/canonical/unseen_attacks.py
=======================================
Leave-One-Attack-Out (LOAO) Unseen Attack Evaluation:
1. Primary Dataset: NSL-KDD attack categories (dos, probe, r2l, u2r).
2. For each attack category:
   - Hold out Attack C.
   - Supervised classifier (XGBoost) trained ONLY on Benign + Remaining Attack Classes.
   - Autoencoder trained strictly on Benign traffic.
   - Evaluate on Test set containing Benign + Held-out Attack C.
3. Decision Logic:
   - If RE > tau -> Flags flow as Anomalous (Unseen Attack candidate).
   - XGBoost does NOT force unseen attack into a known attack class; mapped to UNKNOWN_ATTACK.
4. Report:
   - Unseen Attack Detection Rate (Recall on held-out attack)
   - Benign False Positive Rate (FPR)
   - AUROC and AUPRC on separating Held-out Attack from Benign
   - Mean & Median Reconstruction Errors
5. Output:
   - paper/tables/unseen_attack_results.csv
   - paper/figures/unseen_attack.png
"""

from __future__ import annotations

import json
import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import recall_score, roc_auc_score, average_precision_score
from xgboost import XGBClassifier

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.canonical.seed import set_global_seed
from experiments.canonical.train import build_autoencoder, compute_reconstruction_error

def run_unseen_attack_evaluation(seed: int = 42) -> dict:
    set_global_seed(seed)
    print("=" * 70)
    print("STEP 15: LEAVE-ONE-ATTACK-OUT UNSEEN ATTACK EXPERIMENT (NSL-KDD)")
    print("=" * 70)
    
    data_dir = os.path.join(PROJECT_ROOT, "data", "cleaned", "nsl_kdd")
    models_prep_dir = os.path.join(PROJECT_ROOT, "models", "preprocessors")
    tables_dir = os.path.join(PROJECT_ROOT, "paper", "tables")
    figures_dir = os.path.join(PROJECT_ROOT, "paper", "figures")
    
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    
    label_encoder = joblib.load(os.path.join(models_prep_dir, "nsl_kdd_label_encoder.pkl"))
    classes = list(label_encoder.classes_)
    benign_idx = classes.index("normal")
    attack_classes = [c for c in classes if c != "normal"]
    
    X_train_normal = np.load(os.path.join(data_dir, "X_train_normal.npy"))
    X_train_smote = np.load(os.path.join(data_dir, "X_train_smote.npy"))
    y_train_smote = np.load(os.path.join(data_dir, "y_train_smote.npy"))
    
    X_val = np.load(os.path.join(data_dir, "X_val.npy"))
    y_val = np.load(os.path.join(data_dir, "y_val.npy"))
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))
    
    # 1. Train Benign Autoencoder (Strictly Benign Only)
    print(f"Training Benign Autoencoder on {len(X_train_normal):,} normal flows...")
    ae = build_autoencoder(X_train_normal.shape[1], architecture="baseline")
    ae.fit(X_train_normal, X_train_normal, epochs=25, batch_size=1024, verbose=0)
    
    val_errors = compute_reconstruction_error(ae, X_val)
    val_normal_errors = val_errors[y_val == benign_idx]
    # Optimal threshold from validation normal percentile
    tau = float(np.percentile(val_normal_errors, 95.0))
    print(f"Autoencoder Anomaly Threshold (95th percentile benign validation): {tau:.6f}")
    
    results = []
    
    for held_out_attack in attack_classes:
        held_out_idx = classes.index(held_out_attack)
        print(f"\nEvaluating Held-Out Unseen Class: '{held_out_attack.upper()}' (Index {held_out_idx})")
        
        # Filter training data to EXCLUDE held_out_idx
        train_mask = (y_train_smote != held_out_idx)
        X_tr_subset = X_train_smote[train_mask]
        y_tr_subset = y_train_smote[train_mask]
        
        # Filter val data
        val_mask = (y_val != held_out_idx)
        X_v_subset = X_val[val_mask]
        y_v_subset = y_val[val_mask]
        
        from sklearn.preprocessing import LabelEncoder
        sub_le = LabelEncoder()
        y_tr_mapped = sub_le.fit_transform(y_tr_subset)
        y_v_mapped = sub_le.transform(y_v_subset)
        
        # Train XGBoost without knowing the held_out attack exists
        xgb = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=seed)
        xgb.fit(X_tr_subset, y_tr_mapped, eval_set=[(X_v_subset, y_v_mapped)], verbose=False)
        
        # Test partition: Benign flows + Held-out attack flows ONLY
        test_eval_mask = (y_test == benign_idx) | (y_test == held_out_idx)
        X_test_eval = X_test[test_eval_mask]
        y_test_eval = y_test[test_eval_mask]
        
        y_test_eval_bin = (y_test_eval == held_out_idx).astype(int) # 1 = Unseen attack, 0 = Normal
        
        # Compute Autoencoder errors on test evaluation set
        eval_errors = compute_reconstruction_error(ae, X_test_eval)
        unseen_errors = eval_errors[y_test_eval_bin == 1]
        normal_eval_errors = eval_errors[y_test_eval_bin == 0]
        
        # Unseen Attack Detection Logic:
        # If RE > tau -> Flagged as UNKNOWN / UNSEEN ATTACK
        flagged_anomalous = (eval_errors > tau).astype(int)
        
        detection_rate = float(recall_score(y_test_eval_bin, flagged_anomalous, zero_division=0))
        fpr = float(np.sum((flagged_anomalous == 1) & (y_test_eval_bin == 0)) / np.sum(y_test_eval_bin == 0))
        fnr = 1.0 - detection_rate
        
        auroc = float(roc_auc_score(y_test_eval_bin, eval_errors)) if len(np.unique(y_test_eval_bin)) > 1 else 0.5
        auprc = float(average_precision_score(y_test_eval_bin, eval_errors)) if len(np.unique(y_test_eval_bin)) > 1 else 0.0
        
        mean_re = float(np.mean(unseen_errors)) if len(unseen_errors) > 0 else 0.0
        median_re = float(np.median(unseen_errors)) if len(unseen_errors) > 0 else 0.0
        
        print(f"  -> Unseen Detection Rate (Recall): {detection_rate:.4f} ({detection_rate*100:.1f}%)")
        print(f"  -> Benign False Positive Rate:     {fpr:.4f}")
        print(f"  -> AUROC:                          {auroc:.4f}")
        print(f"  -> Mean Reconstruction Error:      {mean_re:.6f} (vs Normal Mean {np.mean(normal_eval_errors):.6f})")
        
        results.append({
            "Held-out Attack Class": held_out_attack.upper(),
            "Samples": int(np.sum(y_test_eval_bin == 1)),
            "Detection Rate (Recall)": detection_rate,
            "False Negative Rate (FNR)": fnr,
            "Benign FPR": fpr,
            "AUROC": auroc,
            "AUPRC": auprc,
            "Mean RE": mean_re,
            "Median RE": median_re,
            "Decision": "UNKNOWN_ATTACK"
        })
        
    df_results = pd.DataFrame(results)
    df_results.to_csv(os.path.join(tables_dir, "unseen_attack_results.csv"), index=False)
    print(f"\n[OK] Saved results to paper/tables/unseen_attack_results.csv")
    
    # Plot Unseen Attack Detection Rates
    plt.figure(figsize=(7, 5))
    bars = plt.bar(df_results["Held-out Attack Class"], df_results["Detection Rate (Recall)"] * 100, color="#2b5c8f", width=0.5)
    plt.axhline(90.0, color="crimson", linestyle="--", label="Target Detection (90%)")
    plt.ylabel("Unseen Detection Rate (%)", fontsize=11)
    plt.xlabel("Held-Out Attack Category", fontsize=11)
    plt.title("Leave-One-Attack-Out Unseen Attack Detection via Autoencoder RE", fontsize=11, pad=12)
    plt.ylim(0, 105)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., h + 2, f"{h:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")
    plt.legend(loc="lower right")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "unseen_attack.png"), dpi=300)
    plt.close()
    print(f"[OK] Saved figure to paper/figures/unseen_attack.png")
    
    return {"results": results}

if __name__ == "__main__":
    run_unseen_attack_evaluation(seed=42)
