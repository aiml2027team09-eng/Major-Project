import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import re
import shutil

def clean_duplicates_and_spacing(doc_path):
    print(f"Opening {doc_path} for duplicate and spacing cleanup...")
    doc = docx.Document(doc_path)
    
    # 1. FIX SECTION 1.3
    p_13_lead = None
    p_13_items = []
    for i, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if "These operational realities motivate the design" in txt:
            p_13_lead = p
            p_13_lead.text = "These operational realities motivate the design of a unified two-stage hybrid framework:"
            p_13_lead.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_13_lead.paragraph_format.line_spacing = 1.5
            p_13_lead.paragraph_format.space_before = Pt(4)
            p_13_lead.paragraph_format.space_after = Pt(4)
            for r in p_13_lead.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 2. FIX SECTION 1.4
    p_14_lead = None
    for i, p in enumerate(doc.paragraphs):
        txt = p.text.strip()
        if "The primary engineering and research objectives of this capstone" in txt:
            p.text = "The primary engineering and research objectives of this capstone project are:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # Update objectives text to be professional and clean
    obj_texts = [
        "1. Baseline Performance Auditing: Establish rigorous empirical baselines for classical machine learning and deep neural architectures across standardized network security corpora.",
        "2. Tiered Hybrid Architecture Design: Formulate, train, and optimize a two-stage intrusion detection pipeline coupling an unsupervised symmetric Autoencoder gatekeeper with a downstream multi-class XGBoost classifier.",
        "3. Zero-Leakage Data Sanitization: Implement a cryptographically audited data preprocessing workflow that strictly prevents cross-split data leakage (Train ∩ Test = ∅) on benchmark datasets.",
        "4. Threshold Calibration and Drift Adaptation: Overcome Gaussian threshold breakdown by optimizing non-parametric Youden's J-statistic on validation data, and integrate sliding-window statistical drift tracking (DKS, PSI, JSD).",
        "5. Wire-Speed Validation and Interactive Telemetry: Measure and verify sub-millisecond per-flow processing latency on standard multi-core CPUs, and deliver a deployable Streamlit dashboard for real-time traffic analysis and local SHAP explanations."
    ]
    obj_idx = 0
    for p in doc.paragraphs:
        txt = p.text.strip()
        if re.match(r'^1\.\s+To establish', txt) or re.match(r'^1\.\s+Baseline', txt):
            # update this and next 4
            p.text = obj_texts[0]
            obj_idx = 1
        elif obj_idx in [1, 2, 3, 4] and re.match(r'^\d+\.\s+', txt):
            p.text = obj_texts[obj_idx]
            obj_idx += 1
            
    # 3. FIX SECTION 1.5
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "The scope of this investigation includes:" in txt:
            p.text = "The scope of this investigation includes:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    scope_texts = [
        "• Benchmark Datasets: Comprehensive evaluation on the modern, high-dimensional CSE-CIC-IDS2018 dataset (78 continuous transport-layer features) and the multi-class NSL-KDD benchmark corpus (41 connection attributes, expanded to 122 one-hot features).",
        "• Threat Taxonomy: Detection and granular categorization of major exploit vectors: volumetric Denial of Service (DoS/DDoS), automated credential brute-forcing (SSH and FTP), port scanning reconnaissance, Remote-to-Local (R2L) exploits, and User-to-Root (U2R) host privilege escalations.",
        "• Zero-Day Resilience Auditing: Rigorous assessment of unmodeled threat isolation capabilities using a strict Leave-One-Attack-Out (LOAO) cross-validation protocol.",
        "• Deployment Modality: Execution on standard commodity multi-core CPU architectures without requiring GPU coprocessors, accommodating both offline CSV/PCAP batch processing and live promiscuous socket flow capture."
    ]
    scope_idx = 0
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Benchmark Datasets:" in txt or "Evaluation Corpora:" in txt:
            p.text = scope_texts[0]
            scope_idx = 1
        elif scope_idx in [1, 2, 3] and (txt.startswith("•") or txt.startswith("-")):
            p.text = scope_texts[scope_idx]
            scope_idx += 1
            
    # 4. FIX SECTION 1.6
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "This research contributes several concrete solutions" in txt:
            p.text = "This research contributes several concrete solutions and empirical findings to network security engineering:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    sig_texts = [
        "1. Cryptographic Data Hygiene: Identification and elimination of 362 leaking flow records from legacy benchmark splits, guaranteeing verifiable reproducibility.",
        "2. Resolution of Threshold Collapse: Empirical demonstration of the complete breakdown of parametric μ + 3σ rules on heavy-tailed flow data, and formulation of non-parametric Youden's J optimization that restores attack recall to 99.70%.",
        "3. Zero-Day Defense-in-Depth: Verification that the unsupervised gatekeeper successfully isolates 93.11% of unseen DoS attacks and 82.22% of unseen Probe attacks through reconstruction error alone, without prior training exposure.",
        "4. Alert-Gated Explainability: Reduction of TreeSHAP computational overhead by 90% by computing Shapley attributions strictly on anomaly interrupts, preserving line-rate processing.",
        "5. Production-Grade Efficiency: Verification of 0.1830 ms per-flow inference latency (5,464 flows/s) and a compact 527.0 MB RSS memory footprint on standard CPU hardware."
    ]
    sig_idx = 0
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Verifiable Data Hygiene:" in txt or "Cryptographic Data Hygiene:" in txt:
            p.text = sig_texts[0]
            sig_idx = 1
        elif sig_idx in [1, 2, 3, 4] and re.match(r'^\d+\.\s+', txt):
            p.text = sig_texts[sig_idx]
            sig_idx += 1
            
    # 5. FIX SECTION 1.7
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "The structure of this report is outlined as follows:" in txt:
            p.text = "The structure of this report is outlined as follows:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 6. FIX SECTION 2.3
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Existing methodologies in data-driven intrusion detection generally align" in txt:
            p.text = "Existing methodologies in data-driven intrusion detection generally align with two contrasting paradigms:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 7. FIX SECTION 2.4
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "A detailed examination of contemporary literature highlights four" in txt:
            p.text = "A detailed examination of contemporary literature highlights four critical operational limitations:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 8. FIX SECTION 4.3.2 (Figure 4.1 Sequence Diagram)
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Figure 4.1 diagrams the interaction sequence between system components" in txt:
            p.text = "Figure 4.1 diagrams the interaction sequence between system components across three runtime operational scenarios:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 9. FIX SECTION 4.3.4 (Figure 4.3 DFD Level-1)
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Figure 4.3 models the Level-1 data flows across six key processing" in txt:
            p.text = "Figure 4.3 models the Level-1 data flows across six key processing stages and four data stores:"
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 10. FIX SECTION 4.4 (Error Sources)
    err_texts = [
        "• Class Imbalance: Resolved by training the Stage-1 Autoencoder exclusively on normal connection samples, while XGBoost incorporates weighted log-loss optimization.",
        "• Overfitting Mitigation: Controlled via dropout regularization (p=0.20), early stopping based on validation reconstruction error, and depth-bounded trees (max_depth = 6).",
        "• Benchmark Data Leakage: Addressed by calculating cryptographic SHA-256 hashes across all connection records, uncovering and purging 362 shared rows across partitions.",
        "• Concept Drift: Managed through a dynamic 500-sample circular buffer that periodically reassesses the 95th percentile threshold as traffic distributions evolve.",
        "• Stratified Evaluation: Applied across 70% training, 15% validation, and 15% testing splits, paired with Leave-One-Attack-Out cross-validation."
    ]
    # Remove duplicate block in P254
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "• Class Imbalance:" in txt and "\n" in txt:
            p.text = err_texts[0]
            break
            
    # 11. FIX SECTION 7.4 (Limitations & Scope)
    for p in doc.paragraphs:
        txt = p.text.strip()
        if "Current design limitations include reliance on transport-layer" in txt:
            p.text = "Current design limitations include reliance on transport-layer flow statistics without deep packet payload inspection, and CPU throughput boundaries under multi-gigabit saturating loads."
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            for r in p.runs:
                r.font.name = "Times New Roman"
                r.font.size = Pt(12)
            break
            
    # 12. CLEAN UP MULTIPLE CONSECUTIVE EMPTY PARAGRAPHS
    p_to_remove = []
    prev_empty = False
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            # Check if paragraph has graphic/image or table anchor
            has_drawing = len(p._element.xpath('.//w:drawing')) > 0
            if has_drawing:
                prev_empty = False
                continue
            if prev_empty:
                p_to_remove.append(p)
            else:
                prev_empty = True
        else:
            prev_empty = False
            
    print(f"Removing {len(p_to_remove)} redundant consecutive empty paragraphs...")
    for p in p_to_remove:
        p._p.getparent().remove(p._p)
        
    # 13. ENSURE ALL LIST ITEMS HAVE PROPER LEFT ALIGNMENT AND TIGHT SPACING
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
            
        # Bullet items and numbered items
        is_bullet = txt.startswith("•") or txt.startswith("-") or re.match(r'^\d+\.\s+', txt)
        # Exclude chapter/section headings like 1.1, 1., etc.
        is_heading = p.style.name.startswith("Heading") or re.match(r'^\d+\.\d+(\.\d+)?\s+', txt) or txt.startswith("CHAPTER ")
        
        if is_bullet and not is_heading and not txt.startswith("1. INTRODUCTION") and not txt.startswith("2. LITERATURE") and not txt.startswith("3. PROPOSED") and not txt.startswith("4. METHODOLOGY") and not txt.startswith("5. IMPLEMENTATION") and not txt.startswith("6. RESULTS") and not txt.startswith("7. CONCLUSION"):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT  # NEVER JUSTIFIED!
            p.paragraph_format.line_spacing = 1.25
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2.5)
            
    doc.save(doc_path)
    print(f"-> Successfully cleaned duplicates and fixed spacing in: {doc_path}")

if __name__ == '__main__':
    clean_duplicates_and_spacing('report/Major_Project_Report_Final_Updated.docx')
    shutil.copy2('report/Major_Project_Report_Final_Updated.docx', 'report/Major_Project_Report.docx')
