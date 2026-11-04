import os
import shutil
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

matplotlib.use('Agg')

def build_architecture():
    # Ultra-high definition 300 DPI canvas (18 x 10.5 inches)
    fig, ax = plt.subplots(figsize=(18, 10.5), dpi=300)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10.5)
    ax.axis('off')

    # Color Palette: Modern Cloud Cyber-Defense Theme
    c_bg_stage1 = '#F8FAFC'  # Ingestion
    c_border_stage1 = '#475569'
    c_title_stage1 = '#0F172A'

    c_bg_stage2 = '#F0F9FF'  # Autoencoder
    c_border_stage2 = '#0284C7'
    c_title_stage2 = '#0369A1'

    c_bg_stage3 = '#FFFBEB'  # XGBoost
    c_border_stage3 = '#D97706'
    c_title_stage3 = '#B45309'

    c_bg_stage4 = '#F0FDF4'  # SOC / XAI / Drift
    c_border_stage4 = '#16A34A'
    c_title_stage4 = '#15803D'

    c_card_bg = '#FFFFFF'
    c_text_dark = '#0F172A'
    c_text_muted = '#334155'

    # Helper: draw rounded card
    def card(x, y, w, h, bg=c_card_bg, border='#CBD5E1', bw=1.5, boxstyle="round,pad=0.15", zorder=2):
        box = FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                             facecolor=bg, edgecolor=border,
                             linewidth=bw, zorder=zorder)
        ax.add_patch(box)
        return box

    # Helper: draw arrow
    def arrow(x1, y1, x2, y2, color='#334155', width=1.5, head_w=5.5, head_l=6.5, zorder=4):
        a = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle=f"Simple,tail_width={width},head_width={head_w},head_length={head_l}",
                           color=color, linewidth=0.5, zorder=zorder)
        ax.add_patch(a)

    def elbow_arrow(pts, color='#334155', width=1.5, head_w=5.5, head_l=6.5, zorder=4):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.plot(xs[:-1], ys[:-1], color=color, linewidth=width, zorder=zorder, solid_capstyle='round')
        a = FancyArrowPatch(pts[-2], pts[-1],
                           arrowstyle=f"Simple,tail_width={width},head_width={head_w},head_length={head_l}",
                           color=color, linewidth=0.5, zorder=zorder)
        ax.add_patch(a)

    # ==================== 1. TOP HEADER BANNER ====================
    # Distinctive dark header banner
    card(0.5, 9.40, 17.0, 0.95, bg='#0F172A', border='#1E293B', bw=1.2, boxstyle="round,pad=0.12", zorder=3)
    ax.text(9.0, 9.98, "AI-Based Cloud Network Intrusion Detection System",
            ha='center', va='center', fontsize=13.5, fontweight='bold', color='#FFFFFF')
    ax.text(9.0, 9.68, "Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation",
            ha='center', va='center', fontsize=11.0, fontweight='bold', color='#38BDF8')
    ax.text(9.0, 9.45, "Verified Zero-Leakage (Train ∩ Test = ∅)  |  CPU Line-Rate: 0.183 ms/flow (5,464 flows/s)  |  Peak Footprint: 527.0 MB RSS",
            ha='center', va='center', fontsize=8.2, color='#94A3B8', fontweight='medium')

    # ==================== 2. MAIN FOUR STAGE COLUMNS ====================
    panel_y = 0.50
    panel_h = 8.65

    # Column 1: Ingestion & Cloud Perimeter
    card(0.5, panel_y, 4.0, panel_h, bg=c_bg_stage1, border=c_border_stage1, bw=1.8, boxstyle="round,pad=0.2", zorder=1)
    card(0.65, 8.75, 3.7, 0.35, bg='#E2E8F0', border=c_border_stage1, bw=1.2, boxstyle="round,pad=0.08", zorder=2)
    ax.text(2.5, 8.92, "STAGE 1: CLOUD INGESTION & AUDIT", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage1)

    # Column 2: Lightweight Autoencoder Anomaly Gating
    card(4.7, panel_y, 4.2, panel_h, bg=c_bg_stage2, border=c_border_stage2, bw=1.8, boxstyle="round,pad=0.2", zorder=1)
    card(4.85, 8.75, 3.9, 0.35, bg='#BAE6FD', border=c_border_stage2, bw=1.2, boxstyle="round,pad=0.08", zorder=2)
    ax.text(6.8, 8.92, "STAGE 2: LIGHTWEIGHT AUTOENCODER GATE", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage2)

    # Column 3: Multi-Class XGBoost Classifier
    card(9.1, panel_y, 4.2, panel_h, bg=c_bg_stage3, border=c_border_stage3, bw=1.8, boxstyle="round,pad=0.2", zorder=1)
    card(9.25, 8.75, 3.9, 0.35, bg='#FED7AA', border=c_border_stage3, bw=1.2, boxstyle="round,pad=0.08", zorder=2)
    ax.text(11.2, 8.92, "STAGE 3: XGBOOST ATTACK CLASSIFIER", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage3)

    # Column 4: Alert-Gated XAI & Real-Time Drift
    card(13.5, panel_y, 4.0, panel_h, bg=c_bg_stage4, border=c_border_stage4, bw=1.8, boxstyle="round,pad=0.2", zorder=1)
    card(13.65, 8.75, 3.7, 0.35, bg='#BBF7D0', border=c_border_stage4, bw=1.2, boxstyle="round,pad=0.08", zorder=2)
    ax.text(15.5, 8.92, "STAGE 4: SOC XAI & REAL-TIME DRIFT", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_title_stage4)

    # ==================== 3. COLUMN 1 DETAILS ====================
    # 1.1 Cloud Network Traffic Source
    card(0.7, 6.95, 3.6, 1.65, bg='#FFFFFF', border='#94A3B8')
    ax.text(2.5, 8.35, "Cloud Network Ingestion Tap", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_text_dark)
    ax.text(2.5, 7.65, "• AWS VPC Mirroring / Promiscuous Taps\n• Live Socket Sniffing via Scapy Stream\n• CSE-CIC-IDS2018 (671,131 Clean Flows)\n• NSL-KDD Multi-Class (147,790 Records)",
            ha='center', va='center', fontsize=7.6, color=c_text_muted, linespacing=1.35)

    arrow(2.5, 6.95, 2.5, 6.30, color='#475569')

    # 1.2 Flow Extraction
    card(0.7, 4.70, 3.6, 1.60, bg='#FFFFFF', border='#94A3B8')
    ax.text(2.5, 6.05, "Bidirectional Flow Construction", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_text_dark)
    ax.text(2.5, 5.35, "• 5-Tuple Key: (SrcIP, DstIP, SrcP, DstP, Proto)\n• 78 Statistical Features (CICFlowMeter)\n• Directional Packet & Octet Distributions\n• Forward/Backward Inter-Arrival Times",
            ha='center', va='center', fontsize=7.6, color=c_text_muted, linespacing=1.35)

    arrow(2.5, 4.70, 2.5, 4.05, color='#475569')

    # 1.3 Cryptographic Hygiene & Preprocessing
    card(0.7, 2.45, 3.6, 1.60, bg='#FFFFFF', border='#94A3B8')
    ax.text(2.5, 3.80, "Zero-Leakage Preprocessing", ha='center', va='center', fontsize=9.5, fontweight='bold', color=c_text_dark)
    ax.text(2.5, 3.10, "• SHA-256 / MD5 Deduplication Audit\n• 362 Legacy Cross-Split Rows Removed\n• Strict Invariant: Train ∩ Test = ∅\n• Training-Locked StandardScaler (μ, σ)",
            ha='center', va='center', fontsize=7.6, color=c_text_muted, linespacing=1.35)

    arrow(2.5, 2.45, 2.5, 1.80, color='#475569')

    # 1.4 Normalized Feature Tensor
    card(0.7, 0.70, 3.6, 1.10, bg='#F1F5F9', border='#0284C7', bw=1.8)
    ax.text(2.5, 1.50, "Scaled Feature Vector x ∈ ℝᵈ", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0369A1')
    ax.text(2.5, 1.05, "d = 78 numerical features (CICIDS2018)\nd = 122 one-hot dims (NSL-KDD)",
            ha='center', va='center', fontsize=7.5, color='#334155')

    # Route Column 1 -> Column 2
    arrow(4.3, 1.25, 4.7, 1.25, color='#0284C7', width=2.0)

    # ==================== 4. COLUMN 2: AUTOENCODER ====================
    # 2.1 Symmetric Bottleneck Architecture
    card(4.9, 5.75, 3.8, 2.85, bg='#FFFFFF', border='#0284C7')
    ax.text(6.8, 8.35, "Deep Symmetric Autoencoder", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#0369A1')
    ax.text(6.8, 7.95, "Trained Exclusively on Legitimate Benign Traffic (X_benign)", ha='center', va='center', fontsize=7.2, color='#0F172A', fontweight='bold')

    # Draw mini bottleneck layer boxes
    layers = [
        (5.1, 7.20, 0.65, 0.35, "Input\nd"),
        (5.9, 7.20, 0.65, 0.35, "Enc 1\n128"),
        (6.7, 7.20, 0.65, 0.35, "Enc 2\n64"),
        (7.5, 7.20, 0.65, 0.35, "Enc 3\n32"),
        (8.15, 6.70, 0.45, 0.35, "z:16"),
        (7.5, 6.20, 0.65, 0.35, "Dec 1\n32"),
        (6.7, 6.20, 0.65, 0.35, "Dec 2\n64"),
        (5.9, 6.20, 0.65, 0.35, "Dec 3\n128"),
        (5.1, 6.20, 0.65, 0.35, "Output\nd")
    ]
    for lx, ly, lw, lh, ltxt in layers:
        bg_c = '#38BDF8' if "z:16" in ltxt else '#E0F2FE'
        card(lx, ly, lw, lh, bg=bg_c, border='#0284C7', bw=1.0, zorder=3)
        ax.text(lx+lw/2, ly+lh/2, ltxt, ha='center', va='center', fontsize=6.2, weight='bold', color='#0F172A')

    ax.text(6.8, 5.90, "Adam Optimizer (η=0.0005) | Loss = MSE | Dropout: 0.2", ha='center', va='center', fontsize=7.0, color='#475569')

    arrow(6.8, 5.75, 6.8, 5.15, color='#0284C7')

    # 2.2 Reconstruction Error Formulation
    card(4.9, 3.85, 3.8, 1.30, bg='#FFFFFF', border='#0284C7')
    ax.text(6.8, 4.85, "Reconstruction Error Scoring", ha='center', va='center', fontsize=9.2, fontweight='bold', color=c_text_dark)
    ax.text(6.8, 4.40, r"$e(\mathbf{x}) = \frac{1}{d}\sum_{j=1}^d \left(x_j - \hat{x}_j\right)^2$", ha='center', va='center', fontsize=9.5, color='#0369A1', weight='bold')
    ax.text(6.8, 4.02, "Inference Latency: 0.082 ms/flow | RSS: 384.2 MB", ha='center', va='center', fontsize=7.2, color='#475569')

    arrow(6.8, 3.85, 6.8, 3.25, color='#0284C7')

    # 2.3 Pareto-Optimal Decision Gate
    card(4.9, 1.70, 3.8, 1.55, bg='#FEF3C7', border='#D97706', bw=1.8)
    ax.text(6.8, 3.00, "Validation Youden's J Anomaly Gate", ha='center', va='center', fontsize=9.2, fontweight='bold', color='#B45309')
    ax.text(6.8, 2.55, "Decision Rule: e(x) > τ* ?\nτ* = 0.1973 (CICIDS2018)  |  τ* = 0.0840 (NSL-KDD)", ha='center', va='center', fontsize=7.6, color='#78350F', weight='bold')
    ax.text(6.8, 1.95, "Resolves Gaussian Collapse (μ+3σ: Rec=0.0%)\nRecovers 99.70% Attack Recall", ha='center', va='center', fontsize=7.2, color='#92400E')

    # Decision branches from Gate:
    # Branch A: Normal traffic (e(x) <= tau*) -> Goes DOWN to Benign Clear Card, then to Stage 4 Drift Buffer
    card(4.9, 0.65, 3.8, 0.85, bg='#DCFCE7', border='#16A34A', bw=1.4)
    ax.text(6.8, 1.25, "Benign-Screened Traffic [e(x) ≤ τ*]", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#15803D')
    ax.text(6.8, 0.88, "90.0% of line-rate flows safely cleared", ha='center', va='center', fontsize=7.2, color='#166534')

    arrow(6.8, 1.70, 6.8, 1.50, color='#16A34A')
    ax.text(6.95, 1.60, "≤ τ*", fontsize=7.5, weight='bold', color='#16A34A')

    # Route Benign to Stage 4 Sliding Drift Buffer (elbow across the bottom)
    elbow_arrow([(8.7, 1.05), (13.5, 1.05), (13.5, 2.10)], color='#16A34A', width=1.5)
    ax.text(10.8, 0.85, "Quarantined Benign Stream for Real-Time Drift Update", ha='center', fontsize=7.2, weight='bold', color='#16A34A')

    # Branch B: Anomaly Alert (e(x) > tau*) -> Goes to Stage 3 XGBoost
    arrow(8.7, 2.45, 9.1, 2.45, color='#DC2626', width=2.0)
    ax.text(8.9, 2.65, "> τ*", ha='center', fontsize=8.0, weight='bold', color='#DC2626')

    # ==================== 5. COLUMN 3: XGBOOST ====================
    # 3.1 XGBoost Multi-Class Ensemble
    card(9.3, 5.75, 3.8, 2.85, bg='#FFFFFF', border='#D97706')
    ax.text(11.2, 8.35, "XGBoost Attack Classifier", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#B45309')
    ax.text(11.2, 7.95, "Additive Tree Ensemble (T = 500 Estimators)", ha='center', va='center', fontsize=7.5, color='#92400E', weight='bold')

    # Mini trees
    tree_boxes = [
        (9.5, 7.15, 0.95, 0.55, "Tree 1\ndepth=6"),
        (10.7, 7.15, 0.95, 0.55, "Tree 2\ndepth=6"),
        (11.9, 7.15, 0.95, 0.55, "Tree ...\nη = 0.03"),
        (12.0, 6.45, 0.95, 0.55, "Tree 500\nsub=0.9")
    ]
    for tx, ty, tw, th, ttxt in tree_boxes:
        card(tx, ty, tw, th, bg='#FEF3C7', border='#D97706', bw=1.0, zorder=3)
        ax.text(tx+tw/2, ty+th/2, ttxt, ha='center', va='center', fontsize=6.5, weight='bold', color='#92400E')

    ax.text(11.2, 6.10, "Softmax Multi-Class Probability: P(y = c | x)", ha='center', va='center', fontsize=7.5, color='#78350F', weight='bold')
    ax.text(11.2, 5.85, "Classes: DoS, Probe, R2L, U2R, SSH-Bruteforce", ha='center', va='center', fontsize=6.8, color='#475569')

    arrow(11.2, 2.45, 11.2, 3.35, color='#D97706') # Anomaly in from below

    # 3.2 Confidence & Zero-Day Filter
    card(9.3, 3.35, 3.8, 2.05, bg='#FFFFFF', border='#D97706')
    ax.text(11.2, 5.15, "Tiered Decision & Zero-Day Quarantine", ha='center', va='center', fontsize=9.2, fontweight='bold', color=c_text_dark)
    ax.text(11.2, 4.65, "P*(x) = max_c P(y = c | x)\nConfidence Floor: δ_conf = 0.50", ha='center', va='center', fontsize=7.6, color='#78350F', weight='bold')

    # Two outcome badges
    card(9.45, 3.55, 1.65, 0.70, bg='#FEE2E2', border='#DC2626', bw=1.2, zorder=3)
    ax.text(10.27, 3.90, "P* ≥ 0.50", fontsize=7.5, weight='bold', color='#B91C1C', ha='center')
    ax.text(10.27, 3.70, "Known Attack Vector", fontsize=6.5, color='#991B1B', ha='center')

    card(11.35, 3.55, 1.65, 0.70, bg='#FEF3C7', border='#D97706', bw=1.2, zorder=3)
    ax.text(12.17, 3.90, "P* < 0.50", fontsize=7.5, weight='bold', color='#B45309', ha='center')
    ax.text(12.17, 3.70, "UNKNOWN_ATTACK", fontsize=6.5, weight='bold', color='#92400E', ha='center')

    # Leave-One-Attack-Out validation highlight
    card(9.3, 1.80, 3.8, 1.25, bg='#FEF9C3', border='#CA8A04', bw=1.2)
    ax.text(11.2, 2.75, "Leave-One-Attack-Out (LOAO) Audit", ha='center', va='center', fontsize=8.8, fontweight='bold', color='#854D0E')
    ax.text(11.2, 2.20, "• Unseen DoS Attack Recall: 93.11%\n• Unseen Probe Scan Recall: 82.22%\n• Captures Zero-Day Exploits without labels",
            ha='center', va='center', fontsize=7.2, color='#713F12', linespacing=1.3)

    # Route Column 3 -> Column 4
    arrow(13.1, 4.40, 13.5, 4.40, color='#D97706', width=2.0)

    # ==================== 6. COLUMN 4: XAI & DRIFT ====================
    # 4.1 Alert-Gated TreeSHAP
    card(13.7, 5.75, 3.6, 2.85, bg='#FFFFFF', border='#7C3AED')
    ax.text(15.5, 8.35, "Alert-Gated TreeSHAP", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#6D28D9')
    ax.text(15.5, 7.95, "Selective Invocation Strictly on Anomalies", ha='center', va='center', fontsize=7.5, color='#5B21B6', weight='bold')

    # Top Features mini list
    feat_txt = (
        "Ranked Feature Attributions (log-odds):\n"
        "1. Flow Duration (mean |SHAP| = 3.92)\n"
        "2. Dst Port: 22 SSH / 21 FTP (2.53)\n"
        "3. TotLen Fwd Pkts (2.32)\n"
        "4. Flow IAT Mean (1.90)\n"
        "5. Fwd Header Len (0.66)\n"
        "Attribution Stability: Jaccard J5 = 0.8899"
    )
    ax.text(13.9, 6.75, feat_txt, fontsize=6.8, color='#475569', linespacing=1.25)
    ax.text(15.5, 5.95, "Saves 90% XAI Cost on Normal Flows", ha='center', fontsize=7.0, weight='bold', color='#7C3AED')

    # 4.2 Real-Time Drift Adaptation
    card(13.7, 2.70, 3.6, 2.75, bg='#FFFFFF', border='#16A34A')
    ax.text(15.5, 5.20, "Real-Time Drift Adaptation", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#15803D')
    ax.text(15.5, 4.80, "Sliding Window Buffer: W = 500, q = 95th", ha='center', va='center', fontsize=7.5, color='#166534', weight='bold')

    drift_txt = (
        "• Statistical Drift Tracking across Windows:\n"
        "  - Kolmogorov-Smirnov D_KS = 0.103\n"
        "  - Population Stability Index PSI = 0.126\n"
        "  - Jensen-Shannon JSD = 0.026\n"
        "• Quarantines anomalous attack flows\n"
        "• Prevents threshold baseline poisoning"
    )
    ax.text(13.9, 3.75, drift_txt, fontsize=6.8, color='#334155', linespacing=1.3)

    # 4.3 SOC Streamlit Dashboard
    card(13.7, 0.70, 3.6, 1.70, bg='#0F172A', border='#38BDF8', bw=1.5)
    ax.text(15.5, 2.10, "Cloud SOC Alert & Dashboard", ha='center', va='center', fontsize=9.2, fontweight='bold', color='#38BDF8')
    ax.text(15.5, 1.45, "• Real-Time Threat Counter & Telemetry\n• Interactive SHAP Waterfall Visuals\n• Sub-Millisecond CPU Inference\n• Instant Automated Mitigation Droprules",
            ha='center', va='center', fontsize=7.0, color='#E2E8F0', linespacing=1.3)

    arrow(15.5, 5.75, 15.5, 5.45, color='#7C3AED')
    arrow(15.5, 2.70, 15.5, 2.40, color='#16A34A')

    plt.tight_layout()
    
    # Save in multiple locations
    out1 = r"d:\Users\anshp\Final year project\Major-Project\paper\figures\architecture.png"
    out2 = r"d:\Users\anshp\Final year project\Major-Project\report\figures\architecture.png"
    out3 = r"C:\Users\anshp\.gemini\antigravity\brain\c16fdd6f-acd0-4fc0-8631-40969cf19501\architecture.png"
    
    plt.savefig(out1, bbox_inches='tight', dpi=300)
    plt.savefig(out2, bbox_inches='tight', dpi=300)
    try:
        plt.savefig(out3, bbox_inches='tight', dpi=300)
    except Exception as e:
        pass
    plt.close(fig)
    print(f"Successfully generated high-definition architecture diagrams at:\n  {out1}\n  {out2}")

if __name__ == "__main__":
    build_architecture()
