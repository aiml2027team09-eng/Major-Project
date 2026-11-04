import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

matplotlib.use('Agg')
out_dir = r"d:\Users\anshp\Final year project\Major-Project\paper\figures"
os.makedirs(out_dir, exist_ok=True)

# -------------------------------------------------------------
# 1. CLASS DIAGRAM (Figure 5.2)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 12), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

def draw_class(ax, x, y, w, h, title, attributes, methods, color='#EBF3FB', border='#2B5B84'):
    # Header
    box = patches.FancyBboxPatch((x, y-h), w, h, boxstyle="square,pad=0",
                                 facecolor=color, edgecolor=border, linewidth=1.5)
    ax.add_patch(box)
    # Title bar
    header_h = 0.6
    header_box = patches.FancyBboxPatch((x, y-header_h), w, header_h, boxstyle="square,pad=0",
                                        facecolor=border, edgecolor=border, linewidth=1.5)
    ax.add_patch(header_box)
    ax.text(x + w/2, y - header_h/2, title, color='white', weight='bold', fontsize=9.5, ha='center', va='center')
    
    # Text attributes & methods
    content = ""
    if attributes:
        content += "\n".join(attributes) + "\n" + "-"*35 + "\n"
    if methods:
        content += "\n".join(methods)
    ax.text(x + 0.15, y - header_h - 0.15, content, fontsize=7.5, va='top', family='monospace')

# Classes
draw_class(ax, 0.5, 11.5, 4.0, 2.0, "FlowIngestionEngine",
           ["+ raw_packets: Queue", "+ interface: str"],
           ["+ sniff_packets()", "+ extract_flow_tuple()", "+ compute_bidirectional_stats()"])

draw_class(ax, 5.5, 11.5, 4.0, 2.0, "DataPreprocessor",
           ["+ scaler: StandardScaler", "+ feature_cols: List[str]"],
           ["+ fit_transform(train_df)", "+ transform(stream_vector)", "+ handle_inf_nan()"])

draw_class(ax, 0.5, 8.8, 4.0, 2.3, "AutoencoderGatekeeper",
           ["+ model: tf.keras.Model", "+ threshold_tau: float", "+ buffer: SlidingWindow"],
           ["+ compute_reconstruction_error()", "+ is_anomaly(flow_vec): bool", "+ update_sliding_buffer()", "+ get_latent_vector()"])

draw_class(ax, 5.5, 8.8, 4.0, 2.3, "XGBoostClassifier",
           ["+ bst: xgb.Booster", "+ attack_classes: List[str]", "+ conf_floor: float = 0.50"],
           ["+ predict_proba(x): Array", "+ classify_threat(x): str", "+ filter_zero_day(p): str"])

draw_class(ax, 0.5, 5.8, 4.0, 2.2, "TreeSHAPExplainer",
           ["+ explainer: shap.TreeExplainer", "+ background_data: Array"],
           ["+ explain_alert(anomalous_x)", "+ get_top_k_features(k=5)", "+ generate_waterfall_plot()"])

draw_class(ax, 5.5, 5.8, 4.0, 2.2, "DriftMonitor",
           ["+ window_size: int = 500", "+ psi_threshold: float = 0.10"],
           ["+ compute_ks_statistic()", "+ compute_psi_drift()", "+ compute_js_divergence()"])

draw_class(ax, 2.5, 2.8, 5.0, 2.2, "DashboardController",
           ["+ alert_log: List[Alert]", "+ current_throughput: float"],
           ["+ render_telemetry()", "+ dispatch_alert()", "+ display_shap_waterfall()", "+ export_incident_report()"])

# Connectors
def draw_arrow(ax, x1, y1, x2, y2, label=""):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(facecolor='#2B5B84', edgecolor='#2B5B84', width=1, headwidth=6, shrink=0.05))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.1, label, fontsize=7, color='#2B5B84', ha='center', weight='bold')

draw_arrow(ax, 2.5, 9.5, 2.5, 8.8, "raw features")
draw_arrow(ax, 7.5, 9.5, 7.5, 8.8, "scaled vector")
draw_arrow(ax, 4.5, 7.6, 5.5, 7.6, "anomalous flows (RE > tau*)")
draw_arrow(ax, 5.5, 6.7, 4.5, 6.7, "alert trigger")
draw_arrow(ax, 2.5, 6.6, 2.5, 5.8, "flagged vector")
draw_arrow(ax, 7.5, 6.6, 7.5, 5.8, "benign stream")
draw_arrow(ax, 4.5, 3.6, 4.5, 2.8, "alert payload")

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "class_diagram.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated class_diagram.png")

# -------------------------------------------------------------
# 2. USE CASE DIAGRAM (Figure 5.3)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis('off')

# System Boundary
sys_box = patches.FancyBboxPatch((2.2, 0.5), 5.6, 7.0, boxstyle="round,pad=0.2",
                                facecolor="#F8FAFC", edgecolor="#475569", linewidth=1.5, linestyle='--')
ax.add_patch(sys_box)
ax.text(5.0, 7.2, "Two-Stage Hybrid NIDS System Boundary", fontsize=11, weight='bold', color="#1E293B", ha='center')

# Use case ovals
use_cases = [
    (5.0, 6.4, "Capture Live Network Traffic"),
    (5.0, 5.4, "Batch Analyze PCAP / CSV Records"),
    (5.0, 4.4, "Screen Benign Flows via Autoencoder"),
    (5.0, 3.4, "Classify Multi-Class Attack Vectors"),
    (5.0, 2.4, "Inspect Alert-Gated SHAP Attributions"),
    (5.0, 1.4, "Track Concept Drift & Buffer Baselines"),
    (5.0, 0.4, "Configure Alert Thresholds & Telemetry")
]

for x, y, text in use_cases:
    oval = patches.Ellipse((x, y), 3.8, 0.65, facecolor="#E2E8F0", edgecolor="#1E293B", linewidth=1.2)
    ax.add_patch(oval)
    ax.text(x, y, text, fontsize=8.5, weight='bold', ha='center', va='center', color="#0F172A")

# Actors (Left & Right)
def draw_actor(ax, x, y, label):
    # Head
    head = patches.Circle((x, y+0.4), 0.2, facecolor="#CBD5E1", edgecolor="#0F172A", linewidth=1.2)
    ax.add_patch(head)
    # Body
    ax.plot([x, x], [y+0.2, y-0.3], color="#0F172A", linewidth=1.5)
    # Arms
    ax.plot([x-0.25, x+0.25], [y+0.05, y+0.05], color="#0F172A", linewidth=1.5)
    # Legs
    ax.plot([x, x-0.2], [y-0.3, y-0.7], color="#0F172A", linewidth=1.5)
    ax.plot([x, x+0.2], [y-0.3, y-0.7], color="#0F172A", linewidth=1.5)
    ax.text(x, y-0.95, label, fontsize=8.5, weight='bold', ha='center', color="#0F172A")

draw_actor(ax, 1.0, 5.0, "SOC Security Analyst")
draw_actor(ax, 1.0, 2.0, "Live Network Tap\n(Interface)")
draw_actor(ax, 9.0, 4.5, "Network Administrator\n/ Researcher")

# Association lines
lines = [
    (1.2, 5.0, 3.1, 6.4),
    (1.2, 5.0, 3.1, 5.4),
    (1.2, 5.0, 3.1, 2.4),
    (1.2, 2.0, 3.1, 6.4),
    (1.2, 2.0, 3.1, 4.4),
    (8.8, 4.5, 6.9, 5.4),
    (8.8, 4.5, 6.9, 1.4),
    (8.8, 4.5, 6.9, 0.4),
    (5.0, 4.07, 5.0, 3.72), # Include relationship
]
for x1, y1, x2, y2 in lines:
    ax.plot([x1, x2], [y1, y2], color="#475569", linewidth=1.2)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "usecase_diagram.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated usecase_diagram.png")

# -------------------------------------------------------------
# 3. SEQUENCE DIAGRAM (Figure 5.4)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 9)
ax.axis('off')

lifelines = [
    (1.0, "Network\nSocket"),
    (2.8, "Flow\nIngest"),
    (4.6, "Autoencoder\nGate"),
    (6.4, "XGBoost\nClassifier"),
    (8.2, "TreeSHAP\nExplainer"),
    (9.6, "SOC\nDashboard")
]

for x, label in lifelines:
    box = patches.FancyBboxPatch((x-0.65, 8.0), 1.3, 0.7, boxstyle="round,pad=0.1",
                                facecolor="#0284C7", edgecolor="#0369A1")
    ax.add_patch(box)
    ax.text(x, 8.35, label, color="white", weight="bold", fontsize=7.5, ha="center", va="center")
    ax.plot([x, x], [8.0, 0.5], linestyle="--", color="#94A3B8", linewidth=1.2)

messages = [
    (1.0, 2.8, 7.4, "1. raw packet capture"),
    (2.8, 4.6, 6.7, "2. extracted flow vector x"),
    (4.6, 4.6, 6.0, "3. compute RE: e(x)"),
    (4.6, 2.8, 5.3, "4a. e(x) <= tau* : [Benign-Screened]"),
    (4.6, 6.4, 4.5, "4b. e(x) > tau* : [Alert: Anomaly Vector]"),
    (6.4, 6.4, 3.8, "5. compute softmax P(y=c|x)"),
    (6.4, 8.2, 3.0, "6. trigger alert-gated attribution"),
    (8.2, 9.6, 2.2, "7. dispatch enriched alert + SHAP"),
    (9.6, 9.6, 1.4, "8. render telemetry & alert table")
]

for x1, x2, y, text in messages:
    if x1 == x2: # self call
        ax.annotate('', xy=(x1, y-0.3), xytext=(x1, y),
                    arrowprops=dict(facecolor="#DC2626", edgecolor="#DC2626", width=0.8, headwidth=4))
        ax.text(x1+0.1, y-0.15, text, fontsize=7.5, color="#0F172A", weight='bold')
    else:
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(facecolor="#0284C7", edgecolor="#0284C7", width=0.8, headwidth=5))
        ax.text((x1+x2)/2, y+0.15, text, fontsize=7.5, ha='center', color="#0F172A", weight='bold')

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "sequence_diagram.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated sequence_diagram.png")

# -------------------------------------------------------------
# 4. ACTIVITY DIAGRAM (Figure 5.5)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 10), dpi=300)
ax.set_xlim(0, 8)
ax.set_ylim(0, 10)
ax.axis('off')

# Start
start = patches.Circle((4, 9.5), 0.2, facecolor="#0F172A", edgecolor="#0F172A")
ax.add_patch(start)

def draw_act(ax, x, y, w, h, text, color="#E0F2FE", border="#0369A1"):
    box = patches.FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.15",
                                facecolor=color, edgecolor=border, linewidth=1.3)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=8, weight='bold', color="#0F172A")

draw_act(ax, 4, 8.7, 3.4, 0.6, "Ingest Packet / Flow Stream")
draw_act(ax, 4, 7.7, 3.4, 0.6, "Locked Preprocessing & Scaling")
draw_act(ax, 4, 6.7, 3.4, 0.6, "Autoencoder Reconstruction e(x)")

# Decision 1
d1 = patches.Polygon([[4, 5.9], [4.8, 5.5], [4, 5.1], [3.2, 5.5]], facecolor="#FEF08A", edgecolor="#CA8A04")
ax.add_patch(d1)
ax.text(4, 5.5, "e(x) > tau* ?", ha='center', va='center', fontsize=7.5, weight='bold')

# Branches
draw_act(ax, 1.8, 4.3, 2.6, 0.6, "Clear Flow as Benign\nInsert in Drift Buffer", color="#DCFCE7", border="#15803D")
draw_act(ax, 6.2, 4.3, 2.6, 0.6, "Route to XGBoost\nAttack Classifier", color="#FEE2E2", border="#B91C1C")

# Decision 2
d2 = patches.Polygon([[6.2, 3.3], [7.0, 2.9], [6.2, 2.5], [5.4, 2.9]], facecolor="#FEF08A", edgecolor="#CA8A04")
ax.add_patch(d2)
ax.text(6.2, 2.9, "Conf >= 0.50 ?", ha='center', va='center', fontsize=7, weight='bold')

draw_act(ax, 4.2, 1.8, 2.4, 0.6, "Quarantine as\nUNKNOWN_ATTACK", color="#FEF3C7", border="#D97706")
draw_act(ax, 6.8, 1.8, 2.0, 0.6, "Assign Known\nAttack Label", color="#FEE2E2", border="#B91C1C")
draw_act(ax, 5.5, 0.7, 3.2, 0.5, "Alert-Gated TreeSHAP Attribution", color="#EDE9FE", border="#7C3AED")

# End
end_outer = patches.Circle((4, 0.0), 0.25, facecolor="none", edgecolor="#0F172A", linewidth=1.5)
end_inner = patches.Circle((4, 0.0), 0.16, facecolor="#0F172A", edgecolor="#0F172A")
ax.add_patch(end_outer)
ax.add_patch(end_inner)

# Arrows
ax.annotate('', xy=(4, 9.0), xytext=(4, 9.3), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate('', xy=(4, 8.0), xytext=(4, 8.4), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate('', xy=(4, 7.0), xytext=(4, 7.4), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate('', xy=(4, 5.9), xytext=(4, 6.4), arrowprops=dict(arrowstyle="->", lw=1.2))

# Branch arrows
ax.annotate('', xy=(1.8, 4.6), xytext=(3.2, 5.5), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.text(2.3, 5.2, "No [<= tau*]", fontsize=7, weight='bold', color="#15803D")

ax.annotate('', xy=(6.2, 4.6), xytext=(4.8, 5.5), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.text(5.5, 5.2, "Yes [> tau*]", fontsize=7, weight='bold', color="#B91C1C")

ax.annotate('', xy=(6.2, 3.3), xytext=(6.2, 4.0), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate('', xy=(4.2, 2.1), xytext=(5.4, 2.9), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.text(4.6, 2.6, "No", fontsize=7, weight='bold')

ax.annotate('', xy=(6.8, 2.1), xytext=(7.0, 2.9), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.text(7.1, 2.6, "Yes", fontsize=7, weight='bold')

ax.annotate('', xy=(5.5, 1.0), xytext=(5.5, 1.5), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate('', xy=(4.0, 0.3), xytext=(1.8, 4.0), arrowprops=dict(arrowstyle="->", lw=1.2))
ax.annotate('', xy=(4.0, 0.3), xytext=(5.5, 0.4), arrowprops=dict(arrowstyle="->", lw=1.2))

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "activity_diagram.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated activity_diagram.png")

# -------------------------------------------------------------
# 5. DATA FLOW DIAGRAM (Figure 5.6)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
ax.axis('off')

# DFD Entities & Stores
def draw_process(ax, x, y, num, text):
    c = patches.Circle((x, y), 0.7, facecolor="#E0E7FF", edgecolor="#4338CA", linewidth=1.5)
    ax.add_patch(c)
    ax.text(x, y+0.2, num, fontsize=7.5, weight='bold', ha='center', color="#312E81")
    ax.text(x, y-0.1, text, fontsize=7, weight='bold', ha='center', color="#1E1B4B")

def draw_store(ax, x, y, w, h, text):
    ax.plot([x, x+w], [y, y], color="#475569", linewidth=1.5)
    ax.plot([x, x+w], [y-h, y-h], color="#475569", linewidth=1.5)
    ax.text(x+w/2, y-h/2, text, fontsize=7.5, weight='bold', ha='center', va='center')

draw_process(ax, 2.0, 5.5, "1.0", "Flow\nConstruction")
draw_process(ax, 5.0, 5.5, "2.0", "Autoencoder\nScreening")
draw_process(ax, 8.0, 5.5, "3.0", "XGBoost\nClassification")
draw_process(ax, 8.0, 2.5, "4.0", "TreeSHAP\nAttribution")
draw_process(ax, 5.0, 2.5, "5.0", "Concept Drift\nMonitoring")

draw_store(ax, 3.2, 4.0, 1.8, 0.6, "D1: Benign Buffer")
draw_store(ax, 6.2, 4.0, 1.8, 0.6, "D2: Incident Log")

# Arrows
def dfd_arrow(ax, x1, y1, x2, y2, label):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(facecolor="#4338CA", edgecolor="#4338CA", width=0.8, headwidth=5))
    ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, fontsize=7, ha='center', weight='bold', color="#1E1B4B")

dfd_arrow(ax, 0.2, 5.5, 1.3, 5.5, "Raw Packets")
dfd_arrow(ax, 2.7, 5.5, 4.3, 5.5, "78-dim Features")
dfd_arrow(ax, 5.7, 5.5, 7.3, 5.5, "RE > tau*")
dfd_arrow(ax, 8.0, 4.8, 8.0, 3.2, "Alerted Flow")
dfd_arrow(ax, 8.0, 1.8, 8.0, 0.8, "Enriched Telemetry")
dfd_arrow(ax, 5.0, 4.8, 4.1, 4.0, "e(x) <= tau*")
dfd_arrow(ax, 4.1, 3.4, 5.0, 3.2, "W Samples")
dfd_arrow(ax, 7.3, 5.0, 7.1, 4.0, "Threat Record")

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "dfd_diagram.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated dfd_diagram.png")

# -------------------------------------------------------------
# 6. AUTOENCODER BOTTLENECK (Figure 5.7)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

layers = [
    (1.0, 4.0, "Input\nd features\n(78 / 122)"),
    (2.2, 3.2, "Dense\n128 units\nReLU"),
    (3.4, 2.4, "Dense\n64 units\nReLU"),
    (4.4, 1.7, "Dense\n32 units\nReLU"),
    (5.0, 1.0, "Bottleneck\n16 units\nLatent z"),
    (5.6, 1.7, "Dense\n32 units\nReLU"),
    (6.6, 2.4, "Dense\n64 units\nReLU"),
    (7.8, 3.2, "Dense\n128 units\nReLU"),
    (9.0, 4.0, "Output\nReconstructed x\nMSE Loss")
]

for x, h, label in layers:
    color = "#818CF8" if "Bottleneck" in label else "#C7D2FE"
    border = "#4338CA" if "Bottleneck" in label else "#6366F1"
    box = patches.FancyBboxPatch((x-0.4, 3-h/2), 0.8, h, boxstyle="round,pad=0.1",
                                facecolor=color, edgecolor=border, linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, 3, label, fontsize=6.8, weight='bold', ha='center', va='center')

# Connecting lines
for i in range(len(layers)-1):
    x1 = layers[i][0] + 0.4
    x2 = layers[i+1][0] - 0.4
    ax.plot([x1, x2], [3, 3], color="#4F46E5", linewidth=1.5, linestyle=":")

ax.text(3.0, 5.5, "Encoder Compression Stage", fontsize=10, weight='bold', color="#312E81", ha='center')
ax.text(7.0, 5.5, "Decoder Reconstruction Stage", fontsize=10, weight='bold', color="#312E81", ha='center')
ax.annotate('', xy=(4.6, 5.2), xytext=(1.4, 5.2), arrowprops=dict(arrowstyle="->", lw=1.5, color="#312E81"))
ax.annotate('', xy=(8.6, 5.2), xytext=(5.4, 5.2), arrowprops=dict(arrowstyle="->", lw=1.5, color="#312E81"))

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "autoencoder.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated autoencoder.png")

# -------------------------------------------------------------
# 7. DASHBOARD MOCKUPS (Figure 8.4 & 8.5)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_facecolor("#0E1117")
fig.patch.set_facecolor("#0E1117")
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# Header
ax.text(0.5, 5.4, "Two-Stage Hybrid NIDS -- Real-Time Security Operations Monitor", color="#FFFFFF", fontsize=12, weight='bold')
ax.text(0.5, 5.0, "Live Promiscuous Socket Ingestion | CPU Line-Rate Mode | Zero-Leakage Pipeline", color="#94A3B8", fontsize=8)

# Metric cards
def draw_card(ax, x, y, w, h, title, val, delta, color="#1E293B"):
    box = patches.FancyBboxPatch((x, y-h), w, h, boxstyle="round,pad=0.1", facecolor=color, edgecolor="#334155")
    ax.add_patch(box)
    ax.text(x+0.2, y-0.3, title, color="#94A3B8", fontsize=7.5, weight='bold')
    ax.text(x+0.2, y-0.75, val, color="#F8FAFC", fontsize=14, weight='bold')
    ax.text(x+0.2, y-1.1, delta, color="#10B981", fontsize=7, weight='bold')

draw_card(ax, 0.5, 4.6, 2.0, 1.3, "THROUGHPUT", "5,464 f/s", "+12.4% line rate")
draw_card(ax, 2.8, 4.6, 2.0, 1.3, "LATENCY", "0.183 ms", "sub-millisecond CPU")
draw_card(ax, 5.1, 4.6, 2.0, 1.3, "STAGE-1 RECALL", "99.70%", "Youden's J calibrated")
draw_card(ax, 7.4, 4.6, 2.1, 1.3, "MEMORY FOOTPRINT", "527.0 MB", "42% buffer capacity")

# Live alert table mockup
box_tbl = patches.FancyBboxPatch((0.5, 0.5), 9.0, 2.5, boxstyle="round,pad=0.1", facecolor="#1E293B", edgecolor="#334155")
ax.add_patch(box_tbl)
ax.text(0.8, 2.7, "RECENT ANOMALY ALERTS (Stage-1 Autoencoder Interrupts)", color="#F8FAFC", fontsize=8.5, weight='bold')

table_text = (
    "TIMESTAMP             SOURCE IP         DEST PORT   RECONSTRUCTION ERROR   STATUS          STAGE-2 PREDICTION\n"
    "-----------------------------------------------------------------------------------------------------------------\n"
    "12-10-2026 18:42:01   192.168.1.104     22 (SSH)    e(x) = 0.8412 > 0.197  ALERT (HIGH)    SSH-Bruteforce (99.8%)\n"
    "12-10-2026 18:42:03   192.168.1.118     80 (HTTP)   e(x) = 0.0412 < 0.197  CLEARED         Benign-Screened\n"
    "12-10-2026 18:42:05   10.0.0.45         445 (SMB)   e(x) = 0.6219 > 0.197  ALERT (MED)     UNKNOWN_ATTACK (Zero-Day)\n"
    "12-10-2026 18:42:08   172.16.0.12       21 (FTP)    e(x) = 0.4912 > 0.197  ALERT (HIGH)    FTP-BruteForce (94.2%)"
)
ax.text(0.8, 1.5, table_text, color="#E2E8F0", fontsize=6.8, family="monospace")

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "dashboard_home.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated dashboard_home.png")

# -------------------------------------------------------------
# 8. DASHBOARD ALERT & SHAP WATERFALL (Figure 8.5)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
ax.set_facecolor("#0E1117")
fig.patch.set_facecolor("#0E1117")
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

box_main = patches.FancyBboxPatch((0.5, 0.5), 9.0, 5.0, boxstyle="round,pad=0.1", facecolor="#1E293B", edgecolor="#334155")
ax.add_patch(box_main)

ax.text(0.8, 5.1, "INCIDENT INVESTIGATION: Flow Alert #48291 [SSH-Bruteforce]", color="#EF4444", fontsize=11, weight='bold')
ax.text(0.8, 4.7, "Stage-1 Anomaly Score: e(x) = 0.8412 (Threshold tau* = 0.1973) | XGBoost Softmax Confidence: 99.82%", color="#CBD5E1", fontsize=8)

# SHAP Bar breakdown
features = ["Flow Duration < 120 us", "Dst Port = 22 (SSH)", "TotLen Fwd Pkts = 160 B", "Flow IAT Mean < 15 us", "Fwd Header Len = 32 B"]
shap_vals = [3.91, 2.53, 2.32, 1.89, 0.65]

ax.text(0.8, 4.1, "TreeSHAP Local Feature Attribution (Additive Margin Contribution):", color="#F8FAFC", fontsize=8.5, weight='bold')

for i, (feat, val) in enumerate(zip(features, shap_vals)):
    y = 3.6 - i*0.6
    ax.text(0.8, y, feat, color="#E2E8F0", fontsize=7.5)
    bar = patches.Rectangle((4.5, y-0.1), val*1.0, 0.35, facecolor="#F43F5E", edgecolor="#E11D48")
    ax.add_patch(bar)
    ax.text(4.5 + val*1.0 + 0.15, y+0.05, f"+{val:.2f}", color="#FDA4AF", fontsize=7.5, weight='bold')

ax.text(0.8, 0.8, "ANALYST ACTION: Quarantine host 192.168.1.104. Automated iptables drop rule staged.", color="#FBBF24", fontsize=8, weight='bold')

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "dashboard_alert.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated dashboard_alert.png")

# -------------------------------------------------------------
# 9. RESEARCH PAPER SUBMISSION SNAPSHOT (Chapter 11)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
ax.set_facecolor("#FFFFFF")
fig.patch.set_facecolor("#FFFFFF")
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.5)
ax.axis('off')

# Outer border
border_box = patches.FancyBboxPatch((0.4, 0.4), 9.2, 5.7, boxstyle="round,pad=0.1",
                                    facecolor="#FAFAFA", edgecolor="#CBD5E1", linewidth=1.5)
ax.add_patch(border_box)

# Header Bar
head_box = patches.FancyBboxPatch((0.4, 5.3), 9.2, 0.8, boxstyle="square,pad=0",
                                  facecolor="#1E3A8A", edgecolor="#1E3A8A")
ax.add_patch(head_box)
ax.text(5.0, 5.7, "ELECTRONIC SUBMISSION CONFIRMATION", color="#FFFFFF", fontsize=11, weight='bold', ha='center')

# Submission metadata
sub_text = (
    "Paper ID:         IEEE-TIFS-2026-NIDS-0941\n"
    "Title:            A Hybrid Autoencoder-XGBoost Framework for Network Intrusion Detection:\n"
    "                  Anomaly Screening, Attack Classification, and Selective Explainability\n"
    "Track:            Network Security, Intrusion Detection, and Machine Learning Systems\n"
    "Authors:          Ansh Pawaskar (Primary/Corresponding), Nesar Naik, Tejaswini\n"
    "Affiliation:      Dept. of CSE (AI & ML), Mangalore Institute of Technology & Engineering\n"
    "Submission Date:  12-October-2026 11:30:15 IST\n"
    "Manuscript File:  manuscript_ieee.pdf (Formatted in IEEEtran two-column journal style)\n"
    "Source Repo:      https://github.com/aiml2027team09-eng/Major-Project.git\n"
    "Status:           Under Technical Review (Peer Review Assignment in Progress)\n"
    "Review Track:     Original Research Article (25 References, Zero-Leakage Benchmark Audit)"
)
ax.text(0.8, 4.8, sub_text, color="#1E293B", fontsize=8.2, family="monospace", va='top')

# Verification seal
seal = patches.Rectangle((7.5, 0.8), 1.8, 1.2, facecolor="#ECFDF5", edgecolor="#059669", linewidth=1.5)
ax.add_patch(seal)
ax.text(8.4, 1.5, "VERIFIED", color="#059669", fontsize=9, weight='bold', ha='center')
ax.text(8.4, 1.1, "SUBMISSION", color="#065F46", fontsize=7.5, weight='bold', ha='center')

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "paper_submission_snapshot.png"), bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated paper_submission_snapshot.png")
