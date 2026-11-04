import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def create_architecture_diagram():
    # 16:9.5 aspect ratio, 300 DPI for high-impact IEEE journal formatting
    fig, ax = plt.subplots(figsize=(16, 9.5), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.5)
    ax.axis('off')

    # Color Palette - Professional IEEE Transactions Styling
    c_bg_stage1 = '#f8fafc'
    c_border_stage1 = '#64748b'
    c_title_stage1 = '#0f172a'

    c_bg_stage2 = '#f0f7ff'
    c_border_stage2 = '#2563eb'
    c_title_stage2 = '#1e40af'

    c_bg_stage3 = '#fffbf0'
    c_border_stage3 = '#d97706'
    c_title_stage3 = '#92400e'

    c_bg_stage4 = '#f0fdf4'
    c_border_stage4 = '#16a34a'
    c_title_stage4 = '#166534'

    c_card_bg = '#ffffff'
    c_text_dark = '#0f172a'
    c_text_muted = '#475569'

    # Helper function: Draw rounded cards
    def draw_card(x, y, w, h, bg_color=c_card_bg, border_color='#cbd5e1', border_width=1.4, boxstyle="round,pad=0.15", zorder=2):
        box = FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                             facecolor=bg_color, edgecolor=border_color,
                             linewidth=border_width, zorder=zorder)
        ax.add_patch(box)
        return box

    # Helper function: Draw directional arrows
    def draw_arrow(x1, y1, x2, y2, color='#334155', width=1.4, head_w=5.0, head_l=6.0, style="Simple", zorder=4):
        arrow_style = f"{style},tail_width={width},head_width={head_w},head_length={head_l}"
        arrow = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=arrow_style,
                                color=color, linewidth=0.5, zorder=zorder)
        ax.add_patch(arrow)

    # Helper function: Draw multi-segment orthogonal routed lines with an arrow at the end
    def draw_elbow_arrow(points, color='#334155', width=1.4, head_w=5.0, head_l=6.0, zorder=4):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        # Draw polyline up to point -2
        ax.plot(xs[:-1], ys[:-1], color=color, linewidth=width, zorder=zorder, solid_capstyle='round')
        # Draw final segment with FancyArrowPatch
        arrow = FancyArrowPatch(points[-2], points[-1],
                                arrowstyle=f"Simple,tail_width={width},head_width={head_w},head_length={head_l}",
                                color=color, linewidth=0.5, zorder=zorder)
        ax.add_patch(arrow)

    # ==================== 1. TOP HEADER BANNER ====================
    draw_card(0.5, 8.65, 15.0, 0.70, bg_color='#0f172a', border_color='#1e293b', border_width=1.0, boxstyle="round,pad=0.1", zorder=3)
    ax.text(8.0, 9.12, "TWO-STAGE HYBRID NIDS: DEEP ANOMALY SCREENING & ATTACK CLASSIFICATION",
            ha='center', va='center', fontsize=12.5, fontweight='bold', color='#ffffff')
    ax.text(8.0, 8.82, "Operational CPU Latency: 0.183 ms/flow (5,464 flows/s)  |  Peak Memory: 527.0 MB RSS  |  Strict Zero-Leakage: Train ∩ Test = ∅",
            ha='center', va='center', fontsize=8.8, color='#94a3b8', fontweight='medium')

    # ==================== 2. MAIN STAGE PANELS ====================
    panel_y = 0.55
    panel_h = 7.90

    # Stage 1 Panel
    draw_card(0.5, panel_y, 3.5, panel_h, bg_color=c_bg_stage1, border_color=c_border_stage1, border_width=1.6, boxstyle="round,pad=0.2", zorder=1)
    draw_card(0.65, 8.05, 3.2, 0.32, bg_color='#e2e8f0', border_color=c_border_stage1, border_width=1.0, boxstyle="round,pad=0.08", zorder=2)
    ax.text(2.25, 8.21, "STAGE 1: INGESTION & AUDIT", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage1)

    # Stage 2 Panel
    draw_card(4.2, panel_y, 3.6, panel_h, bg_color=c_bg_stage2, border_color=c_border_stage2, border_width=1.6, boxstyle="round,pad=0.2", zorder=1)
    draw_card(4.35, 8.05, 3.3, 0.32, bg_color='#dbeafe', border_color=c_border_stage2, border_width=1.0, boxstyle="round,pad=0.08", zorder=2)
    ax.text(6.0, 8.21, "STAGE 2: ANOMALY GATING (AE)", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage2)

    # Stage 3 Panel
    draw_card(8.0, panel_y, 3.6, panel_h, bg_color=c_bg_stage3, border_color=c_border_stage3, border_width=1.6, boxstyle="round,pad=0.2", zorder=1)
    draw_card(8.15, 8.05, 3.3, 0.32, bg_color='#fef3c7', border_color=c_border_stage3, border_width=1.0, boxstyle="round,pad=0.08", zorder=2)
    ax.text(9.8, 8.21, "STAGE 3: ATTACK CLASSIFICATION", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage3)

    # Stage 4 Panel
    draw_card(11.8, panel_y, 3.7, panel_h, bg_color=c_bg_stage4, border_color=c_border_stage4, border_width=1.6, boxstyle="round,pad=0.2", zorder=1)
    draw_card(11.95, 8.05, 3.4, 0.32, bg_color='#dcfce7', border_color=c_border_stage4, border_width=1.0, boxstyle="round,pad=0.08", zorder=2)
    ax.text(13.65, 8.21, "STAGE 4: SOC XAI & DRIFT", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage4)

    # ==================== 3. STAGE 1 ELEMENTS ====================
    # 1.1 Network Stream
    draw_card(0.7, 6.20, 3.1, 1.60, bg_color=c_card_bg, border_color='#94a3b8')
    ax.text(2.25, 7.50, "Network Traffic Ingestion", ha='center', va='center', fontsize=9.2, fontweight='bold', color=c_text_dark)
    ax.text(2.25, 6.85, "• Raw PCAP / Real-Time Socket Stream\n• Bidirectional Flow Aggregation\n• 78 Statistical Features (CICFlowMeter)\n• CSE-CIC-IDS2018 & NSL-KDD",
            ha='center', va='center', fontsize=7.2, color=c_text_muted, linespacing=1.35)

    draw_arrow(2.25, 6.20, 2.25, 5.55, color='#475569')

    # 1.2 Cryptographic Deduplication
    draw_card(0.7, 3.85, 3.1, 1.70, bg_color='#fff1f2', border_color='#e11d48', border_width=1.5)
    ax.text(2.25, 5.25, "Cryptographic Deduplication", ha='center', va='center', fontsize=9.2, fontweight='bold', color='#be123c')
    ax.text(2.25, 4.50, "• SHA-256 Flow Hashing & Verification\n• Purged 373,620 Duplicate Records\n• Invariant Enforced: Train ∩ Test = ∅\n• Strict Temporal Split (70/15/15)",
            ha='center', va='center', fontsize=7.2, color='#881337', linespacing=1.35)

    draw_arrow(2.25, 3.85, 2.25, 3.20, color='#475569')

    # 1.3 Feature Preprocessing
    draw_card(0.7, 1.45, 3.1, 1.75, bg_color=c_card_bg, border_color='#94a3b8')
    ax.text(2.25, 2.90, "Feature Preprocessing", ha='center', va='center', fontsize=9.2, fontweight='bold', color=c_text_dark)
    ax.text(2.25, 2.15, "• StandardScaler (78 Numerical Features)\n• Categorical OneHotEncoding\n• Transformers Fitted STRICTLY on Train\n• Zero Test Distribution Information Exposure",
            ha='center', va='center', fontsize=7.2, color=c_text_muted, linespacing=1.35)

    # Connector: Stage 1 Preprocessing -> Stage 2 Autoencoder (Clean Orthogonal Pathway)
    draw_elbow_arrow([(3.8, 2.32), (4.08, 2.32), (4.08, 6.90), (4.4, 6.90)], color='#2563eb', width=1.6)
    ax.text(4.08, 4.60, "Standardized\nFlow x ∈ ℝ⁷⁸", ha='center', va='center', fontsize=7.0, fontweight='bold', color='#1d4ed8',
            bbox=dict(boxstyle="round,pad=0.2", fc="#eff6ff", ec="#bfdbfe", lw=0.8))

    # ==================== 4. STAGE 2 ELEMENTS ====================
    # 2.1 Deep Autoencoder
    draw_card(4.4, 6.00, 3.2, 1.80, bg_color=c_card_bg, border_color=c_border_stage2, border_width=1.5)
    ax.text(6.0, 7.50, "Deep Symmetric Autoencoder", ha='center', va='center', fontsize=9.2, fontweight='bold', color='#1d4ed8')
    ax.text(6.0, 6.75, "• Trained Exclusively on Benign Flows\n• Encoder: 78 → 128 → 64 → 32 → 16 (Latent)\n• Decoder: 16 → 32 → 64 → 128 → 78\n• Loss: MSE  |  Optimizer: Adam (η=0.0005)",
            ha='center', va='center', fontsize=7.2, color=c_text_muted, linespacing=1.35)

    draw_arrow(6.0, 6.00, 6.0, 5.35, color='#2563eb')

    # 2.2 Reconstruction Error
    draw_card(4.4, 4.10, 3.2, 1.25, bg_color=c_card_bg, border_color=c_border_stage2)
    ax.text(6.0, 5.05, "Reconstruction Error RE(x)", ha='center', va='center', fontsize=9.2, fontweight='bold', color=c_text_dark)
    ax.text(6.0, 4.50, "RE(x) = (1/d) Σᵢ (xᵢ - x̂ᵢ)²\nBenign Mean: 0.049  |  Attack Mean: 0.228",
            ha='center', va='center', fontsize=7.2, color=c_text_muted, linespacing=1.35)

    draw_arrow(6.0, 4.10, 6.0, 3.45, color='#2563eb')

    # 2.3 Decision Gate
    draw_card(4.5, 1.95, 3.0, 1.50, bg_color='#eff6ff', border_color='#1d4ed8', border_width=1.8)
    ax.text(6.0, 3.15, "STAGE I DECISION GATE", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#1e40af')
    ax.text(6.0, 2.70, "Is RE(x) > τ* ?", ha='center', va='center', fontsize=10.5, fontweight='bold', color='#b91c1c')
    ax.text(6.0, 2.25, "Optimal Cutoff: τ* = 0.1973 (Youden's J)\n(Resolves μ+3σ Zero-Recall Failure)",
            ha='center', va='center', fontsize=7.0, color='#1e3a8a', linespacing=1.3)

    # Branch A: Normal Traffic (Down)
    draw_arrow(6.0, 1.95, 6.0, 1.45, color='#16a34a', width=1.5)
    ax.text(6.35, 1.70, "RE ≤ τ*", ha='left', va='center', fontsize=7.2, fontweight='bold', color='#15803d')

    draw_card(4.4, 0.70, 3.2, 0.75, bg_color='#f0fdf4', border_color='#16a34a', border_width=1.2)
    ax.text(6.0, 1.18, "Normal Traffic Cleared (89.97%)", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#15803d')
    ax.text(6.0, 0.90, "Passed to Safe Operational Buffer (W=500)", ha='center', va='center', fontsize=6.8, color='#166534')

    # Branch B: Candidate Anomaly (Right to Stage 3)
    draw_arrow(7.5, 2.70, 8.2, 2.70, color='#b91c1c', width=1.8)
    ax.text(7.85, 2.95, "RE > τ*\nCandidate\nAnomaly", ha='center', va='center', fontsize=7.0, fontweight='bold', color='#b91c1c')

    # ==================== 5. STAGE 3 ELEMENTS ====================
    # 3.1 Multi-Class XGBoost Classifier
    draw_card(8.2, 1.95, 3.2, 1.50, bg_color=c_card_bg, border_color=c_border_stage3, border_width=1.5)
    ax.text(9.8, 3.15, "Multi-Class XGBoost Classifier", ha='center', va='center', fontsize=9.0, fontweight='bold', color='#b45309')
    ax.text(9.8, 2.50, "• T=500 Trees, Depth=6, η=0.03\n• Objective: multi:softprob\n• Gated: Evaluates ONLY Anomalies (~10%)\n• XGBoost Standalone Latency: 0.0035 ms",
            ha='center', va='center', fontsize=7.0, color=c_text_muted, linespacing=1.35)

    draw_arrow(9.8, 3.45, 9.8, 4.10, color='#d97706')

    # 3.2 Confidence Check
    draw_card(8.3, 4.10, 3.0, 1.25, bg_color='#fef3c7', border_color='#d97706', border_width=1.6)
    ax.text(9.8, 5.05, "STAGE II CONFIDENCE CHECK", ha='center', va='center', fontsize=8.6, fontweight='bold', color='#92400e')
    ax.text(9.8, 4.65, "max_c P(y=c | x) ≥ δ_conf ?", ha='center', va='center', fontsize=9.2, fontweight='bold', color='#92400e')
    ax.text(9.8, 4.30, "Calibrated Threshold: δ_conf = 0.50", ha='center', va='center', fontsize=7.2, color='#78350f')

    # 3.2A High Confidence -> Known Attack
    draw_arrow(9.8, 5.35, 9.8, 6.00, color='#b91c1c')
    ax.text(10.15, 5.68, "≥ 0.50", ha='left', va='center', fontsize=7.2, fontweight='bold', color='#b91c1c')

    draw_card(8.2, 6.00, 3.2, 0.85, bg_color='#fee2e2', border_color='#dc2626', border_width=1.4)
    ax.text(9.8, 6.55, "Classified Known Attack", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#991b1b')
    ax.text(9.8, 6.22, "SSH-Bruteforce (99.72%) | FTP-BruteForce (62.50%)", ha='center', va='center', fontsize=6.8, color='#7f1d1d')

    # 3.2B Low Confidence -> UNKNOWN_ATTACK (Zero-Day)
    draw_elbow_arrow([(8.3, 4.72), (8.12, 4.72), (8.12, 7.42), (8.2, 7.42)], color='#7e22ce', width=1.4)
    ax.text(8.00, 6.00, "< 0.50", ha='right', va='center', fontsize=7.2, fontweight='bold', color='#7e22ce')

    draw_card(8.2, 7.00, 3.2, 0.85, bg_color='#f3e8ff', border_color='#9333ea', border_width=1.4)
    ax.text(9.8, 7.55, "Flagged: UNKNOWN_ATTACK", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#6b21a8')
    ax.text(9.8, 7.22, "Zero-Day Attack Detection (LOAO: 93.11% Recall)", ha='center', va='center', fontsize=6.8, color='#581c87')

    # ==================== 6. STAGE 4 ELEMENTS ====================
    # 4.1 Alert-Gated TreeSHAP
    draw_card(12.0, 4.75, 3.3, 2.95, bg_color=c_card_bg, border_color='#16a34a', border_width=1.5)
    ax.text(13.65, 7.40, "Alert-Gated TreeSHAP Attribution", ha='center', va='center', fontsize=9.0, fontweight='bold', color='#15803d')
    ax.text(13.65, 6.95, "• Evaluated STRICTLY on Threat Alerts\n• Avoids 90% Continuous Line-Rate Cost\n• Explainability Latency: 0.170 ms/alert",
            ha='center', va='center', fontsize=7.0, color=c_text_muted, linespacing=1.35)
    ax.text(13.65, 6.15, "Top Discriminating Attack Features:\n1. Flow Duration    (SHAP: +3.92)\n2. Dst Port         (SHAP: +2.53)\n3. TotLen Fwd Pkts  (SHAP: +2.32)",
            ha='center', va='center', fontsize=6.8, color='#1e293b', linespacing=1.35, family='monospace')
    ax.text(13.65, 5.05, "Top-5 Attribution Jaccard Stability: J = 0.8899\nConsistent Explanations Across Seeds",
            ha='center', va='center', fontsize=7.0, fontweight='bold', color='#15803d')

    # Connections to TreeSHAP from Known & Unknown Attacks
    draw_arrow(11.4, 6.42, 12.0, 6.42, color='#16a34a', width=1.4)
    draw_arrow(11.4, 7.42, 12.0, 7.42, color='#7e22ce', width=1.4)

    # 4.2 Streaming Concept Drift Monitor
    draw_card(12.0, 1.45, 3.3, 3.05, bg_color=c_card_bg, border_color='#0284c7', border_width=1.5)
    ax.text(13.65, 4.20, "Streaming Concept Drift Auditing", ha='center', va='center', fontsize=9.0, fontweight='bold', color='#0369a1')
    ax.text(13.65, 3.75, "• Sliding Verification Window: W = 500\n• Benign Quantile Baseline: q₉₅ Threshold\n• Monitors Non-Stationary Shift in Production",
            ha='center', va='center', fontsize=7.0, color=c_text_muted, linespacing=1.35)
    ax.text(13.65, 2.90, "Statistical Divergence Tests:\n• Kolmogorov-Smirnov (DKS)\n• Population Stability Index (PSI)\n• Jensen-Shannon Divergence (JSD)",
            ha='center', va='center', fontsize=6.8, color='#1e293b', linespacing=1.35)
    ax.text(13.65, 1.85, "Observed Shift: PSI = 0.12 - 0.13\n(Moderate Drift Handled Without Retraining)",
            ha='center', va='center', fontsize=7.0, fontweight='bold', color='#0284c7')

    # Clean bottom pathway from Cleared Benign Traffic to Drift Monitor
    draw_elbow_arrow([(7.6, 1.07), (13.65, 1.07), (13.65, 1.45)], color='#0284c7', width=1.2)
    ax.text(10.6, 0.90, "Continuous Benign Baseline Sampling for Drift Auditing", ha='center', va='center',
            fontsize=6.8, color='#0369a1', fontstyle='italic')

    # Output generation
    fig.tight_layout()

    out1 = os.path.join(os.path.dirname(__file__), "architecture.png")
    fig.savefig(out1, dpi=300, bbox_inches='tight')
    print(f"Generated: {out1}")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out2 = os.path.join(project_root, "Research paper", "architecture.png")
    os.makedirs(os.path.dirname(out2), exist_ok=True)
    fig.savefig(out2, dpi=300, bbox_inches='tight')
    print(f"Generated: {out2}")

    plt.close(fig)

if __name__ == "__main__":
    create_architecture_diagram()
