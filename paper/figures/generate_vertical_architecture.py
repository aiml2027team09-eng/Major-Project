import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

matplotlib.use('Agg')

def build_vertical_architecture():
    # Vertical 8.5 x 13 inches canvas, 300 DPI (fits a portrait page in VTU format)
    fig, ax = plt.subplots(figsize=(9, 13.5), dpi=300)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 13.5)
    ax.axis('off')

    # Color Palette
    c_blue = '#0284C7'
    c_blue_bg = '#F0F9FF'
    c_amber = '#D97706'
    c_amber_bg = '#FFFBEB'
    c_green = '#16A34A'
    c_green_bg = '#F0FDF4'
    c_red = '#DC2626'
    c_red_bg = '#FEF2F2'
    c_card = '#FFFFFF'
    c_dark = '#0F172A'

    def box(x, y, w, h, bg=c_card, border='#94A3B8', bw=1.4, r=0.1, z=2):
        p = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle=f"round,pad={r}",
                           facecolor=bg, edgecolor=border, linewidth=bw, zorder=z)
        ax.add_patch(p)
        return p

    def arrow_down(x, y1, y2, color='#334155', w=1.2, head=5.0):
        a = FancyArrowPatch((x, y1), (x, y2),
                           arrowstyle=f"Simple,tail_width={w},head_width={head},head_length={head+1}",
                           color=color, linewidth=0.5, zorder=4)
        ax.add_patch(a)

    def elbow(pts, color='#334155', w=1.2, head=5.0):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.plot(xs[:-1], ys[:-1], color=color, linewidth=w, zorder=4, solid_capstyle='round')
        a = FancyArrowPatch(pts[-2], pts[-1],
                           arrowstyle=f"Simple,tail_width={w},head_width={head},head_length={head+1}",
                           color=color, linewidth=0.5, zorder=4)
        ax.add_patch(a)

    # 1. Main Title
    box(4.5, 12.85, 8.2, 0.90, bg='#0F172A', border='#1E293B', bw=1.2)
    ax.text(4.5, 13.08, "AI-Based Cloud Network Intrusion Detection System", color='#FFFFFF', fontsize=10.2, weight='bold', ha='center')
    ax.text(4.5, 12.82, "Lightweight Hybrid Autoencoder & XGBoost with Real-Time Drift Adaptation", color='#38BDF8', fontsize=8.2, weight='bold', ha='center')
    ax.text(4.5, 12.60, "Zero-Leakage (Train ∩ Test = ∅) | CPU Latency: 0.183 ms | RAM: 527 MB", color='#94A3B8', fontsize=6.8, ha='center')

    # 2. Input Block
    box(4.5, 11.90, 5.8, 0.65, bg='#F8FAFC', border='#64748B')
    ax.text(4.5, 12.02, "Input: Cloud Network Traffic Stream", fontsize=8.5, weight='bold', ha='center', color=c_dark)
    ax.text(4.5, 11.80, "Raw PCAP / Live Socket Tap (Scapy Promiscuous Ingestion)", fontsize=7.0, color='#475569', ha='center')

    arrow_down(4.5, 11.55, 11.20)

    # 3. Flow Construction & Preprocessing
    box(4.5, 10.75, 6.4, 0.85, bg='#FFFFFF', border='#0284C7', bw=1.5)
    ax.text(4.5, 10.95, "Bidirectional Flow Construction & Preprocessing", fontsize=8.5, weight='bold', ha='center', color='#0369A1')
    ax.text(4.5, 10.70, "78 Numerical Flow Metrics (CICFlowMeter) / 122 Dims (NSL-KDD)", fontsize=7.2, color='#334155', ha='center')
    ax.text(4.5, 10.50, "StandardScaler Fitted Exclusively on Training Set (Zero Leakage)", fontsize=6.8, color='#64748B', ha='center')

    # Split into Two Streams / Columns
    # Left Branch: Stage-1 Autoencoder (x=2.5)
    # Right Branch: Stage-2 XGBoost (x=6.5)
    elbow([(4.5, 10.30), (4.5, 10.05), (2.5, 10.05), (2.5, 9.75)], color='#0284C7')
    elbow([(4.5, 10.30), (4.5, 10.05), (6.5, 10.05), (6.5, 9.75)], color='#D97706')

    # LEFT PANEL: Stage-1 Autoencoder
    box(2.5, 6.75, 3.8, 5.8, bg=c_blue_bg, border=c_blue, bw=1.6, z=1)
    ax.text(2.5, 9.45, "STAGE 1: AUTOENCODER GATE", color='#0369A1', fontsize=8.5, weight='bold', ha='center')

    ae_items = [
        (9.00, "Input Flow Vector x ∈ ℝ⁷⁸", '#FFFFFF'),
        (8.40, "Dense Encoder (128 units, ReLU)\nDropout 0.2 + BatchNorm", '#E0F2FE'),
        (7.70, "Dense Encoder (64 units, ReLU)", '#E0F2FE'),
        (7.15, "Dense Encoder (32 units, ReLU)", '#E0F2FE'),
        (6.55, "Bottleneck Latent Space (z = 16)", '#BAE6FD'),
        (5.95, "Dense Decoder (32 → 64 → 128)", '#E0F2FE'),
        (5.35, "Decoder Output: Reconstructed x̂", '#FFFFFF'),
        (4.70, "Reconstruction Error: e(x) = (1/d) Σ(x_j - x̂_j)²", '#FEF08A'),
    ]
    for ypos, txt, bcolor in ae_items:
        h = 0.50 if "\n" in txt else 0.40
        box(2.5, ypos, 3.4, h, bg=bcolor, border='#0284C7', bw=1.0, z=2)
        ax.text(2.5, ypos, txt, fontsize=6.5, weight='bold', ha='center', va='center', color=c_dark)
        if ypos > 4.70:
            arrow_down(2.5, ypos - h/2 - 0.02, ypos - 0.58 + 0.20, color='#0284C7', w=0.8, head=4.0)

    # Anomaly Gate Decision
    box(2.5, 4.05, 3.4, 0.65, bg='#FEF3C7', border='#D97706', bw=1.5, z=2)
    ax.text(2.5, 4.20, "Pareto-Optimal Anomaly Gate", fontsize=7.5, weight='bold', ha='center', color='#B45309')
    ax.text(2.5, 3.95, "e(x) > τ* ? (τ*=0.1973 CICIDS / 0.0840 KDD)", fontsize=6.6, color='#78350F', ha='center', weight='bold')

    arrow_down(2.5, 4.48, 4.38, color='#D97706', w=1.0)

    # Left Outcome: Benign Screened
    box(1.5, 3.05, 1.8, 0.70, bg='#DCFCE7', border='#16A34A', bw=1.2, z=2)
    ax.text(1.5, 3.22, "e(x) ≤ τ*", fontsize=7.2, weight='bold', color='#15803D', ha='center')
    ax.text(1.5, 3.02, "Benign-Screened\n(90% traffic cleared)", fontsize=6.2, color='#166534', ha='center')

    elbow([(2.5, 3.72), (2.5, 3.50), (1.5, 3.50), (1.5, 3.42)], color='#16A34A', w=1.0)

    # Right Outcome from Gate: Anomaly Trigger -> Route to Stage 2
    elbow([(2.5, 3.72), (2.5, 3.50), (3.8, 3.50), (3.8, 6.75), (4.7, 6.75)], color='#DC2626', w=1.5, head=5.5)
    ax.text(3.3, 3.62, "e(x) > τ*", fontsize=7.0, weight='bold', color='#DC2626')

    # RIGHT PANEL: Stage-2 XGBoost
    box(6.5, 6.75, 3.8, 5.8, bg=c_amber_bg, border=c_amber, bw=1.6, z=1)
    ax.text(6.5, 9.45, "STAGE 2: XGBOOST ATTACK CLASSIFIER", color='#B45309', fontsize=8.2, weight='bold', ha='center')

    xgb_items = [
        (9.00, "Flagged Anomaly Flow Vector", '#FFFFFF'),
        (8.35, "Additive Tree Ensemble (T = 500)\nMax Depth = 6, η = 0.03, Subsample = 0.9", '#FEF3C7'),
        (7.60, "Regularized Multi-Class Log-Loss Objective", '#FEF3C7'),
        (6.95, "Softmax Probability Vector: P(y = c | x)", '#FFFFFF'),
        (6.25, "Confidence Floor Check: P* ≥ 0.50 ?", '#FEF9C3'),
    ]
    for ypos, txt, bcolor in xgb_items:
        h = 0.50 if "\n" in txt else 0.40
        box(6.5, ypos, 3.4, h, bg=bcolor, border='#D97706', bw=1.0, z=2)
        ax.text(6.5, ypos, txt, fontsize=6.5, weight='bold', ha='center', va='center', color=c_dark)
        if ypos > 6.25:
            arrow_down(6.5, ypos - h/2 - 0.02, ypos - 0.58 + 0.20, color='#D97706', w=0.8, head=4.0)

    # Outcomes of Confidence Check
    box(5.5, 5.30, 1.7, 0.70, bg='#FEE2E2', border='#DC2626', bw=1.2, z=2)
    ax.text(5.5, 5.48, "P* ≥ 0.50", fontsize=7.0, weight='bold', color='#B91C1C', ha='center')
    ax.text(5.5, 5.25, "Known Attack\n(DoS, Probe, SSH)", fontsize=6.0, color='#991B1B', ha='center')

    box(7.5, 5.30, 1.7, 0.70, bg='#FEF3C7', border='#D97706', bw=1.2, z=2)
    ax.text(7.5, 5.48, "P* < 0.50", fontsize=7.0, weight='bold', color='#B45309', ha='center')
    ax.text(7.5, 5.25, "UNKNOWN_ATTACK\n(Zero-Day Quarantine)", fontsize=6.0, weight='bold', color='#92400E', ha='center')

    elbow([(6.5, 6.02), (6.5, 5.80), (5.5, 5.80), (5.5, 5.67)], color='#DC2626', w=1.0)
    elbow([(6.5, 6.02), (6.5, 5.80), (7.5, 5.80), (7.5, 5.67)], color='#D97706', w=1.0)

    # LOAO Performance Badge
    box(6.5, 4.30, 3.4, 0.75, bg='#FEF08A', border='#CA8A04', bw=1.2, z=2)
    ax.text(6.5, 4.48, "LOAO Unseen Attack Recall", fontsize=7.2, weight='bold', color='#854D0E', ha='center')
    ax.text(6.5, 4.25, "DoS: 93.11% | Probe: 82.22% | U2R: 50.55%", fontsize=6.4, color='#713F12', ha='center')

    # Merge Outcomes into Stage 3 / 4
    # 4. Alert-Gated TreeSHAP Attribution
    box(4.5, 2.30, 6.2, 0.85, bg='#EDE9FE', border='#7C3AED', bw=1.5, z=2)
    ax.text(4.5, 2.52, "STAGE 3: ALERT-GATED TREESHAP EXPLAINABILITY", fontsize=8.2, weight='bold', ha='center', color='#6D28D9')
    ax.text(4.5, 2.30, "Attribution Computed Strictly on Flagged Anomaly Alerts (RE > τ*)", fontsize=6.8, color='#5B21B6', ha='center')
    ax.text(4.5, 2.10, "Top Contributor: Flow Duration (3.92) | Dst Port (2.53) | TotLen Fwd Pkts (2.32)", fontsize=6.4, color='#4C1D95', ha='center')

    elbow([(5.5, 4.93), (5.5, 2.75)], color='#DC2626', w=1.2)
    elbow([(7.5, 4.93), (7.5, 2.75)], color='#D97706', w=1.2)

    # Real-Time Drift Buffer Connection from Benign Card
    box(1.5, 1.40, 2.4, 0.85, bg=c_green_bg, border=c_green, bw=1.4, z=2)
    ax.text(1.5, 1.62, "Real-Time Drift Buffer", fontsize=7.5, weight='bold', ha='center', color='#15803D')
    ax.text(1.5, 1.40, "Sliding Window: W = 500, q = 95th", fontsize=6.2, color='#166534', ha='center')
    ax.text(1.5, 1.20, "D_KS = 0.103 | PSI = 0.126 (Stable)", fontsize=6.0, color='#14532D', ha='center')

    arrow_down(1.5, 2.68, 1.85, color='#16A34A', w=1.2)

    # 5. Final Stage: Cloud SOC Alerting & Streamlit Dashboard
    box(5.8, 1.20, 4.8, 1.05, bg='#0F172A', border='#38BDF8', bw=1.6, z=2)
    ax.text(5.8, 1.52, "STAGE 4: CLOUD SOC STREAMLIT DASHBOARD", fontsize=8.2, weight='bold', ha='center', color='#38BDF8')
    ax.text(5.8, 1.30, "Throughput: 5,464 flows/sec | End-to-End Latency: 0.1830 ms/flow", fontsize=6.8, color='#FFFFFF', ha='center')
    ax.text(5.8, 1.10, "Peak Memory: 527.0 MB RSS | Automated Mitigation Drop Rules", fontsize=6.4, color='#94A3B8', ha='center')

    arrow_down(4.5, 1.85, 1.75, color='#7C3AED', w=1.2)
    elbow([(1.5, 0.95), (1.5, 0.65), (5.8, 0.65)], color='#16A34A', w=1.0)
    ax.text(3.5, 0.50, "Dynamic Baseline Health Feed", fontsize=6.2, color='#16A34A', weight='bold')

    plt.tight_layout()
    out1 = r"d:\Users\anshp\Final year project\Major-Project\paper\figures\vertical_architecture.png"
    out2 = r"d:\Users\anshp\Final year project\Major-Project\report\figures\vertical_architecture.png"
    plt.savefig(out1, bbox_inches='tight', dpi=300)
    plt.savefig(out2, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print("Successfully generated vertical_architecture.png")

if __name__ == "__main__":
    build_vertical_architecture()
