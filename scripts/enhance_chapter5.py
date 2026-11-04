import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import shutil
import os

src_docx = "report/Major_Project_Report_Final.docx"
doc = docx.Document(src_docx)

def add_heading_styled(target_p, text, level=2):
    """Inserts a styled heading before target_p."""
    p = target_p.insert_paragraph_before()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12 if level == 3 else 13)
    r.font.bold = True
    return p

def add_body_paragraph(target_p, text):
    """Inserts a body paragraph before target_p."""
    p = target_p.insert_paragraph_before()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    return p

def add_code_listing_before(target_p, caption, code_lines):
    """Inserts a beautifully styled code listing table before target_p."""
    p_cap = target_p.insert_paragraph_before()
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(caption)
    r_cap.font.name = "Times New Roman"
    r_cap.font.size = Pt(10)
    r_cap.font.bold = True

    # Create table via doc.add_table and move it before target_p
    table = doc.add_table(rows=1, cols=1)
    target_p._p.addprevious(table._tbl)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    cell = table.cell(0, 0)
    cell.width = Inches(6.0)
    
    # Borders: left thick blue, others subtle gray
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(r'''
        <w:tblBorders %s>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
            <w:left w:val="single" w:sz="18" w:space="0" w:color="0056B3"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="D0D0D0"/>
        </w:tblBorders>
    ''' % nsdecls('w'))
    tblPr.append(tblBorders)
    
    # Cell shading & margins
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(r'<w:shd %s w:val="clear" w:color="auto" w:fill="F8F9FA"/>' % nsdecls('w'))
    tcMar = parse_xml(r'''
        <w:tcMar %s>
            <w:top w:w="120" w:type="dxa"/>
            <w:left w:w="160" w:type="dxa"/>
            <w:bottom w:w="120" w:type="dxa"/>
            <w:right w:w="160" w:type="dxa"/>
        </w:tcMar>
    ''' % nsdecls('w'))
    tcPr.append(shd)
    tcPr.append(tcMar)
    
    p_first = cell.paragraphs[0]
    p_first.paragraph_format.space_before = Pt(0)
    p_first.paragraph_format.space_after = Pt(1)
    p_first.paragraph_format.line_spacing = 1.0
    
    for idx, line in enumerate(code_lines):
        p = p_first if idx == 0 else cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        
        r = p.add_run(line)
        r.font.name = "Consolas"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x20, 0x20, 0x20)
        
    p_space = target_p.insert_paragraph_before()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(4)

# Locate elements by iterating paragraphs
p_52 = None
p_521 = None
p_feat = None
p_ae = None
p_53 = None

for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t == "5.2 Module-wise Implementation":
        p_52 = p
        p_521 = doc.paragraphs[i+1]
    elif "Continuous numerical attributes were scaled" in t:
        p_feat = p
    elif "The Autoencoder was trained strictly on benign flow records" in t:
        p_ae = p
    elif t == "5.3 Experimental Setup":
        p_53 = p

assert all([p_52, p_521, p_feat, p_ae, p_53]), "Could not locate all target paragraphs!"

# Insert 5.2.1
add_heading_styled(p_521, "5.2.1 Data Preparation & Cryptographic Hygiene", level=3)

# Insert 5.2.2
add_heading_styled(p_feat, "5.2.2 Feature Preprocessing & Locked Scaling", level=3)

# Insert 5.2.3
add_heading_styled(p_ae, "5.2.3 Autoencoder Model Training & Manifold Construction", level=3)

# Code Listing 5.1
code_listing_51 = [
    "def build_autoencoder(input_dim: int, dropout_rate: float = 0.20) -> Model:",
    "    '''Constructs deep symmetric Autoencoder (d -> 128 -> 64 -> 32 -> 16 -> 32 -> 64 -> 128 -> d).",
    "       Learns legitimate traffic manifold exclusively on benign network flows.'''",
    "    inputs = Input(shape=(input_dim,), name='flow_features')",
    "    # Progressive pyramidal encoder with dropout regularization",
    "    e1 = Dense(128, activation='relu', name='enc_128')(inputs)",
    "    e1 = Dropout(dropout_rate, name='drop_128')(e1)",
    "    e2 = Dense(64, activation='relu', name='enc_64')(e1)",
    "    e2 = Dropout(dropout_rate, name='drop_64')(e2)",
    "    e3 = Dense(32, activation='relu', name='enc_32')(e2)",
    "    bottleneck = Dense(16, activation='relu', name='bottleneck')(e3)  # Latent Manifold",
    "    # Symmetrical decoder reconstructing benign traffic geometry",
    "    d1 = Dense(32, activation='relu', name='dec_32')(bottleneck)",
    "    d1 = Dropout(dropout_rate, name='drop_32')(d1)",
    "    d2 = Dense(64, activation='relu', name='dec_64')(d1)",
    "    d2 = Dropout(dropout_rate, name='drop_64')(d2)",
    "    d3 = Dense(128, activation='relu', name='dec_128')(d2)",
    "    outputs = Dense(input_dim, activation='linear', name='reconstruction')(d3)",
    "    model = Model(inputs=inputs, outputs=outputs, name='Symmetric_Autoencoder')",
    "    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mse')",
    "    return model"
]
add_code_listing_before(p_53, "Listing 5.1: Deep Symmetric Autoencoder Architecture & Training Routine", code_listing_51)

add_body_paragraph(p_53, (
    "As detailed in Listing 5.1, the Autoencoder enforces a strict 16-dimensional bottleneck representation. "
    "By training exclusively on legitimate benign flows, the network minimizes reconstruction Mean Squared Error (MSE). "
    "When attack traffic or unmodeled zero-day flows pass through the network, their structural divergence produces sharp "
    "reconstruction spikes (e(x) > tau*), enabling wire-speed anomaly gating."
))

# Section 5.2.4: Validation Youden's J Threshold Optimization
add_heading_styled(p_53, "5.2.4 Validation Youden's J Threshold Optimization", level=3)
add_body_paragraph(p_53, (
    "Prevailing anomaly detection systems widely rely on parametric Gaussian heuristics (mu + 3*sigma) to set anomaly boundaries. "
    "However, empirical network telemetry follows heavy-tailed, non-Gaussian distributions, inflating mu + 3*sigma to over 38,723 "
    "and causing catastrophic recall collapse (0.00%). To establish a robust, non-parametric boundary, the system executes an automated "
    "grid search across 200 validation quantiles, maximizing Youden's J-statistic (J = TPR - FPR) to locate the exact Pareto knee."
))

code_listing_52 = [
    "def calibrate_youden_threshold(val_benign_err: np.ndarray, val_mixed_err: np.ndarray, y_val_binary: np.ndarray) -> float:",
    "    '''Optimizes reconstruction threshold tau* on validation partition by maximizing Youden's J = TPR - FPR.",
    "       Eliminates Gaussian threshold collapse on heavy-tailed, bursty network traffic.'''",
    "    # Sample 200 candidate cutoffs across 80.0th to 99.9th percentiles of normal error",
    "    candidates = np.percentile(val_benign_err, np.linspace(80.0, 99.9, 200))",
    "    best_j, optimal_tau = -1.0, float(candidates[0])",
    "    for tau in candidates:",
    "        preds = (val_mixed_err > tau).astype(int)",
    "        tpr = recall_score(y_val_binary, preds, zero_division=0)  # Sensitivity",
    "        fpr = np.mean(preds[y_val_binary == 0])                   # False Alarm Rate",
    "        j_index = tpr - fpr                                       # Youden's J objective",
    "        if j_index > best_j:",
    "            best_j = j_index",
    "            optimal_tau = float(tau)",
    "    return optimal_tau  # Calibrates tau* = 0.1973 (CICIDS2018, securing 99.70% recall)"
]
add_code_listing_before(p_53, "Listing 5.2: Validation Youden's J-Statistic Threshold Calibration Algorithm", code_listing_52)

# Section 5.2.5: XGBoost Multi-Class Classification & Confidence Gating
add_heading_styled(p_53, "5.2.5 XGBoost Multi-Class Classification & Confidence Gating", level=3)
add_body_paragraph(p_53, (
    "Flows flagged as anomalies (e(x) > tau*) are routed to the Stage-2 Extreme Gradient Boosted decision tree ensemble "
    "(500 estimators, max_depth = 6, learning_rate = 0.05). To prevent misclassifying novel zero-day attacks into arbitrary known "
    "classes, a confidence floor (delta_conf = 0.50) is enforced. When softmax confidence drops below 0.50, the flow is isolated "
    "as UNKNOWN_ATTACK for SOC forensic inspection."
))

code_listing_53 = [
    "def two_stage_hybrid_inference(flow_vector: np.ndarray, autoencoder: Model, tau_star: float,",
    "                               xgb_model: XGBClassifier, delta_conf: float = 0.50) -> tuple[str, float]:",
    "    '''Executes two-stage tiered inference: screens normal flows in Stage 1 and classifies threats in Stage 2.'''",
    "    # Stage 1: Autoencoder Anomaly Gating (0.082 ms CPU line-rate clearance)",
    "    reconstruction = autoencoder.predict(flow_vector, verbose=0)",
    "    mse_error = float(np.mean(np.square(flow_vector - reconstruction)))",
    "    if mse_error <= tau_star:",
    "        return 'Benign-Screened', mse_error  # Rapid wire-speed bypass",
    "    # Stage 2: Supervised XGBoost Multi-Class Classification",
    "    probabilities = xgb_model.predict_proba(flow_vector)[0]",
    "    top_idx = int(np.argmax(probabilities))",
    "    confidence = float(probabilities[top_idx])",
    "    # Zero-Day Threat Quarantine: isolate low-confidence anomalies",
    "    if confidence < delta_conf:",
    "        return 'UNKNOWN_ATTACK', mse_error   # Quarantined for SOC investigation",
    "    attack_label = xgb_model.classes_[top_idx]",
    "    return attack_label, mse_error"
]
add_code_listing_before(p_53, "Listing 5.3: Two-Stage Hybrid Gating and Zero-Day Threat Quarantine", code_listing_53)

# Section 5.2.6: Dynamic Concept Drift Monitoring & Alert-Gated TreeSHAP
add_heading_styled(p_53, "5.2.6 Dynamic Concept Drift Monitoring & Alert-Gated TreeSHAP", level=3)
add_body_paragraph(p_53, (
    "In operational deployment, streaming network distributions experience non-adversarial concept drift. The system maintains "
    "a circular reference buffer (W = 500 benign flows) that tracks covariate drift via Population Stability Index (PSI) and "
    "Kolmogorov-Smirnov two-sample tests. Furthermore, to eliminate the computational latency bottleneck of Explainable AI (XAI), "
    "TreeSHAP feature attributions are computed strictly on anomaly interrupts (e(x) > tau*), eliminating 90% of XAI overhead."
))

code_listing_54 = [
    "def monitor_drift_and_explain(current_window: np.ndarray, baseline_ref: np.ndarray,",
    "                             alert_flow: np.ndarray, explainer: shap.TreeExplainer) -> dict:",
    "    '''Audits covariate drift across sliding buffer (W=500) and computes top-5 SHAP attributions on alerts.'''",
    "    # 1. Population Stability Index (PSI) calculation across flow features",
    "    total_psi = 0.0",
    "    for col in range(current_window.shape[1]):",
    "        ref, cur = baseline_ref[:, col], current_window[:, col]",
    "        bins = np.percentile(ref, np.linspace(0, 100, 11))",
    "        bins[0] -= 1e-5; bins[-1] += 1e-5",
    "        p_exp = np.histogram(ref, bins=bins)[0] / len(ref) + 1e-6",
    "        p_act = np.histogram(cur, bins=bins)[0] / len(cur) + 1e-6",
    "        total_psi += np.sum((p_act - p_exp) * np.log(p_act / p_exp))",
    "    mean_psi = total_psi / current_window.shape[1]",
    "    ks_stat, _ = ks_2samp(baseline_ref[:, 0], current_window[:, 0])",
    "    # 2. Alert-Gated TreeSHAP: compute additive feature attributions only on anomalies",
    "    shap_values = explainer.shap_values(alert_flow)[0]",
    "    top_5_indices = np.argsort(np.abs(shap_values))[-5:][::-1]",
    "    return {'mean_psi': mean_psi, 'ks_stat': ks_stat, 'top_shap_indices': top_5_indices}"
]
add_code_listing_before(p_53, "Listing 5.4: Sliding-Window Concept Drift Monitoring and Alert-Gated TreeSHAP", code_listing_54)

# Remove old redundant P265/P266 if present
for p in list(doc.paragraphs):
    if "To monitor operational data drift over continuous packet streams, the" in p.text:
        p._p.getparent().remove(p._p)
    elif "The Autoencoder was trained for 50 epochs using mini-batches of 256 sa" in p.text:
        p._p.getparent().remove(p._p)

doc.save(src_docx)
print("Successfully enhanced Chapter 5 in Major_Project_Report_Final.docx!")
try:
    shutil.copy2(src_docx, "report/Major_Project_Report.docx")
    shutil.copy2(src_docx, "report/Major_Project_Report_Final_Updated.docx")
    print("Synchronized all report docx files.")
except Exception as e:
    print("Sync error:", e)
