import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def style_cell(cell, font_size_pt=9.0, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.paragraphs[0].paragraph_format.alignment = align
    cell.paragraphs[0].paragraph_format.space_before = Pt(0)
    cell.paragraphs[0].paragraph_format.space_after = Pt(0)
    for r in cell.paragraphs[0].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size_pt)
        r.font.bold = bold
        r.font.color.rgb = RGBColor(0, 0, 0)

def update_table_2_1(doc_path):
    doc = docx.Document(doc_path)
    
    # Locate Table 2.1 (Table with Sl., Author / Year, Problem / Domain)
    t = None
    for tbl in doc.tables:
        if len(tbl.rows) > 0:
            h = [c.text.strip().replace('\n', ' ') for c in tbl.rows[0].cells]
            if len(h) >= 6 and h[0] == 'Sl.' and 'Author' in h[1]:
                t = tbl
                break
                
    if t is None:
        print(f"Could not find Table 2.1 in {doc_path}")
        return
        
    print(f"Found Table 2.1 in {doc_path}. Updating entries...")
    
    data_2_1 = [
        ('1', 'Sharafaldin et al. (2018)', 'Benchmark intrusion dataset generation & evaluation', 'Multi-vector attack simulation in enterprise testbed (CICIDS2017/2018)', 'Extracted 80 transport flow features; demonstrated high utility of directional timings', 'Published splits contained duplicate flow records and cross-partition session leakage'),
        ('2', 'Tavallaee et al. (2009)', 'Redundancy and bias analysis in legacy KDD99 corpus', 'Statistical deduplication and difficulty stratification producing NSL-KDD', 'Eliminated 78% redundant records; prevented classifiers from biasing toward frequent flows', 'Synthetic simulation environment lacks modern encrypted protocols and cloud payloads'),
        ('3', 'Neupane et al. (2022)', 'Explainability of automated NIDS alerts in SOCs', 'Systematic survey and evaluation of post-hoc attribution methods (SHAP, LIME)', 'Demonstrated that Shapley values provide highest mathematical consistency for flow triage', 'Continuous per-flow SHAP calculation introduces severe computational latency bottlenecks'),
        ('4', 'Mirsky et al. (2018)', 'Online wire-speed anomaly screening in network taps', 'Kitsune: Ensemble of lightweight neural autoencoders mapping packet statistics', 'Successfully isolated volumetric anomalies with low per-packet execution latency', 'Binary anomaly output lacks granular threat family labels; static threshold vulnerable to drift'),
        ('5', 'Chen & Guestrin (2016)', 'Scalable tree boosting for structured tabular datasets', 'Regularized gradient boosted decision trees with sparsity-aware split finding (XGBoost)', 'Achieved superior accuracy and training speed across benchmark classification tasks', 'Closed-world supervised model fails when encountering unmodeled zero-day intrusions'),
        ('6', 'Lundberg et al. (2020)', 'Efficient local feature attribution for tree-based ensembles', 'TreeSHAP algorithm optimizing conditional Shapley expectations in polynomial time', 'Reduced explanation computation time by orders of magnitude compared to model-agnostic SHAP', 'Unbounded invocation across every flow still exceeds sub-millisecond line-rate latency budgets'),
        ('7', 'Lu et al. (2018)', 'Systematic review of machine learning under concept drift', 'Taxonomy of windowing strategies, statistical divergence metrics, and adaptive ensembles', 'Demonstrated that sliding reference buffers and divergence metrics effectively track drift', 'Most adaptive frameworks require supervised ground truth labels, unavailable at line rate'),
        ('8', 'Moustafa & Slay (2015)', 'Generation of realistic contemporary network benchmark datasets', 'Synthetic attack simulation using IXIA PerfectStorm tool to create UNSW-NB15 dataset', 'Demonstrated that legacy benchmark features fail to capture contemporary threat behaviors', 'Focused on offline evaluation; real-time memory and CPU inference latency not profiled'),
        ('9', 'Sommer & Paxson (2010)', 'Fundamental operational obstacles to ML in intrusion detection', 'Critical analysis of semantic gap, closed-world assumptions, and asymmetric error costs', 'Proved that pure anomaly detection incurs prohibitive false-positive rates under network noise', 'Foundational theoretical study; did not implement a two-stage hybrid screening pipeline'),
        ('10', 'Engelen et al. (2021)', 'Troubleshooting methodological flaws in intrusion benchmarks', 'Systematic flow reconstruction audit of CIC-IDS benchmark feature extraction pipelines', 'Exposed subtle label mismatches, timing artifacts, and duplicate connection records', 'Evaluated benchmark data quality; did not propose an automated online drift-adaptive IDS')
    ]
    
    for row_idx, row_data in enumerate(data_2_1, start=1):
        row = t.rows[row_idx]
        for col_idx, text_val in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.text = text_val
            align = WD_ALIGN_PARAGRAPH.CENTER if col_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            style_cell(cell, font_size_pt=9.0, bold=False, align=align)
            
    doc.save(doc_path)
    print(f"Successfully updated Table 2.1 in {doc_path}")

if __name__ == '__main__':
    update_table_2_1('report/Major_Project_Report_Final_Updated.docx')
    update_table_2_1('report/Major_Project_Report_Final.docx')
    update_table_2_1('report/Major_Project_Report.docx')
