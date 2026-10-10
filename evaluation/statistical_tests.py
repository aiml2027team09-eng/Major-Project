"""
evaluation/statistical_tests.py
=================================
Statistical validation for the Hybrid IDS experiments.

Addresses research rule:
  "Do not rely on a single training run."

Implements:
  - Multi-seed experiment runner
  - Mean ± standard deviation reporting
  - 95% confidence interval computation
  - Paired t-test for comparing two models
  - Wilcoxon signed-rank test (non-parametric alternative)
  - Bootstrap confidence intervals

Usage
-----
Run experiments with N different random seeds, then report
mean ± std with confidence intervals.

IMPORTANT
---------
This module only performs statistical tests on actual experiment
results. Never fabricate or extrapolate results.
"""

from __future__ import annotations

import json
import os
import warnings

import numpy as np
import pandas as pd
from scipy import stats


# ─────────────────────────────────────────────
#  1. Multi-seed runner
# ─────────────────────────────────────────────

def run_multiseed_experiment(
    experiment_fn,
    seeds: list[int],
    output_dir: str | None = None,
    **kwargs,
) -> dict:
    """
    Run experiment_fn with multiple random seeds and aggregate results.

    Parameters
    ----------
    experiment_fn : callable(seed, **kwargs) → dict of metric_name → float
    seeds         : list of random seeds
    output_dir    : if provided, save per-seed and aggregated results
    **kwargs      : passed to experiment_fn

    Returns
    -------
    dict with:
        per_seed_results: list of dicts
        mean:            dict of metric → mean
        std:             dict of metric → std
        ci_95:           dict of metric → (lower, upper)
        n_seeds:         int
    """
    print(f"\n  Running {len(seeds)}-seed experiment...")
    per_seed = []

    for seed in seeds:
        print(f"\n  Seed {seed}:")
        np.random.seed(seed)
        try:
            result = experiment_fn(seed=seed, **kwargs)
            result["seed"] = seed
            per_seed.append(result)
            print(f"    Metrics: " +
                  "  ".join(f"{k}={v:.4f}" for k, v in result.items()
                             if isinstance(v, float)))
        except Exception as e:
            warnings.warn(f"Seed {seed} failed: {e}")

    if not per_seed:
        return {"error": "All seeds failed", "seeds": seeds}

    # Collect metric names
    metric_keys = [k for k in per_seed[0].keys()
                   if isinstance(per_seed[0][k], (int, float)) and k != "seed"]

    agg = {}
    for k in metric_keys:
        values = [r[k] for r in per_seed if k in r and r[k] is not None]
        if not values:
            continue
        values = np.array(values, dtype=float)
        mean_v = float(np.mean(values))
        std_v  = float(np.std(values))
        ci     = confidence_interval_95(values)
        agg[k] = {
            "mean":  mean_v,
            "std":   std_v,
            "ci_95": ci,
            "values": values.tolist(),
        }
        print(f"  {k:<30s}: {mean_v:.4f} ± {std_v:.4f}  "
              f"CI-95% [{ci[0]:.4f}, {ci[1]:.4f}]")

    results = {
        "per_seed_results": per_seed,
        "aggregated":       agg,
        "n_seeds":          len(per_seed),
        "seeds":            seeds,
    }

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "multiseed_results.json"), "w") as f:
            json.dump(results, f, indent=4)

    return results


# ─────────────────────────────────────────────
#  2. Confidence interval (t-distribution)
# ─────────────────────────────────────────────

def confidence_interval_95(
    values: np.ndarray,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """
    Compute t-distribution based confidence interval.

    Parameters
    ----------
    values     : 1-D array of metric values
    confidence : confidence level (default 0.95)

    Returns
    -------
    (lower, upper) CI bounds
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n < 2:
        return (float(values[0]), float(values[0]))

    mean = np.mean(values)
    sem  = stats.sem(values)  # standard error of the mean
    h    = sem * stats.t.ppf((1 + confidence) / 2.0, df=n - 1)

    return (float(mean - h), float(mean + h))


# ─────────────────────────────────────────────
#  3. Paired t-test
# ─────────────────────────────────────────────

def paired_t_test(
    model_a_scores: np.ndarray,
    model_b_scores: np.ndarray,
    metric_name: str = "metric",
    alpha: float = 0.05,
) -> dict:
    """
    Paired t-test: is Model A significantly different from Model B?

    H0: Mean scores are equal.
    Reject H0 (significant difference) if p < alpha.

    Parameters
    ----------
    model_a_scores : 1-D array of scores (one per seed)
    model_b_scores : 1-D array of scores (one per seed)
    metric_name    : for logging
    alpha          : significance level

    Returns
    -------
    dict with t_statistic, p_value, significant, direction
    """
    a = np.asarray(model_a_scores, dtype=float)
    b = np.asarray(model_b_scores, dtype=float)

    if len(a) < 2 or len(b) < 2:
        warnings.warn(f"Not enough data for t-test ({metric_name}): need >= 2 seeds.")
        return {"error": "insufficient_data"}

    t_stat, p_value = stats.ttest_rel(a, b)

    significant = bool(p_value < alpha)
    direction   = "A > B" if a.mean() > b.mean() else "B > A"

    result = {
        "metric":      metric_name,
        "t_statistic": float(t_stat),
        "p_value":     float(p_value),
        "alpha":       alpha,
        "significant": significant,
        "direction":   direction,
        "a_mean":      float(a.mean()),
        "b_mean":      float(b.mean()),
        "a_std":       float(a.std()),
        "b_std":       float(b.std()),
        "interpretation": (
            f"Model improvement is statistically significant (p={p_value:.4f} < {alpha})"
            if significant
            else
            f"No significant difference (p={p_value:.4f} >= {alpha})"
        ),
    }

    print(f"\n  Paired t-test [{metric_name}]: t={t_stat:.4f}  p={p_value:.4f}  "
          f"{'SIGNIFICANT' if significant else 'not significant'}  ({direction})")
    print(f"    {result['interpretation']}")

    return result


# ─────────────────────────────────────────────
#  4. Wilcoxon signed-rank test (non-parametric)
# ─────────────────────────────────────────────

def wilcoxon_test(
    model_a_scores: np.ndarray,
    model_b_scores: np.ndarray,
    metric_name: str = "metric",
    alpha: float = 0.05,
) -> dict:
    """
    Wilcoxon signed-rank test (non-parametric, does not assume normality).

    Parameters
    ----------
    model_a_scores, model_b_scores : matched arrays (one per seed)
    metric_name, alpha             : as above

    Returns
    -------
    dict with statistic, p_value, significant
    """
    a = np.asarray(model_a_scores, dtype=float)
    b = np.asarray(model_b_scores, dtype=float)

    if len(a) < 3 or len(b) < 3:
        return {"error": "Need >= 3 samples for Wilcoxon test"}

    try:
        stat, p_value = stats.wilcoxon(a, b, alternative="two-sided")
    except ValueError as e:
        return {"error": str(e)}

    significant = bool(p_value < alpha)

    result = {
        "metric":      metric_name,
        "statistic":   float(stat),
        "p_value":     float(p_value),
        "significant": significant,
        "direction":   "A > B" if a.mean() > b.mean() else "B > A",
    }

    print(f"\n  Wilcoxon test [{metric_name}]: W={stat:.2f}  p={p_value:.4f}  "
          f"{'SIGNIFICANT' if significant else 'not significant'}")

    return result


# ─────────────────────────────────────────────
#  5. Bootstrap confidence interval
# ─────────────────────────────────────────────

def bootstrap_ci(
    values: np.ndarray,
    statistic_fn=np.mean,
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """
    Bootstrap confidence interval for a statistic.

    Parameters
    ----------
    values       : 1-D array of metric values
    statistic_fn : function to compute statistic (default: mean)
    n_bootstrap  : number of bootstrap samples
    confidence   : confidence level

    Returns
    -------
    (lower, upper) CI bounds
    """
    values = np.asarray(values, dtype=float)
    bootstrap_stats = []

    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        sample = rng.choice(values, size=len(values), replace=True)
        bootstrap_stats.append(float(statistic_fn(sample)))

    alpha   = 1 - confidence
    lower   = float(np.percentile(bootstrap_stats, 100 * alpha / 2))
    upper   = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))

    return (lower, upper)


# ─────────────────────────────────────────────
#  6. Summary table builder
# ─────────────────────────────────────────────

def build_statistical_summary(
    multiseed_results: dict,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Build a formatted summary table from multi-seed results.

    Columns: metric, mean, std, ci_lower, ci_upper
    """
    agg = multiseed_results.get("aggregated", {})
    rows = []
    for metric, v in agg.items():
        rows.append({
            "metric":    metric,
            "mean":      v["mean"],
            "std":       v["std"],
            "ci_lower":  v["ci_95"][0],
            "ci_upper":  v["ci_95"][1],
            "n_seeds":   multiseed_results["n_seeds"],
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        print("\n=== Statistical Summary (Multi-Seed) ===")
        fmt = {c: "{:.4f}".format for c in df.columns if c not in ("metric", "n_seeds")}
        print(df.to_string(index=False, float_format="{:.4f}".format))

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df.to_csv(output_path, index=False)

    return df
