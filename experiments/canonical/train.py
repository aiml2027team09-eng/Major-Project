"""
experiments/canonical/train.py
==============================
Canonical Model Training Suite:
1. Autoencoder Architectures (Baseline [128-64-32-16], Compact, Expanded)
2. Threshold Determination (Percentiles, k-sigma, Validation F1, Youden's J)
3. XGBoost Classifier (Tuned with early stopping on Validation)
4. Baseline Models (Logistic Regression, Random Forest, LinearSVC, MLP)
"""

from __future__ import annotations

import json
import os
import sys
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def build_autoencoder(input_dim: int, architecture: str = "baseline", dropout_rate: float = 0.2) -> Model:
    """Build Autoencoder architecture according to configuration."""
    configs = {
        "baseline": [128, 64, 32, 16],
        "compact": [128, 64, 32],
        "expanded": [256, 128, 64, 32],
    }
    layers = configs.get(architecture, configs["baseline"])
    
    inp = Input(shape=(input_dim,))
    x = inp
    # Encoder
    for units in layers:
        x = Dense(units, activation="relu")(x)
        if dropout_rate > 0:
            x = Dropout(dropout_rate)(x)
    # Bottleneck representation
    # Decoder
    for units in reversed(layers[:-1]):
        x = Dense(units, activation="relu")(x)
        if dropout_rate > 0:
            x = Dropout(dropout_rate)(x)
    out = Dense(input_dim, activation="linear")(x)
    
    model = Model(inputs=inp, outputs=out, name=f"Autoencoder_{architecture}")
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005), loss="mse")
    return model

def compute_reconstruction_error(model: Model, X: np.ndarray, batch_size: int = 512) -> np.ndarray:
    preds = model.predict(X, batch_size=batch_size, verbose=0)
    return np.mean(np.square(X - preds), axis=1)

def evaluate_threshold_methods(
    val_normal_errors: np.ndarray,
    val_errors: np.ndarray,
    y_val_binary: np.ndarray,
) -> dict:
    """Evaluate and compare Methods A (Percentile), B (k-sigma), C (Val F1), and D (Youden's J)."""
    results = {}
    
    # Method A: Fixed percentiles on Normal validation errors
    for p in [95.0, 97.5, 99.0, 99.5, 99.9]:
        th = float(np.percentile(val_normal_errors, p))
        preds = (val_errors > th).astype(int)
        results[f"Percentile_{p}"] = {
            "threshold": th,
            "method": f"Percentile_{p}",
            "precision": float(precision_score(y_val_binary, preds, zero_division=0)),
            "recall": float(recall_score(y_val_binary, preds, zero_division=0)),
            "f1": float(f1_score(y_val_binary, preds, zero_division=0)),
            "accuracy": float(accuracy_score(y_val_binary, preds)),
        }
        
    # Method B: Mean + k sigma on Normal validation errors
    mu = float(np.mean(val_normal_errors))
    sigma = float(np.std(val_normal_errors))
    for k in [2.0, 2.5, 3.0, 3.5]:
        th = mu + k * sigma
        preds = (val_errors > th).astype(int)
        results[f"Sigma_{k}"] = {
            "threshold": th,
            "method": f"Sigma_{k}",
            "precision": float(precision_score(y_val_binary, preds, zero_division=0)),
            "recall": float(recall_score(y_val_binary, preds, zero_division=0)),
            "f1": float(f1_score(y_val_binary, preds, zero_division=0)),
            "accuracy": float(accuracy_score(y_val_binary, preds)),
        }
        
    # Method C: Validation F1 Search
    candidates = np.percentile(val_normal_errors, np.linspace(80.0, 99.9, 200))
    best_f1 = -1
    best_c = None
    for cand in candidates:
        preds = (val_errors > cand).astype(int)
        f = f1_score(y_val_binary, preds, zero_division=0)
        if f > best_f1:
            best_f1 = f
            best_c = cand
    if best_c is None:
        best_c = float(np.percentile(val_normal_errors, 90.0))
    preds = (val_errors > best_c).astype(int)
    results["Validation_F1_Optimized"] = {
        "threshold": float(best_c),
        "method": "Validation_F1_Optimized",
        "precision": float(precision_score(y_val_binary, preds, zero_division=0)),
        "recall": float(recall_score(y_val_binary, preds, zero_division=0)),
        "f1": float(f1_score(y_val_binary, preds, zero_division=0)),
        "accuracy": float(accuracy_score(y_val_binary, preds)),
    }
    
    # Method D: Youden's J statistic (TPR - FPR)
    best_j = -2
    best_j_th = None
    for cand in candidates:
        preds = (val_errors > cand).astype(int)
        tpr = recall_score(y_val_binary, preds, zero_division=0)
        fpr = 1.0 - accuracy_score(y_val_binary[y_val_binary == 0], preds[y_val_binary == 0])
        j = tpr - fpr
        if j > best_j:
            best_j = j
            best_j_th = cand
    preds = (val_errors > best_j_th).astype(int)
    results["Youden_J_Optimized"] = {
        "threshold": float(best_j_th),
        "method": "Youden_J_Optimized",
        "precision": float(precision_score(y_val_binary, preds, zero_division=0)),
        "recall": float(recall_score(y_val_binary, preds, zero_division=0)),
        "f1": float(f1_score(y_val_binary, preds, zero_division=0)),
        "accuracy": float(accuracy_score(y_val_binary, preds)),
    }
    return results

def train_canonical_pipeline(dataset_name: str = "nsl_kdd", seed: int = 42) -> dict:
    from experiments.canonical.seed import set_global_seed
    set_global_seed(seed)
    
    print("=" * 70)
    print(f"TRAINING CANONICAL MODELS (Seed={seed}) - {dataset_name.upper()}")
    print("=" * 70)
    
    data_dir = os.path.join(PROJECT_ROOT, "data", "cleaned", dataset_name)
    X_train_smote = np.load(os.path.join(data_dir, "X_train_smote.npy"))
    y_train_smote = np.load(os.path.join(data_dir, "y_train_smote.npy"))
    X_train_normal = np.load(os.path.join(data_dir, "X_train_normal.npy"))
    X_val = np.load(os.path.join(data_dir, "X_val.npy"))
    y_val = np.load(os.path.join(data_dir, "y_val.npy"))
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))
    
    models_dir = os.path.join(PROJECT_ROOT, "models", "canonical", dataset_name, f"seed_{seed}")
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Train Baseline Autoencoder
    input_dim = X_train_normal.shape[1]
    ae = build_autoencoder(input_dim, architecture="baseline", dropout_rate=0.2)
    es = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
    lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3)
    
    print(f"Training Autoencoder on {len(X_train_normal):,} benign flows...")
    ae.fit(
        X_train_normal, X_train_normal,
        validation_split=0.15,
        epochs=35,
        batch_size=1024,
        callbacks=[es, lr],
        verbose=0,
    )
    ae.save(os.path.join(models_dir, "autoencoder.keras"))
    print("[OK] Autoencoder saved.")
    
    # Calculate errors on validation & test sets
    val_normal_idx = 0 if dataset_name == "cicids2018" else 1 # Benign code
    y_val_bin = (y_val != val_normal_idx).astype(int)
    y_test_bin = (y_test != val_normal_idx).astype(int)
    
    val_errors = compute_reconstruction_error(ae, X_val)
    val_normal_errors = val_errors[y_val_bin == 0]
    
    # 2. Select & Compare Thresholds
    th_methods = evaluate_threshold_methods(val_normal_errors, val_errors, y_val_bin)
    chosen_method = "Validation_F1_Optimized"
    if th_methods["Youden_J_Optimized"]["f1"] > th_methods["Validation_F1_Optimized"]["f1"]:
        chosen_method = "Youden_J_Optimized"
    chosen_th = th_methods[chosen_method]["threshold"]
    
    with open(os.path.join(models_dir, "threshold_comparison.json"), "w") as f:
        json.dump(th_methods, f, indent=4)
    with open(os.path.join(models_dir, "threshold.json"), "w") as f:
        json.dump({"threshold": chosen_th, "method": chosen_method}, f, indent=4)
    print(f"[OK] Selected optimal validation threshold ({chosen_method}): {chosen_th:.6f}")
    
    # 3. Train Tuned XGBoost Classifier
    n_classes = len(np.unique(y_train_smote))
    xgb = XGBClassifier(
        n_estimators=400,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.8,
        random_state=seed,
        early_stopping_rounds=25,
        eval_metric="mlogloss",
    )
    print(f"Training XGBoost classifier on {len(X_train_smote):,} balanced samples...")
    xgb.fit(X_train_smote, y_train_smote, eval_set=[(X_val, y_val)], verbose=False)
    xgb.save_model(os.path.join(models_dir, "xgboost_model.json"))
    print("[OK] XGBoost classifier saved.")
    
    # 4. Train Baselines on Identical Splits
    print("Training standard baseline models on identical splits...")
    baselines = {}
    
    rng = np.random.RandomState(seed)
    shuffled_idx = rng.permutation(len(y_train_smote))
    idx_20k = shuffled_idx[:min(20000, len(shuffled_idx))]
    idx_40k = shuffled_idx[:min(40000, len(shuffled_idx))]
    idx_30k = shuffled_idx[:min(30000, len(shuffled_idx))]
    
    # Logistic Regression
    lr_clf = LogisticRegression(max_iter=300, random_state=seed)
    lr_clf.fit(X_train_smote[idx_20k], y_train_smote[idx_20k])
    joblib.dump(lr_clf, os.path.join(models_dir, "baseline_logistic_regression.pkl"))
    
    # Random Forest
    rf_clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=seed, n_jobs=-1)
    rf_clf.fit(X_train_smote[idx_40k], y_train_smote[idx_40k])
    joblib.dump(rf_clf, os.path.join(models_dir, "baseline_random_forest.pkl"))
    
    # LinearSVC
    svc_clf = LinearSVC(max_iter=1000, random_state=seed, dual="auto")
    svc_clf.fit(X_train_smote[idx_20k], y_train_smote[idx_20k])
    joblib.dump(svc_clf, os.path.join(models_dir, "baseline_linearsvc.pkl"))
    
    # MLP
    mlp_clf = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=25, random_state=seed)
    mlp_clf.fit(X_train_smote[idx_30k], y_train_smote[idx_30k])
    joblib.dump(mlp_clf, os.path.join(models_dir, "baseline_mlp.pkl"))
    
    print("[SUCCESS] Trained and saved all canonical models and baselines.")
    return {"models_dir": models_dir, "chosen_threshold": chosen_th}

if __name__ == "__main__":
    train_canonical_pipeline("nsl_kdd", seed=42)
    train_canonical_pipeline("cicids2018", seed=42)
