import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def create_simple_architecture_diagram():
    # 16 x 9 inches - vector-quality rasterization at 300 DPI
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Color Palette - IEEE Professional Styling
    c_slate_bg = '#f8fafc'
    c_slate_bd = '#475569'
    c_slate_tx = '#0f172a'

    c_blue_bg = '#eff6ff'
    c_blue_bd = '#2563eb'
    c_blue_tx = '#1e40af'

    c_green_bg = '#f0fdf4'
    c_green_bd = '#16a34a'
    c_green_tx = '#15803d'

    c_amber_bg = '#fffbeb'
    c_amber_bd = '#d97706'
    c_amber_tx = '#92400e'

    c_red_bg = '#fef2f2'
    c_red_bd = '#dc2626'
    c_red_tx = '#991b1b'

    c_purple_bg = '#faf5ff'
    c_purple_bd = '#7e22ce'
    c_purple_tx = '#6b21a8'

    c_teal_bg = '#f0fdfa'
    c_teal_bd = '#0d9488'
    c_teal_tx = '#0f766e'

    c_soc_bg = '#0f172a'
    c_soc_bd = '#1e293b'
    c_soc_tx = '#ffffff'

    # Helper: draw clean rounded box
    def draw_box(x, y, w, h, bg, bd, text, text_color, fontsize=10.0, fontweight='bold', boxstyle="round,pad=0.12", lw=1.5, zorder=2):
        box = FancyBboxPatch((x, y), w, h, boxstyle=boxstyle,
                             facecolor=bg, edgecolor=bd,
                             linewidth=lw, zorder=zorder)
        ax.add_patch(box)
        ax.text(x + w/2.0, y + h/2.0, text, ha='center', va='center',
                fontsize=fontsize, fontweight=fontweight, color=text_color, zorder=zorder+1)
        return box

    # Helper: draw straight arrow
    def draw_arrow(x1, y1, x2, y2, color='#334155', width=1.4, head_w=5.5, head_l=6.5, zorder=4):
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle=f"Simple,tail_width={width},head_width={head_w},head_length={head_l}",
                                color=color, linewidth=0.5, zorder=zorder)
        ax.add_patch(arrow)

    # Helper: draw elbow polyline with arrow
    def draw_elbow(points, color='#334155', width=1.4, head_w=5.5, head_l=6.5, zorder=4):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs[:-1], ys[:-1], color=color, linewidth=width, zorder=zorder, solid_capstyle='round')
        arrow = FancyArrowPatch(points[-2], points[-1],
                                arrowstyle=f"Simple,tail_width={width},head_width={head_w},head_length={head_l}",
                                color=color, linewidth=0.5, zorder=zorder)
        ax.add_patch(arrow)

    # ==================== 1. TOP HEADER BANNER ====================
    draw_box(0.6, 8.15, 14.8, 0.55, '#0f172a', '#0f172a',
             "TWO-STAGE HYBRID NIDS: DATA FLOW ARCHITECTURE", '#ffffff', fontsize=12.0, lw=1)

    # ==================== ROW 1: STAGE I (SCREENING & NORMAL) ====================
    # Stage I Header Pill
    draw_box(0.6, 7.35, 4.4, 0.35, '#e2e8f0', '#64748b',
             "STAGE I: TRAFFIC SCREENING & NORMAL FLOW", '#334155', fontsize=8.5, lw=1.0)

    # Box 1.1: Network Traffic Ingestion
    draw_box(0.6, 5.50, 1.8, 1.40, c_slate_bg, c_slate_bd,
             "Network Traffic\nIngestion", c_slate_tx, fontsize=9.8)

    draw_arrow(2.55, 6.20, 3.65, 6.20, color='#475569')
    ax.text(3.10, 6.45, "Raw Flows", ha='center', va='center', fontsize=8.0, color='#475569', fontweight='semibold')

    # Box 1.2: Flow Feature Extraction
    draw_box(3.8, 5.50, 1.8, 1.40, c_slate_bg, c_slate_bd,
             "Flow Feature\nExtraction", c_slate_tx, fontsize=9.8)

    draw_arrow(5.75, 6.20, 6.85, 6.20, color='#2563eb')
    ax.text(6.30, 6.45, "Features (x)", ha='center', va='center', fontsize=8.0, color='#1d4ed8', fontweight='semibold')

    # Box 1.3: Autoencoder Anomaly Detector
    draw_box(7.0, 5.50, 1.8, 1.40, c_blue_bg, c_blue_bd,
             "Autoencoder\nDetector", c_blue_tx, fontsize=9.8)

    draw_arrow(8.95, 6.20, 10.05, 6.20, color='#2563eb')
    ax.text(9.50, 6.45, "Error RE(x)", ha='center', va='center', fontsize=8.0, color='#1d4ed8', fontweight='semibold')

    # Box 1.4: Anomaly Decision Gate
    draw_box(10.2, 5.50, 2.0, 1.40, '#dbeafe', '#1d4ed8',
             "Anomaly Decision Gate\n(RE > τ*)", '#1e40af', fontsize=9.8, lw=1.8)

    # Box 1.5: Normal Traffic Cleared (Branch Right)
    draw_arrow(12.35, 6.20, 13.35, 6.20, color='#16a34a')
    ax.text(12.85, 6.45, "RE ≤ τ*", ha='center', va='center', fontsize=8.2, color='#15803d', fontweight='bold')

    draw_box(13.5, 5.50, 1.9, 1.40, c_green_bg, c_green_bd,
             "Normal Traffic\n(Cleared)", c_green_tx, fontsize=9.8)

    # Connection: Normal Traffic -> Streaming Drift Monitoring
    draw_arrow(14.45, 5.38, 14.45, 4.70, color='#0d9488')
    ax.text(14.60, 5.04, "Benign Stream", ha='left', va='center', fontsize=7.5, color='#0f766e', fontweight='semibold')

    # Box 1.6: Streaming Concept Drift Monitoring
    draw_box(13.5, 3.85, 1.9, 0.75, c_teal_bg, c_teal_bd,
             "Streaming Drift\nMonitoring", c_teal_tx, fontsize=9.0)

    # Connection: Drift Monitoring -> SOC Dashboard
    draw_arrow(14.45, 3.73, 14.45, 3.20, color='#0d9488')
    ax.text(14.60, 3.47, "Drift Signals", ha='left', va='center', fontsize=7.5, color='#0f766e', fontweight='semibold')

    # ==================== INTER-STAGE CONNECTOR ====================
    # Anomaly Path from Row 1 Decision Gate down, around left margin, into Row 2 XGBoost
    draw_elbow([(11.2, 5.38), (11.2, 4.55), (0.25, 4.55), (0.25, 2.50), (0.50, 2.50)], color='#dc2626', width=1.6)
    ax.text(5.8, 4.80, "RE > τ*  (Candidate Anomalies Forwarded to Stage II)",
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#b91c1c',
            bbox=dict(boxstyle="round,pad=0.25", fc="#fef2f2", ec="#fca5a5", lw=0.9))

    # ==================== ROW 2: STAGE II (CLASSIFICATION & RESPONSE) ====================
    # Stage II Header Pill
    draw_box(0.6, 3.65, 4.8, 0.35, '#fef3c7', '#d97706',
             "STAGE II: ATTACK CLASSIFICATION & SOC RESPONSE", '#92400e', fontsize=8.5, lw=1.0)

    # Box 2.1: XGBoost Attack Classifier
    draw_box(0.6, 1.80, 1.8, 1.40, c_amber_bg, c_amber_bd,
             "XGBoost Multi-Class\nClassifier", c_amber_tx, fontsize=9.8)

    draw_arrow(2.55, 2.50, 3.65, 2.50, color='#d97706')
    ax.text(3.10, 2.75, "P(y|x)", ha='center', va='center', fontsize=8.0, color='#92400e', fontweight='semibold')

    # Box 2.2: Confidence Decision Gate
    draw_box(3.8, 1.80, 1.8, 1.40, '#fef3c7', '#d97706',
             "Confidence Gate\n(max P ≥ δ)", '#92400e', fontsize=9.8, lw=1.8)

    # Branch A: High Confidence -> Known Attack
    draw_elbow([(5.75, 2.75), (6.30, 2.75), (6.30, 3.05), (6.85, 3.05)], color='#dc2626')
    ax.text(6.15, 3.25, "P ≥ δ", ha='right', va='center', fontsize=7.8, color='#b91c1c', fontweight='bold')

    draw_box(7.0, 2.65, 2.1, 0.80, c_red_bg, c_red_bd,
             "Known Attack\nClassification", c_red_tx, fontsize=9.2)

    # Branch B: Low Confidence -> Unknown Attack
    draw_elbow([(5.75, 2.25), (6.30, 2.25), (6.30, 1.95), (6.85, 1.95)], color='#7e22ce')
    ax.text(6.15, 1.75, "P < δ", ha='right', va='center', fontsize=7.8, color='#6b21a8', fontweight='bold')

    draw_box(7.0, 1.55, 2.1, 0.80, c_purple_bg, c_purple_bd,
             "Unknown / Zero-Day\nAttack Alert", c_purple_tx, fontsize=9.2)

    # Connection: Attack alerts to TreeSHAP
    draw_elbow([(9.25, 3.05), (9.75, 3.05), (9.75, 2.75), (10.25, 2.75)], color='#dc2626')
    draw_elbow([(9.25, 1.95), (9.75, 1.95), (9.75, 2.25), (10.25, 2.25)], color='#7e22ce')
    ax.text(9.75, 3.25, "Alerts", ha='center', va='center', fontsize=7.5, color='#991b1b', fontweight='semibold')

    # Box 2.4: Alert-Gated TreeSHAP
    draw_box(10.4, 1.80, 2.0, 1.40, c_green_bg, c_green_bd,
             "Alert-Gated TreeSHAP\nExplainability", c_green_tx, fontsize=9.8)

    draw_arrow(12.55, 2.50, 13.35, 2.50, color='#15803d')
    ax.text(12.95, 2.75, "SHAP", ha='center', va='center', fontsize=8.0, color='#15803d', fontweight='semibold')

    # Box 2.5: SOC Incident Response Dashboard
    draw_box(13.5, 1.65, 1.9, 1.55, c_soc_bg, c_soc_bd,
             "SOC Incident\nResponse\nDashboard", c_soc_tx, fontsize=10.0, lw=1.2)

    # Save outputs
    out1 = os.path.join(os.path.dirname(__file__), "simple_architecture.png")
    fig.savefig(out1, dpi=300, bbox_inches='tight')
    print(f"Generated: {out1}")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out2 = os.path.join(project_root, "Research paper", "simple_architecture.png")
    os.makedirs(os.path.dirname(out2), exist_ok=True)
    fig.savefig(out2, dpi=300, bbox_inches='tight')
    print(f"Generated: {out2}")

    plt.close(fig)

if __name__ == "__main__":
    create_simple_architecture_diagram()
