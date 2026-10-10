"""
evaluation/class_distribution.py
================================
Class distribution analysis and figure generator for paper submission.
Generates:
- class counts & percentages
- imbalance ratios
- train/validation/test comparison
- figures/class_distribution.png
"""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def analyze_and_plot_distributions(dataset_name: str = "nsl_kdd") -> pd.DataFrame:
    splits_dir = os.path.join(PROJECT_ROOT, "data", "splits", dataset_name)
    train_df = pd.read_parquet(os.path.join(splits_dir, "train.parquet"))
    val_df = pd.read_parquet(os.path.join(splits_dir, "val.parquet"))
    test_df = pd.read_parquet(os.path.join(splits_dir, "test.parquet"))
    
    label_col = "category" if "category" in train_df.columns else ("Label" if "Label" in train_df.columns else "label")
    
    train_counts = train_df[label_col].value_counts()
    val_counts = val_df[label_col].value_counts()
    test_counts = test_df[label_col].value_counts()
    
    df_dist = pd.DataFrame({
        "Train": train_counts,
        "Validation": val_counts,
        "Test": test_counts,
    }).fillna(0).astype(int)
    
    df_dist["Total"] = df_dist.sum(axis=1)
    df_dist["Percentage"] = (df_dist["Total"] / df_dist["Total"].sum() * 100).round(2)
    
    out_table = os.path.join(PROJECT_ROOT, "paper", "tables", f"class_distribution_{dataset_name}.csv")
    os.makedirs(os.path.dirname(out_table), exist_ok=True)
    df_dist.to_csv(out_table)
    
    # Generate Publication Figure
    fig, ax = plt.subplots(figsize=(10, 6))
    df_plot = df_dist[["Train", "Validation", "Test"]].copy()
    df_plot.plot(kind="bar", stacked=False, ax=ax, colormap="viridis", edgecolor="black", alpha=0.85)
    
    ax.set_title(f"Class Distribution across Canonical Splits — {dataset_name.upper()}", fontsize=14, pad=15)
    ax.set_xlabel("Attack Class", fontsize=12)
    ax.set_ylabel("Sample Count (log scale)", fontsize=12)
    ax.set_yscale("log")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    
    out_fig = os.path.join(PROJECT_ROOT, "paper", "figures", f"class_distribution_{dataset_name}.png")
    os.makedirs(os.path.dirname(out_fig), exist_ok=True)
    plt.savefig(out_fig, dpi=300)
    plt.close()
    
    print(f"[SUCCESS] Analyzed {dataset_name}: Saved table to {out_table} and figure to {out_fig}")
    return df_dist

if __name__ == "__main__":
    analyze_and_plot_distributions("nsl_kdd")
    analyze_and_plot_distributions("cicids2018")
