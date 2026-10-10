"""
dashboard/research_pages.py
============================
Additional research-oriented dashboard pages for the Hybrid IDS.

Pages added:
  - Ablation Study          (Models A→G comparison)
  - SHAP Explainability     (Global + local feature importance)
  - Drift Detection         (KS, PSI, JSD results)
  - Unseen Attack Eval      (Leave-one-class-out results)
  - Baseline Comparison     (LR, RF, SVM, MLP, XGB, AE, Hybrid)
  - Temporal Evaluation     (Temporal vs random split)
  - Performance Metrics     (Latency, throughput, CPU, memory)
  - Severity Analysis       (Alert severity distribution)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _load_json(path: str | Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _pct(v) -> str:
    if v is None or (isinstance(v, float) and (v != v)):
        return "N/A"
    return f"{float(v) * 100:.2f}%"


def _metric(v) -> str:
    if v is None:
        return "N/A"
    return f"{float(v):.4f}"


def _eval_dir(project_root: Path, dataset: str) -> Path:
    return project_root / "result_images" / dataset / "evaluation"


# ─────────────────────────────────────────────
#  Ablation Study Page
# ─────────────────────────────────────────────

def page_ablation(project_root: Path, dataset: str) -> None:
    st.subheader("Ablation Study — Component Contribution Analysis")
    st.caption(
        "Compares 7 model variants (A→G) to quantify the contribution "
        "of each system component."
    )

    ablation_csv = _eval_dir(project_root, dataset) / "ablation" / "ablation_results.csv"

    if not ablation_csv.exists():
        st.warning(
            f"No ablation results found.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`"
        )
        st.markdown("""
        ### Planned Ablation Models
        | Model | Description |
        |-------|-------------|
        | A | XGBoost only (no anomaly filter) |
        | B | Autoencoder only (binary detection) |
        | C | AE + XGBoost (untuned threshold) |
        | D | AE + XGBoost + Fixed tuned threshold |
        | E | AE + XGBoost + Adaptive threshold (μ+kσ) |
        | F | AE + XGBoost + Adaptive + SHAP |
        | G | Full system (A→F + temporal + unseen) |
        """)
        return

    df = pd.read_csv(ablation_csv)

    # KPI row
    if not df.empty and "accuracy" in df.columns:
        best = df.loc[df["f1_weighted"].idxmax()] if "f1_weighted" in df.columns else df.iloc[-1]
        st.metric("Best Model", str(best["model"]),
                  help="Model with highest weighted F1")

    # Bar chart: F1 and FPR
    key_metrics = ["f1_weighted", "f1_macro", "fpr", "fnr"]
    present = [m for m in key_metrics if m in df.columns]

    if present:
        fig = go.Figure()
        colors = px.colors.qualitative.Set2
        for i, metric in enumerate(present):
            fig.add_trace(go.Bar(
                name=metric.replace("_", " ").title(),
                x=df["model"],
                y=df[metric],
                marker_color=colors[i % len(colors)],
            ))
        fig.update_layout(
            barmode="group",
            title=f"Ablation Study — Key Metrics ({dataset.upper()})",
            xaxis_tickangle=-30,
            yaxis_range=[0, 1.05],
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Latency comparison
    if "latency_ms_per_sample" in df.columns:
        fig2 = px.bar(
            df, x="model", y="latency_ms_per_sample",
            title="Detection Latency by Model (ms/sample)",
            color="model", color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig2.update_layout(height=350, xaxis_tickangle=-30, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Table
    st.markdown("#### Full ablation results table")
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download ablation results (CSV)", csv, "ablation_results.csv", "text/csv")


# ─────────────────────────────────────────────
#  SHAP Explainability Page
# ─────────────────────────────────────────────

def page_shap(project_root: Path, dataset: str) -> None:
    st.subheader("SHAP Explainability — Feature Contribution Analysis")
    st.caption(
        "Global and local SHAP explanations for XGBoost attack classifications. "
        "Every alert in the live pipeline receives a local SHAP explanation."
    )

    shap_dir    = _eval_dir(project_root, dataset) / "shap"
    shap_json   = shap_dir / "shap_summary.json"
    ranking_csv = shap_dir / "shap_feature_ranking.csv"

    if not shap_json.exists():
        st.warning(
            f"No SHAP results found.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`\n\n"
            f"(SHAP analysis is included in the full evaluation pipeline.)"
        )
        return

    summary = _load_json(shap_json)

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Samples analysed", summary.get("n_samples_analysed", "N/A"))
    col2.metric("Top-K features", summary.get("top_k", 5))
    stab = summary.get("stability", {})
    col3.metric(
        "Explanation stability",
        f"{1 - stab.get('mean_rank_deviation', 0):.3f}",
        help="1 = perfectly stable top features under noise; 0 = unstable",
    )

    # Global feature importance bar chart
    if ranking_csv.exists():
        df_rank = pd.read_csv(ranking_csv).head(20)
        fig = px.bar(
            df_rank,
            x="mean_abs_shap",
            y="feature",
            orientation="h",
            title="Global SHAP Feature Importance (Top 20)",
            labels={"mean_abs_shap": "Mean |SHAP value|", "feature": "Feature"},
            color="mean_abs_shap",
            color_continuous_scale="Blues",
        )
        fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

    # Display SHAP images if present
    shap_images = list(shap_dir.glob("shap_*.png"))
    if shap_images:
        st.markdown("#### SHAP Charts")
        cols = st.columns(2)
        for i, img in enumerate(shap_images[:4]):
            with cols[i % 2]:
                st.image(str(img), caption=img.stem.replace("_", " ").title(),
                         use_container_width=True)

    # Top features text
    if summary.get("top_10_features"):
        st.markdown("#### Top 10 features (global SHAP)")
        for i, feat in enumerate(summary["top_10_features"], 1):
            st.text(f"  {i:2d}. {feat}")

    # Stability details
    if stab:
        with st.expander("Stability analysis details"):
            st.json(stab)


# ─────────────────────────────────────────────
#  Drift Detection Page
# ─────────────────────────────────────────────

def page_drift(project_root: Path, dataset: str) -> None:
    st.subheader("Concept Drift / Distribution Shift Detection")
    st.caption(
        "Monitors drift in reconstruction error and prediction distributions "
        "using KS-test, PSI, and Jensen-Shannon divergence."
    )

    drift_dir    = _eval_dir(project_root, dataset) / "drift"
    drift_report = drift_dir / "drift_report.json"

    if not drift_report.exists():
        st.warning(
            f"No drift report found.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`"
        )
        st.markdown("""
        ### Drift Detection Methods
        | Method | Formula | Threshold |
        |--------|---------|-----------|
        | KS Test | `D = sup_x |F1(x) - F2(x)|` | p < 0.05 |
        | PSI | `Σ (P-Q) * ln(P/Q)` | > 0.25 = major |
        | JSD | `½KL(P‖M) + ½KL(Q‖M)` | > 0.15 = major |
        """)
        return

    report = _load_json(drift_report)

    for signal_name, signal_data in report.items():
        drift_detected = signal_data.get("drift_detected", False)
        severity       = signal_data.get("severity", "UNKNOWN")

        color = {"NONE": "green", "MARGINAL": "blue",
                 "MINOR": "orange", "MAJOR": "red"}.get(severity, "gray")

        st.markdown(
            f"**{signal_name.replace('_', ' ').title()}** — "
            f":{color}[{severity}] {'⚠️ DRIFT' if drift_detected else '✓ Stable'}"
        )

        votes = signal_data.get("votes", {})
        ks    = signal_data.get("ks_test", {})
        psi_v = signal_data.get("psi", {})
        jsd_v = signal_data.get("jsd", {})

        col1, col2, col3 = st.columns(3)
        col1.metric("KS p-value", f"{ks.get('p_value', 0):.4f}",
                    delta="Drift" if votes.get("ks") else "Stable",
                    delta_color="inverse")
        col2.metric("PSI", f"{psi_v.get('psi_value', 0):.4f}",
                    delta="Drift" if votes.get("psi") else "Stable",
                    delta_color="inverse")
        col3.metric("JSD", f"{jsd_v.get('jsd_value', 0):.4f}",
                    delta="Drift" if votes.get("jsd") else "Stable",
                    delta_color="inverse")

        rec = signal_data.get("recommendation", "")
        if rec:
            st.info(f"**Recommendation:** {rec}")
        st.divider()

    # Drift images
    drift_images = list(drift_dir.glob("drift_*.png"))
    if drift_images:
        st.markdown("#### Distribution Comparison Plots")
        cols = st.columns(2)
        for i, img in enumerate(drift_images[:4]):
            with cols[i % 2]:
                st.image(str(img), caption=img.stem.replace("_", " ").title(),
                         use_container_width=True)


# ─────────────────────────────────────────────
#  Unseen Attack Page
# ─────────────────────────────────────────────

def page_unseen_attack(project_root: Path, dataset: str) -> None:
    st.subheader("Unseen Attack Detection (Leave-One-Class-Out)")
    st.caption(
        "Evaluates the Autoencoder's ability to detect attack categories "
        "that were excluded from XGBoost training. (RQ4, H4)"
    )

    unseen_dir = _eval_dir(project_root, dataset) / "unseen"
    unseen_csv = unseen_dir / "unseen_attack_summary.csv"

    if not unseen_csv.exists():
        st.warning(
            f"No unseen attack results.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`"
        )
        return

    df = pd.read_csv(unseen_csv)

    # Summary KPIs
    if not df.empty and "detection_rate" in df.columns:
        col1, col2, col3 = st.columns(3)
        col1.metric("Attack classes evaluated", len(df))
        col2.metric("Mean AE detection rate",
                    f"{df['detection_rate'].mean() * 100:.1f}%")
        col3.metric("Min detection rate",
                    f"{df['detection_rate'].min() * 100:.1f}%",
                    help="Worst-case unseen class")

    # Detection rate chart
    if "held_out_class" in df.columns and "detection_rate" in df.columns:
        fig = px.bar(
            df,
            x="held_out_class",
            y="detection_rate",
            color="detection_rate",
            color_continuous_scale="RdYlGn",
            title="Autoencoder Detection Rate for Unseen Attack Classes",
            labels={"held_out_class": "Held-out Class",
                    "detection_rate": "Detection Rate"},
        )
        fig.update_layout(height=400, xaxis_tickangle=-30, yaxis_range=[0, 1.05])
        fig.add_hline(y=0.5, line_dash="dash", line_color="red",
                      annotation_text="50% detection threshold")
        st.plotly_chart(fig, use_container_width=True)

    # FNR chart
    if "false_negative_rate" in df.columns:
        fig2 = px.bar(
            df,
            x="held_out_class",
            y="false_negative_rate",
            title="False Negative Rate for Unseen Attack Classes",
            labels={"false_negative_rate": "FNR", "held_out_class": "Class"},
            color="false_negative_rate",
            color_continuous_scale="Reds",
        )
        fig2.update_layout(height=350, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    # RE comparison
    if "mean_re_held_out" in df.columns and "mean_re_benign" in df.columns:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Mean RE (Held-out)", x=df["held_out_class"],
            y=df["mean_re_held_out"], marker_color="darkorange",
        ))
        if df["mean_re_benign"].std() < 1e-8:
            fig3.add_hline(y=df["mean_re_benign"].mean(),
                           line_dash="dash", line_color="green",
                           annotation_text="Benign mean RE")
        fig3.update_layout(
            title="Mean Reconstruction Error: Unseen Attack vs Benign",
            height=350, xaxis_tickangle=-30,
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Full results table")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Images
    imgs = list(unseen_dir.glob("unseen_*.png"))
    if imgs:
        st.markdown("#### Error distribution plots")
        for img in imgs[:4]:
            st.image(str(img), caption=img.stem.replace("_", " "), use_container_width=True)


# ─────────────────────────────────────────────
#  Baseline Comparison Page
# ─────────────────────────────────────────────

def page_baselines(project_root: Path, dataset: str) -> None:
    st.subheader("Baseline Model Comparison")
    st.caption(
        "Compares the proposed hybrid system against LR, RF, SVM, MLP, "
        "XGBoost-standalone, and AE-only baselines."
    )

    baselines_dir = _eval_dir(project_root, dataset) / "baselines"
    baselines_csv = baselines_dir / "baseline_comparison.csv"

    if not baselines_csv.exists():
        st.warning(
            f"No baseline results found.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`\n\n"
            f"(Baseline training can take 5-15 minutes.)"
        )
        return

    df = pd.read_csv(baselines_csv)

    # Highlight hybrid
    if not df.empty:
        best_idx = df["f1_weighted"].idxmax() if "f1_weighted" in df.columns else None
        if best_idx is not None:
            st.success(f"🏆 Best model: **{df.loc[best_idx, 'model']}** "
                       f"(F1-weighted = {df.loc[best_idx, 'f1_weighted']:.4f})")

    # Grouped bar chart
    metrics = ["accuracy", "f1_weighted", "f1_macro"]
    metrics = [m for m in metrics if m in df.columns]

    if metrics:
        fig = go.Figure()
        colors = px.colors.qualitative.Set2
        for i, metric in enumerate(metrics):
            fig.add_trace(go.Bar(
                name=metric.replace("_", " ").title(),
                x=df["model"],
                y=df[metric],
                marker_color=colors[i],
            ))
        fig.update_layout(
            barmode="group",
            title=f"Baseline Comparison — {dataset.upper()}",
            xaxis_tickangle=-30,
            yaxis_range=[0, 1.05],
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Latency comparison
    if "latency_ms_per_sample" in df.columns:
        fig2 = px.bar(
            df.dropna(subset=["latency_ms_per_sample"]),
            x="model", y="latency_ms_per_sample",
            title="Inference Latency (ms/sample)",
            color="model", color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig2.update_layout(height=350, xaxis_tickangle=-30, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Results table")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
#  Temporal Evaluation Page
# ─────────────────────────────────────────────

def page_temporal(project_root: Path, dataset: str) -> None:
    st.subheader("Temporal Evaluation — Generalization Test")
    st.caption(
        "Evaluates whether performance degrades under temporal train-test "
        "separation compared to random splitting (RQ3, H3)."
    )

    temporal_dir  = _eval_dir(project_root, dataset) / "temporal"
    results_json  = temporal_dir / "temporal_evaluation_results.json"
    compare_json  = temporal_dir / "temporal_vs_random.json"

    if not results_json.exists():
        st.warning(
            f"No temporal evaluation results.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`"
        )
        st.info(
            "**What temporal evaluation does:** Instead of random 70/15/15 splits, "
            "traffic is sorted by timestamp. Earlier traffic → training, "
            "later traffic → test. This reveals optimistic bias in random splitting."
        )
        return

    results = _load_json(results_json)
    if results:
        col1, col2, col3 = st.columns(3)
        col1.metric("Method", results.get("method", "N/A"))
        col2.metric("Train samples", f"{results.get('n_train', 0):,}")
        col3.metric("Test samples",  f"{results.get('n_test', 0):,}")

        if results.get("ae_metrics"):
            ae = results["ae_metrics"]
            st.markdown("##### Autoencoder (temporal test set)")
            cols = st.columns(4)
            cols[0].metric("Accuracy",  f"{ae.get('accuracy', 0):.4f}")
            cols[1].metric("Precision", f"{ae.get('precision', 0):.4f}")
            cols[2].metric("Recall",    f"{ae.get('recall', 0):.4f}")
            cols[3].metric("F1",        f"{ae.get('f1', 0):.4f}")

    # Random vs temporal comparison chart
    if compare_json.exists():
        comp = _load_json(compare_json)
        if comp:
            rows = []
            for metric, v in comp.items():
                rows.append({
                    "metric":    metric,
                    "random":    v.get("random", 0),
                    "temporal":  v.get("temporal", 0),
                    "gap":       v.get("generalization_gap", 0),
                })
            df_comp = pd.DataFrame(rows)

            fig = go.Figure()
            fig.add_trace(go.Bar(name="Random split",   x=df_comp["metric"],
                                 y=df_comp["random"],   marker_color="steelblue"))
            fig.add_trace(go.Bar(name="Temporal split", x=df_comp["metric"],
                                 y=df_comp["temporal"], marker_color="darkorange"))
            fig.update_layout(
                barmode="group",
                title="Generalization Gap: Random vs Temporal Split",
                yaxis_range=[0, 1.05],
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Generalization gap analysis")
            df_comp["interpretation"] = df_comp["gap"].apply(
                lambda g: "✅ Minimal" if abs(g) < 0.02
                else ("⚠️ Moderate gap" if abs(g) < 0.10
                      else "❌ Large gap (optimistic bias in random)")
            )
            st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # Temporal drift chart
    re_evo = temporal_dir / "temporal_re_evolution.png"
    if re_evo.exists():
        st.markdown("#### Reconstruction error evolution over time")
        st.image(str(re_evo), use_container_width=True)


# ─────────────────────────────────────────────
#  Performance Metrics Page
# ─────────────────────────────────────────────

def page_performance_extended(project_root: Path, dataset: str) -> None:
    st.subheader("Real-Time Performance Metrics")
    st.caption(
        "Latency, throughput, CPU utilization, and memory consumption "
        "of the detection pipeline. (RQ6, RQ7)"
    )

    perf_json = _eval_dir(project_root, dataset) / "performance_metrics.json"

    if not perf_json.exists():
        st.warning(
            f"No performance metrics found.\n\n"
            f"Run: `python run_full_evaluation.py --dataset {dataset}`"
        )
        return

    perf = _load_json(perf_json)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("AE Latency",      f"{perf.get('ae_latency_ms_per_sample', 0):.3f} ms/sample")
    col2.metric("XGB Latency",     f"{perf.get('xgb_latency_ms_per_sample', 0):.3f} ms/sample")
    col3.metric("Total Latency",   f"{perf.get('total_latency_ms_per_sample', 0):.3f} ms/sample")
    col4.metric("AE Throughput",   f"{perf.get('ae_throughput_fps', 0):,.0f} flows/s")

    if perf.get("cpu_percent") is not None:
        col1b, col2b = st.columns(2)
        col1b.metric("CPU Usage",    f"{perf.get('cpu_percent', 0):.1f}%")
        col2b.metric("Memory Usage", f"{perf.get('memory_mb', 0):.0f} MB")

    st.markdown("""
    #### Latency breakdown
    The detection pipeline has two serial stages:
    1. **Autoencoder inference** — per-flow reconstruction error
    2. **XGBoost inference** — attack classification (anomalies only)

    Total pipeline latency = AE latency + XGBoost latency (for anomalous flows).

    #### Real-time claim validation
    > We claim "real-time" detection only if total latency < 100ms/flow.
    """)

    total = perf.get("total_latency_ms_per_sample", 0)
    if total < 10:
        st.success(f"✅ Total latency {total:.3f} ms/sample — real-time capable")
    elif total < 100:
        st.info(f"ℹ️ Total latency {total:.3f} ms/sample — near real-time")
    else:
        st.warning(f"⚠️ Total latency {total:.3f} ms/sample — may not be real-time")
