"""
experiments/canonical/evaluate.py
=================================
Canonical Evaluation Suite:
1. Autoencoder Anomaly Detection (Threshold Methods A, B, C, D)
2. Standalone XGBoost Classifier
3. Hybrid AE + XGBoost Pipeline
4. Baseline Models (LR, RF, LinearSVC, MLP)
5. Security Metrics (FPR, FNR, Detection Rate, ROC-AUC, PR-AUC)
6. Per-class metrics and Confusion Matrices
7. Visualization Generation (ROC curves, PR curves, Confusion Matrices)
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
import tensorflow as tf
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    precision_recall_curve,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def compute_security_metrics(y_true_binary: np.ndarray, y_pred_binary: np.ndarray, y_scores: np.ndarray | None = None) -> dict:
    """Compute standard IDS security metrics: FPR, FNR, TPR, TNR, Precision, Recall, F1, ROC-AUC, PR-AUC."""
    cm = confusion_matrix(y_true_binary, y_pred_binary, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    tpr = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    tnr = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    
    prec = float(precision_score(y_true_binary, y_pred_binary, zero_division=0))
    rec = float(recall_score(y_true_binary, y_pred_binary, zero_division=0))
    f1 = float(f1_score(y_true_binary, y_pred_binary, zero_division=0))
    acc = float(accuracy_score(y_true_binary, y_pred_binary))
    
    metrics = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
        "tpr": tpr,
        "tnr": tnr,
        "detection_rate": tpr,
        "false_alarm_rate": fpr,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }
    
    if y_scores is not None and len(np.unique(y_true_binary)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true_binary, y_scores))
        metrics["pr_auc"] = float(average_precision_score(y_true_binary, y_scores))
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
        
    return metrics

def evaluate_canonical_experiment(dataset_name: str = "nsl_kdd", seed: int = 42) -> dict:
    print("=" * 70)
    print(f"CANONICAL EVALUATION (Seed={seed}) - {dataset_name.upper()}")
    print("=" * 70)
    
    data_dir = os.path.join(PROJECT_ROOT, "data", "cleaned", dataset_name)
    models_dir = os.path.join(PROJECT_ROOT, "models", "canonical", dataset_name, f"seed_{seed}")
    models_prep_dir = os.path.join(PROJECT_ROOT, "models", "preprocessors")
    tables_dir = os.path.join(PROJECT_ROOT, "paper", "tables")
    figures_dir = os.path.join(PROJECT_ROOT, "paper", "figures")
    results_dir = os.path.join(PROJECT_ROOT, "results", "canonical", dataset_name)
    
    os.makedirs(tables_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # Load test split
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))
    
    # Load Label Encoder
    label_encoder = joblib.load(os.path.join(models_prep_dir, f"{dataset_name}_label_encoder.pkl"))
    class_names = list(label_encoder.classes_)
    benign_class_name = "normal" if dataset_name == "nsl_kdd" else "Benign"
    normal_idx = class_names.index(benign_class_name)
    
    y_test_bin = (y_test != normal_idx).astype(int)
    
    print(f"Loaded {len(X_test):,} test flows ({np.sum(y_test_bin == 0):,} Benign, {np.sum(y_test_bin == 1):,} Attacks)")
    
    # 1. Evaluate Autoencoder
    ae = tf.keras.models.load_model(os.path.join(models_dir, "autoencoder.keras"))
    preds_ae = ae.predict(X_test, batch_size=512, verbose=0)
    test_reconstruction_errors = np.mean(np.square(X_test - preds_ae), axis=1)
    
    with open(os.path.join(models_dir, "threshold.json"), "r") as f:
        th_info = json.load(f)
    tau = th_info["threshold"]
    
    y_ae_bin_pred = (test_reconstruction_errors > tau).astype(int)
    ae_sec_metrics = compute_security_metrics(y_test_bin, y_ae_bin_pred, test_reconstruction_errors)
    print(f"[STAGE 1 - AE Anomaly Detection] Threshold: {tau:.6f} | Recall: {ae_sec_metrics['recall']:.4f} | FPR: {ae_sec_metrics['fpr']:.4f} | F1: {ae_sec_metrics['f1']:.4f} | ROC-AUC: {ae_sec_metrics['roc_auc']:.4f}")
    
    # 2. Evaluate Standalone XGBoost
    xgb = XGBClassifier()
    xgb.load_model(os.path.join(models_dir, "xgboost_model.json"))
    
    xgb_preds = xgb.predict(X_test)
    xgb_probs = xgb.predict_proba(X_test)
    
    # Multi-class metrics for standalone XGBoost
    xgb_acc = float(accuracy_score(y_test, xgb_preds))
    xgb_macro_f1 = float(f1_score(y_test, xgb_preds, average="macro", zero_division=0))
    xgb_weighted_f1 = float(f1_score(y_test, xgb_preds, average="weighted", zero_division=0))
    xgb_bin_pred = (xgb_preds != normal_idx).astype(int)
    xgb_attack_prob = 1.0 - xgb_probs[:, normal_idx]
    xgb_sec_metrics = compute_security_metrics(y_test_bin, xgb_bin_pred, xgb_attack_prob)
    
    print(f"[STAGE 2 - Standalone XGBoost] Multi-class Acc: {xgb_acc:.4f} | Macro-F1: {xgb_macro_f1:.4f} | FPR: {xgb_sec_metrics['fpr']:.4f}")
    
    # 3. Evaluate End-to-End Hybrid System
    # Gate: If RE <= tau -> Benign; If RE > tau -> XGBoost prediction
    # If XGBoost predicts Benign when RE > tau, keep as Anomaly or default to most likely attack
    hybrid_preds = np.zeros_like(xgb_preds)
    is_anomaly = test_reconstruction_errors > tau
    
    for i in range(len(X_test)):
        if not is_anomaly[i]:
            hybrid_preds[i] = normal_idx
        else:
            p = xgb_preds[i]
            if p == normal_idx:
                # If XGB predicted normal despite high error, take top non-normal class
                probs = xgb_probs[i].copy()
                probs[normal_idx] = -1.0
                hybrid_preds[i] = int(np.argmax(probs))
            else:
                hybrid_preds[i] = p
                
    hybrid_acc = float(accuracy_score(y_test, hybrid_preds))
    hybrid_macro_f1 = float(f1_score(y_test, hybrid_preds, average="macro", zero_division=0))
    hybrid_weighted_f1 = float(f1_score(y_test, hybrid_preds, average="weighted", zero_division=0))
    hybrid_bin_pred = (hybrid_preds != normal_idx).astype(int)
    hybrid_sec_metrics = compute_security_metrics(y_test_bin, hybrid_bin_pred, test_reconstruction_errors)
    
    print(f"[HYBRID AE + XGBoost] Multi-class Acc: {hybrid_acc:.4f} | Macro-F1: {hybrid_macro_f1:.4f} | FPR: {hybrid_sec_metrics['fpr']:.4f} | FNR: {hybrid_sec_metrics['fnr']:.4f}")
    
    # 4. Evaluate Baseline Models
    baseline_files = {
        "Logistic Regression": "baseline_logistic_regression.pkl",
        "Random Forest": "baseline_random_forest.pkl",
        "LinearSVC": "baseline_linearsvc.pkl",
        "MLP": "baseline_mlp.pkl",
    }
    
    baseline_results = []
    # Add standalone XGBoost, AE, and Hybrid to comparison
    baseline_results.append({
        "Model": "Autoencoder Anomaly Detector",
        "Accuracy": ae_sec_metrics["accuracy"],
        "Macro-F1": ae_sec_metrics["f1"],
        "Weighted-F1": ae_sec_metrics["f1"],
        "FPR": ae_sec_metrics["fpr"],
        "FNR": ae_sec_metrics["fnr"],
        "ROC-AUC": ae_sec_metrics["roc_auc"],
        "PR-AUC": ae_sec_metrics["pr_auc"],
    })
    baseline_results.append({
        "Model": "Standalone XGBoost",
        "Accuracy": xgb_acc,
        "Macro-F1": xgb_macro_f1,
        "Weighted-F1": xgb_weighted_f1,
        "FPR": xgb_sec_metrics["fpr"],
        "FNR": xgb_sec_metrics["fnr"],
        "ROC-AUC": xgb_sec_metrics["roc_auc"],
        "PR-AUC": xgb_sec_metrics["pr_auc"],
    })
    baseline_results.append({
        "Model": "Hybrid (AE + XGBoost)",
        "Accuracy": hybrid_acc,
        "Macro-F1": hybrid_macro_f1,
        "Weighted-F1": hybrid_weighted_f1,
        "FPR": hybrid_sec_metrics["fpr"],
        "FNR": hybrid_sec_metrics["fnr"],
        "ROC-AUC": hybrid_sec_metrics["roc_auc"],
        "PR-AUC": hybrid_sec_metrics["pr_auc"],
    })
    
    for b_name, b_file in baseline_files.items():
        b_path = os.path.join(models_dir, b_file)
        if os.path.exists(b_path):
            clf = joblib.load(b_path)
            b_preds = clf.predict(X_test)
            b_bin = (b_preds != normal_idx).astype(int)
            b_sec = compute_security_metrics(y_test_bin, b_bin)
            baseline_results.append({
                "Model": b_name,
                "Accuracy": float(accuracy_score(y_test, b_preds)),
                "Macro-F1": float(f1_score(y_test, b_preds, average="macro", zero_division=0)),
                "Weighted-F1": float(f1_score(y_test, b_preds, average="weighted", zero_division=0)),
                "FPR": b_sec["fpr"],
                "FNR": b_sec["fnr"],
                "ROC-AUC": None,
                "PR-AUC": None,
            })
            
    df_baselines = pd.DataFrame(baseline_results)
    df_baselines.to_csv(os.path.join(tables_dir, f"baseline_comparison_{dataset_name}.csv"), index=False)
    print(f"[OK] Saved baseline comparison table to paper/tables/baseline_comparison_{dataset_name}.csv")
    
    # 5. Per-class Evaluation for Hybrid & Standalone XGBoost
    cr_hybrid = classification_report(y_test, hybrid_preds, target_names=class_names, output_dict=True, zero_division=0)
    per_class_rows = []
    for c_name in class_names:
        per_class_rows.append({
            "Class": c_name,
            "Precision": cr_hybrid[c_name]["precision"],
            "Recall": cr_hybrid[c_name]["recall"],
            "F1-Score": cr_hybrid[c_name]["f1-score"],
            "Support": int(cr_hybrid[c_name]["support"]),
        })
    df_per_class = pd.DataFrame(per_class_rows)
    df_per_class.to_csv(os.path.join(tables_dir, f"per_class_{dataset_name}.csv"), index=False)
    print(f"[OK] Saved per-class metrics to paper/tables/per_class_{dataset_name}.csv")
    
    # 6. Confusion Matrix Plots & Tables
    cm_hybrid = confusion_matrix(y_test, hybrid_preds, labels=range(len(class_names)))
    cm_hybrid_norm = cm_hybrid.astype("float") / (cm_hybrid.sum(axis=1)[:, np.newaxis] + 1e-9)
    
    df_cm = pd.DataFrame(cm_hybrid, index=class_names, columns=class_names)
    df_cm.to_csv(os.path.join(tables_dir, f"confusion_matrix_{dataset_name}.csv"))
    
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm_hybrid_norm, annot=True, fmt=".2f", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.title(f"Normalized Confusion Matrix - Hybrid ({dataset_name.upper()})", fontsize=12, pad=12)
    plt.ylabel("True Class", fontsize=10)
    plt.xlabel("Predicted Class", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, f"confusion_hybrid_{dataset_name}.png"), dpi=300)
    plt.close()
    
    # 7. ROC and Precision-Recall Curves
    if ae_sec_metrics["roc_auc"] is not None:
        fpr_arr, tpr_arr, _ = roc_curve(y_test_bin, test_reconstruction_errors)
        prec_arr, rec_arr, _ = precision_recall_curve(y_test_bin, test_reconstruction_errors)
        
        plt.figure(figsize=(6, 5))
        plt.plot(fpr_arr, tpr_arr, color="#1f77b4", lw=2, label=f"Autoencoder (AUC = {ae_sec_metrics['roc_auc']:.4f})")
        plt.plot([0, 1], [0, 1], color="grey", linestyle="--")
        plt.xlabel("False Positive Rate (FPR)", fontsize=10)
        plt.ylabel("True Positive Rate (TPR)", fontsize=10)
        plt.title(f"ROC Curve - Anomaly Detection ({dataset_name.upper()})", fontsize=12)
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, f"roc_curves_{dataset_name}.png"), dpi=300)
        plt.close()
        
        plt.figure(figsize=(6, 5))
        plt.plot(rec_arr, prec_arr, color="#2ca02c", lw=2, label=f"Autoencoder (PR-AUC = {ae_sec_metrics['pr_auc']:.4f})")
        plt.xlabel("Recall", fontsize=10)
        plt.ylabel("Precision", fontsize=10)
        plt.title(f"Precision-Recall Curve ({dataset_name.upper()})", fontsize=12)
        plt.legend(loc="lower left")
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, f"precision_recall_curves_{dataset_name}.png"), dpi=300)
        plt.close()
        
    # Save overall canonical experiment metrics
    experiment_metrics = {
        "dataset": dataset_name,
        "seed": seed,
        "threshold": tau,
        "autoencoder": ae_sec_metrics,
        "xgboost_standalone": {
            "accuracy": xgb_acc,
            "macro_f1": xgb_macro_f1,
            "weighted_f1": xgb_weighted_f1,
            "security": xgb_sec_metrics,
        },
        "hybrid": {
            "accuracy": hybrid_acc,
            "macro_f1": hybrid_macro_f1,
            "weighted_f1": hybrid_weighted_f1,
            "security": hybrid_sec_metrics,
        },
        "per_class": cr_hybrid,
    }
    
    with open(os.path.join(results_dir, f"seed_{seed}_metrics.json"), "w") as f:
        json.dump(experiment_metrics, f, indent=4)
        
    print(f"[SUCCESS] Canonical evaluation complete for {dataset_name.upper()}.")
    return experiment_metrics

if __name__ == "__main__":
    evaluate_canonical_experiment("nsl_kdd", seed=42)
    evaluate_canonical_experiment("cicids2018", seed=42)
