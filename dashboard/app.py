"""Streamlit dashboard for Hybrid IDS alerts and model results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# pyrefly: ignore [missing-import]
import streamlit as st

from dashboard.alert_parser import load_all_alerts
from dashboard.metrics_loader import (
    EXPECTED_TARGETS,
    build_outcome_table,
    dataset_display_name,
    list_result_images,
    load_all_dataset_classes,
    load_metrics_summary,
    load_retrain_comparison,
    load_retrain_results,
    metrics_to_long_df,
    get_threshold_info,
)
from dashboard.research_pages import (
    page_ablation,
    page_shap,
    page_drift,
    page_unseen_attack,
    page_baselines,
    page_temporal,
    page_performance_extended,
)
from dataset_config import VALID_DATASETS

PROJECT_ROOT = Path(__file__).resolve().parent.parent

st.set_page_config(
    page_title="Hybrid IDS Research Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.2f}%"


@st.cache_data(ttl=30)
def _load_alerts() -> pd.DataFrame:
    return load_all_alerts(PROJECT_ROOT)


@st.cache_data(ttl=60)
def _load_outcomes() -> pd.DataFrame:
    return build_outcome_table(PROJECT_ROOT)


@st.cache_data(ttl=60)
def _load_dataset_classes() -> dict[str, list[str]]:
    return load_all_dataset_classes(PROJECT_ROOT)


def _sidebar_filters(alerts: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    all_classes = _load_dataset_classes()

    dataset_options = ["All"] + list(VALID_DATASETS)
    dataset_labels = {
        "All": "All datasets",
        **{
            ds: f"{dataset_display_name(ds)} ({ds})"
            for ds in VALID_DATASETS
        },
    }
    selected_dataset = st.sidebar.selectbox(
        "Dataset",
        dataset_options,
        format_func=lambda x: dataset_labels.get(x, x),
    )

    filtered = alerts.copy()
    if selected_dataset != "All" and not filtered.empty and "dataset_key" in filtered.columns:
        filtered = filtered[filtered["dataset_key"] == selected_dataset]

    # Attack classes from label encoder (full list), not only classes seen in alerts
    if selected_dataset == "All":
        label_pool = sorted(
            {cls for classes in all_classes.values() for cls in classes}
        )
    else:
        label_pool = all_classes.get(selected_dataset, [])

    alert_labels = (
        sorted(filtered["predicted_label"].dropna().unique().tolist())
        if not filtered.empty and "predicted_label" in filtered.columns
        else []
    )

    label_options = ["All"] + label_pool
    selected_label = st.sidebar.selectbox("Attack class", label_options)

    if selected_label != "All" and not filtered.empty and "predicted_label" in filtered.columns:
        filtered = filtered[filtered["predicted_label"] == selected_label]

    # Show counts so user knows which classes have live alerts
    if label_pool:
        with st.sidebar.expander("Class alert counts", expanded=False):
            for cls in label_pool:
                if not alerts.empty and "predicted_label" in alerts.columns:
                    if selected_dataset == "All":
                        count = int((alerts["predicted_label"] == cls).sum())
                    elif "dataset_key" in alerts.columns:
                        count = int(
                            (
                                (alerts["dataset_key"] == selected_dataset)
                                & (alerts["predicted_label"] == cls)
                            ).sum()
                        )
                    else:
                        count = 0
                else:
                    count = 0
                in_alerts = " (in alerts)" if cls in alert_labels else ""
                st.caption(f"{cls}: {count}{in_alerts}")

    if selected_dataset == "cicids2018" and alerts.empty:
        st.sidebar.info("No CICIDS2018 alerts yet. Run live monitor with --dataset cicids2018 or both.")
    elif selected_dataset == "cicids2018" and not alerts.empty and "dataset_key" in alerts.columns:
        cicids_count = int((alerts["dataset_key"] == "cicids2018").sum())
        if cicids_count == 0:
            st.sidebar.info(
                "No CICIDS2018 alerts logged yet. "
                "Run: python live_monitor.py --dataset both --interface \"Wi-Fi\""
            )

    if not filtered.empty:
        show_fp_only = st.sidebar.checkbox("Likely false positives only", value=False)
        if show_fp_only and "likely_false_positive" in filtered.columns:
            filtered = filtered[filtered["likely_false_positive"]]

        min_conf = st.sidebar.slider(
            "Min confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
        )
        if "confidence" in filtered.columns:
            filtered = filtered[filtered["confidence"] >= min_conf]
    elif selected_label != "All" or selected_dataset != "All":
        st.sidebar.warning("No alerts match the current filters.")

    st.sidebar.divider()
    st.sidebar.markdown("**Supported attack classes**")
    for ds in VALID_DATASETS:
        classes = all_classes.get(ds, [])
        if classes:
            st.sidebar.caption(
                f"{dataset_display_name(ds)}: {', '.join(classes)}"
            )

    st.sidebar.divider()
    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

    return filtered


def _kpi_row(items: list[tuple[str, str, str | None]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)


def page_overview(alerts: pd.DataFrame) -> None:
    st.subheader("Overview")

    total_alerts = len(alerts)
    fp_count = int(alerts["likely_false_positive"].sum()) if "likely_false_positive" in alerts.columns else 0
    attack_count = total_alerts - fp_count
    fp_rate = (fp_count / total_alerts * 100) if total_alerts else 0.0

    outcomes = _load_outcomes()
    met = int(outcomes["met_target"].sum()) if not outcomes.empty else 0
    total_targets = len(outcomes)

    _kpi_row(
        [
            ("Total alerts", str(total_alerts), "All logged anomaly events"),
            ("Likely attacks", str(attack_count), "Predicted as non-normal class"),
            ("Likely false positives", str(fp_count), f"{fp_rate:.1f}% of alerts"),
            ("Targets met", f"{met}/{total_targets}", "Expected vs actual test metrics"),
        ]
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Model performance snapshot")
        for dataset in ("nsl_kdd", "cicids2018"):
            metrics = load_metrics_summary(PROJECT_ROOT, dataset)
            if not metrics:
                continue
            ae = metrics.get("Autoencoder", {})
            st.markdown(f"**{dataset.upper()}**")
            st.write(
                f"AE test accuracy: **{_pct(ae.get('test_accuracy'))}** | "
                f"F1: **{_pct(ae.get('test_f1'))}** | "
                f"Hybrid: **{_pct(metrics.get('Hybrid', {}).get('test_accuracy'))}**"
            )

    with col2:
        st.markdown("#### Retrain impact")
        retrain = load_retrain_comparison(PROJECT_ROOT)
        if retrain:
            for ds, data in retrain.items():
                delta = data.get("delta", {})
                st.markdown(f"**{ds.upper()}**")
                st.write(
                    f"AE accuracy: **{delta.get('autoencoder_test_accuracy', 0):+.2%}** | "
                    f"F1: **{delta.get('autoencoder_test_f1', 0):+.2%}**"
                )
        else:
            st.info("Run live retrain to populate `result_images/retrain_comparison.json`.")

    if not alerts.empty:
        st.divider()
        st.markdown("#### Recent alerts")
        display_cols = [
            c
            for c in [
                "timestamp",
                "dataset",
                "flow",
                "predicted_label",
                "confidence",
                "reconstruction_error",
                "likely_false_positive",
            ]
            if c in alerts.columns
        ]
        st.dataframe(alerts[display_cols].head(20), width='stretch', hide_index=True)


def page_alerts(alerts: pd.DataFrame) -> None:
    st.subheader("Live alert analysis")

    all_classes = _load_dataset_classes()
    st.caption(
        "Classes are loaded from trained label encoders. "
        "Live alerts may only contain a subset (e.g. normal, dos) until attacks are detected."
    )

    if alerts.empty:
        st.warning(
            "No alerts match the current filters.\n\n"
            "To generate CICIDS2018 alerts, run:\n\n"
            "`python live_monitor.py --dataset both --interface \"Wi-Fi\"`"
        )
        st.markdown("#### All supported classes (from trained models)")
        for ds, classes in all_classes.items():
            st.write(f"**{dataset_display_name(ds)}:** {', '.join(classes)}")
        return

    col1, col2 = st.columns(2)

    with col1:
        if "timestamp" in alerts.columns:
            timeline = (
                alerts.dropna(subset=["timestamp"])
                .set_index("timestamp")
                .resample("1min")
                .size()
                .reset_index(name="count")
            )
            if not timeline.empty:
                fig = px.line(
                    timeline,
                    x="timestamp",
                    y="count",
                    title="Alerts over time",
                    labels={"count": "Alerts per minute"},
                )
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, width='stretch')

    with col2:
        if "predicted_label" in alerts.columns:
            label_counts = alerts["predicted_label"].value_counts().reset_index()
            label_counts.columns = ["label", "count"]
            # Include all known classes with zero count for context
            known = sorted(
                {cls for classes in all_classes.values() for cls in classes}
            )
            full_counts = pd.DataFrame({"label": known})
            full_counts = full_counts.merge(label_counts, on="label", how="left")
            full_counts["count"] = full_counts["count"].fillna(0).astype(int)
            fig = px.pie(
                full_counts[full_counts["count"] > 0] if full_counts["count"].sum() > 0 else full_counts,
                names="label",
                values="count",
                title="Alert class distribution",
                hole=0.35,
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, width='stretch')

    col3, col4 = st.columns(2)

    with col3:
        if "confidence" in alerts.columns:
            fig = px.histogram(
                alerts,
                x="confidence",
                nbins=30,
                color="likely_false_positive" if "likely_false_positive" in alerts.columns else None,
                title="Confidence distribution",
                labels={"confidence": "XGBoost confidence"},
            )
            fig.update_layout(height=350, barmode="overlay")
            st.plotly_chart(fig, width='stretch')

    with col4:
        if "reconstruction_error" in alerts.columns:
            fig = px.histogram(
                alerts,
                x="reconstruction_error",
                nbins=30,
                title="Reconstruction error distribution",
                labels={"reconstruction_error": "AE reconstruction error"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, width='stretch')

    if "dst_ip" in alerts.columns:
        st.markdown("#### Top destination IPs")
        top_dst = alerts["dst_ip"].value_counts().head(10).reset_index()
        top_dst.columns = ["dst_ip", "alerts"]
        st.dataframe(top_dst, width='stretch', hide_index=True)

    st.markdown("#### Alert log table")
    st.dataframe(alerts, width='stretch', hide_index=True)

    csv = alerts.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered alerts (CSV)", csv, "ids_alerts.csv", "text/csv")


def page_performance() -> None:
    st.subheader("Model performance")

    dataset = st.selectbox("Select dataset", ["nsl_kdd", "cicids2018"], key="perf_dataset")
    metrics = load_metrics_summary(PROJECT_ROOT, dataset)

    if not metrics:
        st.warning(f"No metrics at `result_images/{dataset}/metrics_summary.json`. Run training first.")
        return

    long_df = metrics_to_long_df(metrics, dataset, split="test")
    if long_df.empty:
        return

    fig = px.bar(
        long_df,
        x="stage",
        y="value",
        color="metric",
        barmode="group",
        title=f"{dataset.upper()} — Test set metrics by pipeline stage",
        labels={"value": "Score", "stage": "Stage"},
        range_y=[0, 1.05],
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, width='stretch')

    val_df = metrics_to_long_df(metrics, dataset, split="validation")
    compare = pd.merge(
        long_df,
        val_df,
        on=["dataset", "stage", "metric"],
        suffixes=("_test", "_validation"),
    )
    if not compare.empty:
        fig2 = go.Figure()
        for metric in ("accuracy", "precision", "recall", "f1"):
            subset = compare[compare["metric"] == metric]
            if subset.empty:
                continue
            fig2.add_trace(
                go.Bar(
                    name=f"{metric} (val)",
                    x=subset["stage"],
                    y=subset["value_validation"],
                    opacity=0.6,
                )
            )
            fig2.add_trace(
                go.Bar(
                    name=f"{metric} (test)",
                    x=subset["stage"],
                    y=subset["value_test"],
                )
            )
        fig2.update_layout(
            barmode="group",
            title="Validation vs test comparison",
            yaxis_range=[0, 1.05],
            height=420,
        )
        st.plotly_chart(fig2, width='stretch')

    st.markdown("#### Result charts")
    images = list_result_images(PROJECT_ROOT, dataset)
    if not images:
        st.info("No result images found. Run `python generate_result_images.py --dataset " + dataset + "`")
        return

    chart_names = st.multiselect(
        "Charts to display",
        options=sorted(images.keys()),
        default=sorted(images.keys())[:4],
    )
    cols = st.columns(2)
    for i, name in enumerate(chart_names):
        with cols[i % 2]:
            st.image(str(images[name]), caption=name.replace("_", " ").title(), width='stretch')


def page_expected_outcomes() -> None:
    st.subheader("Expected outcomes vs actual results")

    st.markdown(
        """
        This page compares **project target metrics** against your latest test-set results.
        Targets reflect realistic goals for each dataset and pipeline stage.
        """
    )

    outcomes = _load_outcomes()
    if outcomes.empty:
        st.warning("No metrics available. Train models and run `generate_result_images.py` first.")
        return

    met_pct = outcomes["met_target"].mean() * 100
    _kpi_row(
        [
            ("Targets evaluated", str(len(outcomes)), None),
            ("Targets met", str(int(outcomes["met_target"].sum())), None),
            ("Success rate", f"{met_pct:.1f}%", None),
        ]
    )

    st.markdown("#### Target checklist")
    display = outcomes.copy()
    display["expected"] = display["expected"].map(_pct)
    display["actual"] = display["actual"].map(_pct)
    display["delta"] = display["delta"].map(lambda x: f"{x:+.2%}")
    display["status"] = display["met_target"].map({True: "PASS", False: "FAIL"})
    st.dataframe(
        display[
            ["dataset", "stage", "metric", "expected", "actual", "delta", "status"]
        ],
        width='stretch',
        hide_index=True,
    )

    fig = px.bar(
        outcomes,
        x="metric",
        y="actual",
        color="met_target",
        facet_col="dataset",
        facet_row="stage",
        title="Actual vs expected (bar height = actual; color = pass/fail)",
        labels={"actual": "Actual score", "met_target": "Target met"},
        range_y=[0, 1.05],
    )
    fig.add_hline(y=0.85, line_dash="dash", line_color="gray", annotation_text="Sample target line")
    st.plotly_chart(fig, width='stretch')

    with st.expander("View configured targets"):
        st.json(EXPECTED_TARGETS)

    st.markdown("#### Interpretation guide")
    st.markdown(
        """
        | Signal | Meaning |
        |--------|---------|
        | AE flagged but class = **normal/Benign** | Likely **false positive** — tune threshold or retrain AE on live traffic |
        | High confidence + attack class | Strong alert — investigate flow |
        | Low hybrid accuracy on NSL-KDD | Expected — multi-class naming on hard minority attacks |
        | CICIDS2018 hybrid ~100% | Subset has only 3 classes; XGBoost performs very well |
        """
    )


def page_retrain() -> None:
    st.subheader("Live retrain impact")

    comparison = load_retrain_comparison(PROJECT_ROOT)
    if not comparison:
        st.info(
            "No retrain comparison yet. Run:\n\n"
            "`python retrain_from_live.py --dataset both --interface \"Wi-Fi\" --capture-seconds 180`"
        )
        return

    for dataset, data in comparison.items():
        st.markdown(f"### {dataset.upper()}")
        before = data.get("before", {})
        after = data.get("after", {})
        delta = data.get("delta", {})
        settings = data.get("retrain_settings", {})

        cols = st.columns(4)
        cols[0].metric("AE accuracy", _pct(after.get("autoencoder_test_accuracy")), f"{delta.get('autoencoder_test_accuracy', 0):+.2%}")
        cols[1].metric("AE F1", _pct(after.get("autoencoder_test_f1")), f"{delta.get('autoencoder_test_f1', 0):+.2%}")
        cols[2].metric("Hybrid accuracy", _pct(after.get("hybrid_test_accuracy")), f"{delta.get('hybrid_test_accuracy', 0):+.2%}")
        cols[3].metric("Overall accuracy", _pct(after.get("overall_test_accuracy")), f"{delta.get('overall_test_accuracy', 0):+.2%}")

        compare_rows = []
        for key in before:
            compare_rows.append(
                {
                    "metric": key.replace("_", " "),
                    "before": before[key],
                    "after": after.get(key),
                    "delta": delta.get(key),
                }
            )
        compare_df = pd.DataFrame(compare_rows)
        if not compare_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Before", x=compare_df["metric"], y=compare_df["before"]))
            fig.add_trace(go.Bar(name="After", x=compare_df["metric"], y=compare_df["after"]))
            fig.update_layout(barmode="group", title="Before vs after live retrain", height=380)
            st.plotly_chart(fig, width='stretch')

        retrain_meta = load_retrain_results(PROJECT_ROOT, dataset)
        threshold = get_threshold_info(PROJECT_ROOT, dataset)
        if settings or retrain_meta:
            st.caption(
                f"Settings: oversample={settings.get('live_oversample', 'N/A')} | "
                f"threshold metric={settings.get('threshold_metric', retrain_meta.get('threshold_metric', 'N/A') if retrain_meta else 'N/A')} | "
                f"live flows={settings.get('live_flows_captured', 'N/A')}"
            )
        if threshold:
            st.caption(f"Current AE threshold: {threshold.get('threshold', 0):.6f}")


def main() -> None:
    st.title("🛡️ Hybrid IDS — Adaptive & Explainable NIDS Dashboard")
    st.caption(
        "Autoencoder + XGBoost intrusion detection | "
        "CICIDS2018 & NSL-KDD | Adaptive thresholding | SHAP explainability"
    )

    alerts = _load_alerts()
    filtered = _sidebar_filters(alerts)

    # ── Research dataset selector (for research tabs) ─────────
    with st.sidebar:
        st.divider()
        st.markdown("**Research Evaluation**")
        research_dataset = st.selectbox(
            "Research eval dataset",
            options=list(VALID_DATASETS),
            format_func=lambda x: dataset_display_name(x),
            key="research_dataset",
        )

    # ── Tabs ─────────────────────────────────────────────────────
    (
        tab_overview, tab_alerts, tab_perf, tab_outcomes, tab_retrain,
        tab_ablation, tab_shap, tab_drift, tab_unseen,
        tab_baselines, tab_temporal, tab_realtime,
    ) = st.tabs([
        "📊 Overview",
        "🚨 Live Alerts",
        "📈 Model Performance",
        "🎯 Expected Outcomes",
        "🔄 Retrain Impact",
        "🔬 Ablation Study",
        "💡 SHAP Explainability",
        "📉 Drift Detection",
        "🔍 Unseen Attacks",
        "📋 Baselines",
        "⏱️ Temporal Eval",
        "⚡ Performance",
    ])

    with tab_overview:
        page_overview(filtered)
    with tab_alerts:
        page_alerts(filtered)
    with tab_perf:
        page_performance()
    with tab_outcomes:
        page_expected_outcomes()
    with tab_retrain:
        page_retrain()

    # ── Research tabs (use research_dataset selector) ─────────
    with tab_ablation:
        page_ablation(PROJECT_ROOT, research_dataset)
    with tab_shap:
        page_shap(PROJECT_ROOT, research_dataset)
    with tab_drift:
        page_drift(PROJECT_ROOT, research_dataset)
    with tab_unseen:
        page_unseen_attack(PROJECT_ROOT, research_dataset)
    with tab_baselines:
        page_baselines(PROJECT_ROOT, research_dataset)
    with tab_temporal:
        page_temporal(PROJECT_ROOT, research_dataset)
    with tab_realtime:
        page_performance_extended(PROJECT_ROOT, research_dataset)


if __name__ == "__main__":
    main()
