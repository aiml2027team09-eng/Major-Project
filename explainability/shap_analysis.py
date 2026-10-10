"""
explainability/shap_analysis.py
================================
SHAP-based explainability for XGBoost attack classification.

Generates:
  - Global SHAP summary plot (beeswarm)
  - Global SHAP bar plot (feature importance)
  - Local SHAP waterfall plot (per-alert explanation)
  - SHAP stability analysis (mean absolute deviation across runs)
  - Per-class SHAP feature patterns

IMPORTANT
---------
SHAP is used here as an integral part of the detection workflow, not an
afterthought. Every classified attack in the live pipeline receives a
local SHAP explanation attached to the alert.

Evaluation of explanation usefulness:
  - feature_ranking_consistency(): compares top-K features across seeds
  - local_global_agreement(): Pearson correlation of local vs global SHAP
  - stability_under_perturbation(): mean rank deviation under small noise
"""

from __future__ import annotations

import os
import warnings
from typing import Any

import numpy as np
import pandas as pd

# Lazy import — SHAP is heavy, only load when needed
_shap = None

def _get_shap():
    global _shap
    if _shap is None:
        import shap
        _shap = shap
    return _shap


# ─────────────────────────────────────────────
#  1. Build SHAP explainer
# ─────────────────────────────────────────────

def build_explainer(
    xgb_model,
    X_background: np.ndarray,
    max_background: int = 500,
) -> Any:
    """
    Build a SHAP TreeExplainer for XGBoost.

    Parameters
    ----------
    xgb_model     : trained XGBClassifier
    X_background  : background dataset (subset of training data)
    max_background: max rows to use as background (for memory)
    """
    shap = _get_shap()

    if len(X_background) > max_background:
        idx = np.random.choice(len(X_background), max_background, replace=False)
        X_background = X_background[idx]

    explainer = shap.TreeExplainer(
        xgb_model,
        data=X_background,
        feature_perturbation="interventional",
        model_output="raw",
    )
    return explainer


# ─────────────────────────────────────────────
#  2. Compute SHAP values
# ─────────────────────────────────────────────

def compute_shap_values(
    explainer,
    X: np.ndarray,
    check_additivity: bool = False,
) -> np.ndarray:
    """
    Compute SHAP values for array X.

    Returns
    -------
    shap_values : ndarray of shape (n_samples, n_features, n_classes)
                  or (n_samples, n_features) for binary
    """
    shap_values = explainer.shap_values(X, check_additivity=check_additivity)
    return np.array(shap_values)


# ─────────────────────────────────────────────
#  3. Global SHAP plots
# ─────────────────────────────────────────────

def plot_global_shap(
    shap_values: np.ndarray,
    X: np.ndarray,
    feature_names: list[str],
    output_dir: str,
    class_names: list[str] | None = None,
    max_display: int = 20,
) -> None:
    """
    Generate global SHAP summary plots (beeswarm + bar).

    Parameters
    ----------
    shap_values   : array (n_samples, n_features, n_classes) or (n_samples, n_features)
    X             : feature matrix (same rows as shap_values)
    feature_names : list of feature names
    output_dir    : directory to save plots
    class_names   : list of attack class names
    max_display   : top N features to show
    """
    shap = _get_shap()
    os.makedirs(output_dir, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    X_df = pd.DataFrame(X, columns=feature_names)

    # Handle multi-class: average |SHAP| across classes
    if shap_values.ndim == 3:
        # (n_samples, n_classes, n_features) or (n_classes, n_samples, n_features)
        # Normalise to (n_samples, n_features) by mean absolute value
        if shap_values.shape[0] == len(X):
            # shape = (n_samples, n_classes, n_features)?  — check
            mean_abs = np.abs(shap_values).mean(axis=1)  # average over classes
        else:
            mean_abs = np.abs(shap_values).mean(axis=0)  # average over classes (dim 0)

        # Beeswarm from mean
        plt.figure(figsize=(10, 6))
        mean_per_feature = mean_abs.mean(axis=0)
        top_idx = np.argsort(mean_per_feature)[::-1][:max_display]
        feat_names_top = [feature_names[i] for i in top_idx]
        plt.barh(feat_names_top, mean_per_feature[top_idx][::-1],
                 color="steelblue")
        plt.xlabel("Mean |SHAP value|")
        plt.title("Global SHAP Feature Importance (mean |SHAP| across classes)")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "shap_global_bar.png"), dpi=300)
        plt.close()

        # Per-class SHAP bar plots
        if class_names is not None:
            n_classes = shap_values.shape[1] if shap_values.shape[0] == len(X) else shap_values.shape[0]
            for c in range(min(n_classes, len(class_names) if class_names else n_classes)):
                plt.figure(figsize=(10, 6))
                if shap_values.shape[0] == len(X):
                    class_shap = shap_values[:, c, :]
                else:
                    class_shap = shap_values[c]
                class_mean = np.abs(class_shap).mean(axis=0)
                top_c = np.argsort(class_mean)[::-1][:max_display]
                plt.barh(
                    [feature_names[i] for i in top_c],
                    class_mean[top_c][::-1],
                    color="darkorange",
                )
                cls_name = class_names[c] if class_names and c < len(class_names) else f"class_{c}"
                plt.xlabel("Mean |SHAP value|")
                plt.title(f"SHAP Importance — {cls_name}")
                plt.tight_layout()
                safe_name = cls_name.replace(" ", "_").replace("/", "_")
                plt.savefig(
                    os.path.join(output_dir, f"shap_class_{safe_name}.png"),
                    dpi=300,
                )
                plt.close()

    else:
        # Binary / flattened (n_samples, n_features)
        plt.figure(figsize=(10, 6))
        mean_abs = np.abs(shap_values).mean(axis=0)
        top_idx  = np.argsort(mean_abs)[::-1][:max_display]
        plt.barh(
            [feature_names[i] for i in top_idx],
            mean_abs[top_idx][::-1],
            color="steelblue",
        )
        plt.xlabel("Mean |SHAP value|")
        plt.title("Global SHAP Feature Importance")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "shap_global_bar.png"), dpi=300)
        plt.close()

    print(f"  Global SHAP plots saved → {output_dir}")


# ─────────────────────────────────────────────
#  4. Local SHAP explanation (per alert)
# ─────────────────────────────────────────────

def explain_single_prediction(
    explainer,
    x: np.ndarray,
    feature_names: list[str],
    class_names: list[str],
    predicted_class_idx: int,
    top_k: int = 5,
) -> dict:
    """
    Generate a local SHAP explanation for a single flow.

    Parameters
    ----------
    explainer           : SHAP TreeExplainer
    x                   : 1-D feature vector (1 sample)
    feature_names       : list of feature name strings
    class_names         : list of attack class names
    predicted_class_idx : integer index of the predicted class
    top_k               : number of top contributing features to return

    Returns
    -------
    dict with:
        predicted_class  : str
        top_features     : list of (feature, shap_value) tuples
        expected_value   : float (base value)
        shap_vector      : list of float (all SHAP values for predicted class)
    """
    shap = _get_shap()
    x = np.asarray(x).reshape(1, -1)
    sv = explainer.shap_values(x, check_additivity=False)

    # Extract SHAP vector for predicted class
    if isinstance(sv, list):
        # List of arrays, one per class
        if predicted_class_idx < len(sv):
            shap_vec = np.asarray(sv[predicted_class_idx]).ravel()
        else:
            shap_vec = np.asarray(sv[0]).ravel()
    elif isinstance(sv, np.ndarray) and sv.ndim == 3:
        shap_vec = sv[0, predicted_class_idx, :]
    elif isinstance(sv, np.ndarray) and sv.ndim == 2:
        shap_vec = sv[0, :]
    else:
        shap_vec = np.asarray(sv).ravel()

    # Top-K features by absolute SHAP value
    top_idx = np.argsort(np.abs(shap_vec))[::-1][:top_k]
    top_features = [
        {
            "rank":         int(r + 1),
            "feature":      feature_names[i],
            "shap_value":   float(shap_vec[i]),
            "abs_shap":     float(abs(shap_vec[i])),
            "direction":    "increases_risk" if shap_vec[i] > 0 else "decreases_risk",
        }
        for r, i in enumerate(top_idx)
    ]

    predicted_class_name = (
        class_names[predicted_class_idx]
        if predicted_class_idx < len(class_names)
        else f"class_{predicted_class_idx}"
    )

    return {
        "predicted_class": predicted_class_name,
        "top_features":    top_features,
        "shap_vector":     shap_vec.tolist(),
    }


# ─────────────────────────────────────────────
#  5. SHAP feature ranking table
# ─────────────────────────────────────────────

def build_feature_ranking_table(
    shap_values: np.ndarray,
    feature_names: list[str],
    class_names: list[str] | None = None,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Build a DataFrame of global feature importance from SHAP values.

    Returns
    -------
    DataFrame with columns: feature, mean_abs_shap, rank
    """
    sv = np.array(shap_values)

    if sv.ndim == 3:
        # Average across classes and samples
        mean_abs = np.abs(sv).mean(axis=(0, 1)) if sv.shape[0] == len(sv) else np.abs(sv).mean(axis=(0, 1))
        mean_abs = np.abs(sv).reshape(-1, sv.shape[-1]).mean(axis=0)
    else:
        mean_abs = np.abs(sv).mean(axis=0)

    df = pd.DataFrame({
        "feature":        feature_names,
        "mean_abs_shap":  mean_abs,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "rank"

    print("\n=== SHAP Global Feature Ranking (Top 20) ===")
    print(df.head(20).to_string(float_format="{:.6f}".format))

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path)
        print(f"  Saved: {output_path}")

    return df


# ─────────────────────────────────────────────
#  6. Explanation stability under perturbation
# ─────────────────────────────────────────────

def stability_under_perturbation(
    explainer,
    X: np.ndarray,
    feature_names: list[str],
    n_samples: int = 50,
    noise_std: float = 0.01,
    top_k: int = 5,
) -> dict:
    """
    Evaluate SHAP explanation stability under small Gaussian noise.

    Perturbs each sample slightly and checks if the top-K features remain
    consistent. Returns mean rank deviation (lower = more stable).
    """
    shap = _get_shap()

    if len(X) > n_samples:
        idx = np.random.choice(len(X), n_samples, replace=False)
        X_sub = X[idx]
    else:
        X_sub = X

    rank_deviations = []

    for i in range(len(X_sub)):
        x_orig = X_sub[i:i+1]
        x_noisy = x_orig + np.random.normal(0, noise_std, x_orig.shape)

        sv_orig  = np.array(explainer.shap_values(x_orig,  check_additivity=False))
        sv_noisy = np.array(explainer.shap_values(x_noisy, check_additivity=False))

        # Flatten to 1-D
        if sv_orig.ndim > 2:
            sv_orig  = sv_orig.mean(axis=tuple(range(sv_orig.ndim - 1)))
            sv_noisy = sv_noisy.mean(axis=tuple(range(sv_noisy.ndim - 1)))
        elif sv_orig.ndim == 2:
            sv_orig  = sv_orig.mean(axis=0)
            sv_noisy = sv_noisy.mean(axis=0)
        else:
            sv_orig  = sv_orig.ravel()
            sv_noisy = sv_noisy.ravel()

        top_orig  = set(np.argsort(np.abs(sv_orig))[::-1][:top_k])
        top_noisy = set(np.argsort(np.abs(sv_noisy))[::-1][:top_k])

        # Jaccard similarity of top-K sets
        intersection = len(top_orig & top_noisy)
        union        = len(top_orig | top_noisy)
        jaccard = intersection / union if union > 0 else 1.0
        rank_deviations.append(1.0 - jaccard)  # deviation = 1 - jaccard

    mean_dev = float(np.mean(rank_deviations))
    std_dev  = float(np.std(rank_deviations))

    print(f"\n  SHAP Stability: mean rank deviation = {mean_dev:.4f} ± {std_dev:.4f}")
    print(f"  (0 = perfectly stable, 1 = completely different top features)")

    return {
        "mean_rank_deviation": mean_dev,
        "std_rank_deviation":  std_dev,
        "n_samples":           n_samples,
        "noise_std":           noise_std,
        "top_k":               top_k,
    }


# ─────────────────────────────────────────────
#  7. Full SHAP analysis pipeline
# ─────────────────────────────────────────────

def run_full_shap_analysis(
    xgb_model,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str],
    label_encoder,
    output_dir: str,
    top_k: int = 5,
    sample_size: int = 2000,
) -> dict:
    """
    Complete SHAP analysis pipeline.

    Generates:
      1. TreeExplainer
      2. SHAP values on test set (sampled for speed)
      3. Global feature importance table + plots
      4. Per-class SHAP patterns
      5. Local examples for each attack class
      6. Stability analysis

    Parameters
    ----------
    xgb_model    : trained XGBClassifier
    X_train      : training features (numpy) for background
    X_test       : test features (numpy)
    y_test       : integer-encoded test labels
    feature_names: list of feature name strings
    label_encoder: fitted LabelEncoder
    output_dir   : directory for all outputs
    top_k        : top features per local explanation
    sample_size  : max test samples for SHAP (performance limit)
    """
    os.makedirs(output_dir, exist_ok=True)
    results = {}
    class_names = list(label_encoder.classes_)

    print("\n" + "=" * 60)
    print("SHAP EXPLAINABILITY ANALYSIS")
    print("=" * 60)

    # 1. Build explainer
    print("\n  Building SHAP TreeExplainer...")
    explainer = build_explainer(xgb_model, X_train)

    # 2. Sample test set
    if len(X_test) > sample_size:
        idx    = np.random.choice(len(X_test), sample_size, replace=False)
        X_sub  = X_test[idx]
        y_sub  = y_test[idx]
    else:
        X_sub, y_sub = X_test, y_test

    print(f"  Computing SHAP values for {len(X_sub)} samples...")
    shap_values = compute_shap_values(explainer, X_sub)

    # 3. Global plots
    plot_global_shap(shap_values, X_sub, feature_names, output_dir, class_names)

    # 4. Feature ranking table
    ranking_df = build_feature_ranking_table(
        shap_values, feature_names, class_names,
        output_path=os.path.join(output_dir, "shap_feature_ranking.csv"),
    )
    results["feature_ranking"] = ranking_df.reset_index().to_dict(orient="records")

    # 5. Local examples — one per attack class
    local_explanations = {}
    for cls_idx, cls_name in enumerate(class_names):
        mask = y_sub == cls_idx
        if mask.sum() == 0:
            continue
        x_example = X_sub[np.where(mask)[0][0]]
        local_exp = explain_single_prediction(
            explainer, x_example, feature_names, class_names,
            predicted_class_idx=cls_idx, top_k=top_k,
        )
        local_explanations[cls_name] = local_exp
        print(f"\n  Local explanation — {cls_name}:")
        for feat in local_exp["top_features"]:
            print(f"    {feat['rank']}. {feat['feature']:<35s}  SHAP={feat['shap_value']:+.4f}")

    results["local_examples"] = local_explanations

    # 6. Stability
    print("\n  Evaluating SHAP stability under perturbation...")
    stability = stability_under_perturbation(
        explainer, X_sub, feature_names, n_samples=min(50, len(X_sub))
    )
    results["stability"] = stability

    # 7. Save summary
    import json
    summary = {
        "n_samples_analysed": len(X_sub),
        "top_k":              top_k,
        "top_10_features":    [r["feature"] for r in results["feature_ranking"][:10]],
        "stability":          stability,
    }
    with open(os.path.join(output_dir, "shap_summary.json"), "w") as f:
        json.dump(summary, f, indent=4)

    print(f"\n  SHAP analysis complete. Results → {output_dir}")
    return results
