import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import copy

def set_cell_properties(cell, width_dxa=None, top_pt=3, bottom_pt=3, left_pt=5, right_pt=5, v_align='center'):
    tcPr = cell._tc.get_or_add_tcPr()
    if width_dxa is not None:
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is None:
            tcW = OxmlElement('w:tcW')
            tcPr.append(tcW)
        tcW.set(qn('w:w'), str(width_dxa))
        tcW.set(qn('w:type'), 'dxa')
        
    tcMar = tcPr.find(qn('w:tcMar'))
    if tcMar is None:
        tcMar = OxmlElement('w:tcMar')
        tcPr.append(tcMar)
    for m, pt in [('top', top_pt), ('bottom', bottom_pt), ('left', left_pt), ('right', right_pt)]:
        node = tcMar.find(qn(f'w:{m}'))
        if node is None:
            node = OxmlElement(f'w:{m}')
            tcMar.append(node)
        node.set(qn('w:w'), str(int(pt * 20)))
        node.set(qn('w:type'), 'dxa')
        
    vAlign = tcPr.find(qn('w:vAlign'))
    if vAlign is None:
        vAlign = OxmlElement('w:vAlign')
        tcPr.append(vAlign)
    vAlign.set(qn('w:val'), v_align)

def set_row_properties(row, is_header=False):
    trPr = row._tr.get_or_add_trPr()
    cantSplit = trPr.find(qn('w:cantSplit'))
    if cantSplit is None:
        trPr.append(OxmlElement('w:cantSplit'))
    jc = trPr.find(qn('w:jc'))
    if jc is None:
        jc = OxmlElement('w:jc')
        trPr.append(jc)
    jc.set(qn('w:val'), 'center')
    if is_header:
        tblHeader = trPr.find(qn('w:tblHeader'))
        if tblHeader is None:
            trPr.append(OxmlElement('w:tblHeader'))

def style_paragraph(p, font_name="Times New Roman", font_size_pt=9.5, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=1.5, line_spacing=1.0):
    p.paragraph_format.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    for r in p.runs:
        r.font.name = font_name
        r.font.size = Pt(font_size_pt)
        r.font.bold = bold
        r.font.color.rgb = RGBColor(0, 0, 0)

def set_cell_borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

def update_table_of_contents(doc, toc_entries):
    t = doc.tables[1]
    
    # Keep row 0 (header), delete all subsequent rows
    while len(t.rows) > 1:
        tr = t.rows[-1]._tr
        tr.getparent().remove(tr)
        
    # Column widths in dxa (1 inch = 1440 dxa):
    # Col 0 (Sr. NO.): 1152 dxa (0.8 in)
    # Col 1 (CONTENTS): 6480 dxa (4.5 in)
    # Col 2 (PAGE NO.): 1008 dxa (0.7 in)
    col_widths = [1152, 6480, 1008]
    
    # Configure header row (row 0)
    set_row_properties(t.rows[0], is_header=True)
    header_texts = ['Sr. NO.', 'CONTENTS', 'PAGE NO.']
    for j, cell in enumerate(t.rows[0].cells):
        cell.text = header_texts[j]
        set_cell_properties(cell, width_dxa=col_widths[j], top_pt=4, bottom_pt=4, left_pt=6, right_pt=6)
        set_cell_borders(cell)
        align = WD_ALIGN_PARAGRAPH.CENTER if j != 1 else WD_ALIGN_PARAGRAPH.LEFT
        style_paragraph(cell.paragraphs[0], font_name="Times New Roman", font_size_pt=9.5, bold=True, align=align, space_before=0, space_after=0)

    # Add each entry
    for item in toc_entries:
        sr_no, title, page_no, level = item # level: 'chapter', 'section', 'subsection', 'backmatter'
        row = t.add_row()
        set_row_properties(row, is_header=False)
        
        is_bold = (level in ['chapter', 'backmatter'])
        font_size = 9.5 if level in ['chapter', 'backmatter'] else 9.0
        
        # Indentation for title
        indent_prefix = ""
        if level == 'section':
            indent_prefix = "   "
        elif level == 'subsection':
            indent_prefix = "      "
            
        row.cells[0].text = sr_no
        row.cells[1].text = indent_prefix + title
        row.cells[2].text = str(page_no)
        
        for j, cell in enumerate(row.cells):
            set_cell_properties(cell, width_dxa=col_widths[j], top_pt=2, bottom_pt=2, left_pt=6, right_pt=6)
            set_cell_borders(cell)
            if j == 0:
                align = WD_ALIGN_PARAGRAPH.CENTER if not sr_no else WD_ALIGN_PARAGRAPH.LEFT
            elif j == 1:
                align = WD_ALIGN_PARAGRAPH.LEFT
            else:
                align = WD_ALIGN_PARAGRAPH.CENTER
            style_paragraph(cell.paragraphs[0], font_name="Times New Roman", font_size_pt=font_size, bold=is_bold, align=align, space_before=0, space_after=0)

def update_list_of_figures(doc, figure_entries):
    t = doc.tables[2]
    while len(t.rows) > 1:
        tr = t.rows[-1]._tr
        tr.getparent().remove(tr)
        
    col_widths = [1440, 6192, 1008]
    set_row_properties(t.rows[0], is_header=True)
    header_texts = ['Sr. No.', 'TITLE', 'Page No.']
    for j, cell in enumerate(t.rows[0].cells):
        cell.text = header_texts[j]
        set_cell_properties(cell, width_dxa=col_widths[j], top_pt=4, bottom_pt=4, left_pt=6, right_pt=6)
        set_cell_borders(cell)
        align = WD_ALIGN_PARAGRAPH.CENTER if j != 1 else WD_ALIGN_PARAGRAPH.LEFT
        style_paragraph(cell.paragraphs[0], font_name="Times New Roman", font_size_pt=9.5, bold=True, align=align, space_before=0, space_after=0)

    for fig_no, title, page_no in figure_entries:
        row = t.add_row()
        set_row_properties(row, is_header=False)
        row.cells[0].text = fig_no
        row.cells[1].text = title
        row.cells[2].text = str(page_no)
        for j, cell in enumerate(row.cells):
            set_cell_properties(cell, width_dxa=col_widths[j], top_pt=2.5, bottom_pt=2.5, left_pt=6, right_pt=6)
            set_cell_borders(cell)
            align = WD_ALIGN_PARAGRAPH.CENTER if j == 2 else (WD_ALIGN_PARAGRAPH.LEFT if j == 1 else WD_ALIGN_PARAGRAPH.CENTER)
            style_paragraph(cell.paragraphs[0], font_name="Times New Roman", font_size_pt=9.0, bold=False, align=align, space_before=0, space_after=0)

def update_list_of_tables(doc, table_entries):
    t = doc.tables[3]
    while len(t.rows) > 1:
        tr = t.rows[-1]._tr
        tr.getparent().remove(tr)
        
    col_widths = [1440, 6192, 1008]
    set_row_properties(t.rows[0], is_header=True)
    header_texts = ['Sr. No.', 'TITLE', 'Page No.']
    for j, cell in enumerate(t.rows[0].cells):
        cell.text = header_texts[j]
        set_cell_properties(cell, width_dxa=col_widths[j], top_pt=4, bottom_pt=4, left_pt=6, right_pt=6)
        set_cell_borders(cell)
        align = WD_ALIGN_PARAGRAPH.CENTER if j != 1 else WD_ALIGN_PARAGRAPH.LEFT
        style_paragraph(cell.paragraphs[0], font_name="Times New Roman", font_size_pt=9.5, bold=True, align=align, space_before=0, space_after=0)

    for tbl_no, title, page_no in table_entries:
        row = t.add_row()
        set_row_properties(row, is_header=False)
        row.cells[0].text = tbl_no
        row.cells[1].text = title
        row.cells[2].text = str(page_no)
        for j, cell in enumerate(row.cells):
            set_cell_properties(cell, width_dxa=col_widths[j], top_pt=2.5, bottom_pt=2.5, left_pt=6, right_pt=6)
            set_cell_borders(cell)
            align = WD_ALIGN_PARAGRAPH.CENTER if j == 2 else (WD_ALIGN_PARAGRAPH.LEFT if j == 1 else WD_ALIGN_PARAGRAPH.CENTER)
            style_paragraph(cell.paragraphs[0], font_name="Times New Roman", font_size_pt=9.0, bold=False, align=align, space_before=0, space_after=0)

if __name__ == '__main__':
    toc_data = [
        # Chapter 1
        ('1.', 'INTRODUCTION', '1', 'chapter'),
        ('1.1', 'Background', '1', 'section'),
        ('1.2', 'Problem Statement', '1', 'section'),
        ('1.3', 'Motivation / Need for the Project', '2', 'section'),
        ('1.4', 'Objectives', '3', 'section'),
        ('1.5', 'Scope of the Project', '3', 'section'),
        ('1.6', 'Significance / Expected Contribution', '3', 'section'),
        ('1.7', 'Organization of the Report', '4', 'section'),
        # Chapter 2
        ('2.', 'LITERATURE SURVEY', '5', 'chapter'),
        ('2.1', 'Introduction', '5', 'section'),
        ('2.2', 'Review of Existing Work', '6', 'section'),
        ('2.3', 'Comparative Analysis', '7', 'section'),
        ('2.4', 'Research / Design Gap', '8', 'section'),
        ('2.5', 'Summary', '8', 'section'),
        # Chapter 3
        ('3.', 'PROPOSED SYSTEM AND SCOPE', '9', 'chapter'),
        ('3.1', 'Problem Formulation', '9', 'section'),
        ('3.2', 'Proposed Solution', '9', 'section'),
        ('3.3', 'Requirements', '10', 'section'),
        ('3.3.1', 'Functional & Non-Functional Requirements', '10', 'subsection'),
        ('3.3.2', 'Hardware & Software Requirements', '11', 'subsection'),
        ('3.4', 'System Architecture / Block Diagram', '12', 'section'),
        ('3.5', 'Functional Components & Scope Constraints', '13', 'section'),
        # Chapter 4
        ('4.', 'METHODOLOGY', '14', 'chapter'),
        ('4.1', 'Objective and Method / Approach', '14', 'section'),
        ('4.2', 'Measurement / Evaluation Parameters', '14', 'section'),
        ('4.3', 'Model Architecture and Structural Diagrams', '15', 'section'),
        ('4.3.1', 'Autoencoder Latent Topology & Manifold Projection', '15', 'subsection'),
        ('4.3.2', 'Sequence Diagram of Packet Ingestion and Prediction', '16', 'subsection'),
        ('4.3.3', 'Activity Diagram of Tiered Detection and Alert Routing', '17', 'subsection'),
        ('4.3.4', 'Data Flow Diagram (DFD Level-1) for Flow Processing', '18', 'subsection'),
        ('4.3.5', 'Class Diagram and Use Case Diagram', '19', 'subsection'),
        ('4.4', 'Error Sources, Mitigation, and Data Processing', '20', 'section'),
        # Chapter 5
        ('5.', 'IMPLEMENTATION & EXPERIMENTAL WORK', '21', 'chapter'),
        ('5.1', 'Implementation Environment', '21', 'section'),
        ('5.2', 'Module-wise Implementation', '21', 'section'),
        ('5.2.1', 'Data Preparation & Cryptographic Hygiene', '21', 'subsection'),
        ('5.2.2', 'Feature Preprocessing & Locked Scaling', '22', 'subsection'),
        ('5.2.3', 'Autoencoder Model Training & Manifold Construction', '22', 'subsection'),
        ('5.2.4', 'Validation Youden\'s J Threshold Optimization', '23', 'subsection'),
        ('5.2.5', 'XGBoost Multi-Class Classification & Confidence Gating', '23', 'subsection'),
        ('5.2.6', 'Dynamic Concept Drift Monitoring & Alert-Gated TreeSHAP', '24', 'subsection'),
        ('5.3', 'Experimental Setup', '24', 'section'),
        ('5.4', 'Prototype & Testing', '26', 'section'),
        # Chapter 6
        ('6.', 'RESULTS, ANALYSIS AND DISCUSSION', '27', 'chapter'),
        ('6.1', 'Quantitative Classification Results', '27', 'section'),
        ('6.2', 'Confusion Matrix & Threshold Analysis', '29', 'section'),
        ('6.3', 'Zero-Day Generalization & Drift Tracking', '31', 'section'),
        ('6.4', 'Latency, Memory Footprint & Baseline Comparisons', '34', 'section'),
        # Chapter 7
        ('7.', 'CONCLUSION AND FUTURE SCOPE', '38', 'chapter'),
        ('7.1', 'Summary of Work', '38', 'section'),
        ('7.2', 'Conclusions', '38', 'section'),
        ('7.3', 'Contributions & Utility', '38', 'section'),
        ('7.4', 'Limitations & Scope for Future Work', '39', 'section'),
        # Backmatter
        ('', 'RESEARCH PAPER / PATENT PUBLISHED (if any)', '40', 'backmatter'),
        ('', 'REFERENCES', '40', 'backmatter'),
        ('', 'APPENDICES', '42', 'backmatter'),
        ('', 'Appendix A: Mathematical Derivations and Objective Functions', '42', 'subsection'),
        ('', 'Appendix B: Scapy Live Packet Sniffing & Flow Extraction Configuration', '42', 'subsection'),
    ]

    figure_data = [
        ('Figure 3.1', 'System Architecture of the Two-Stage Hybrid NIDS', '12'),
        ('Figure 4.1', 'Sequence Diagram of Packet Ingestion and Prediction', '16'),
        ('Figure 4.2', 'Activity Diagram of Tiered Detection and Alert Routing', '17'),
        ('Figure 4.3', 'Data Flow Diagram (DFD Level-1) for Flow Processing', '18'),
        ('Figure 4.4', 'Class Diagram of Object-Oriented Framework Architecture', '19'),
        ('Figure 4.5', 'Use Case Diagram of Network Intrusion Detection Workflow', '20'),
        ('Figure 5.1', 'Real-Time Network Flow Telemetry and Live Sniffing Monitor', '26'),
        ('Figure 5.2', 'Threat Diagnosis, Alert Gating, and Local TreeSHAP Explanation', '26'),
        ('Figure 6.1', 'Row-Normalized Confusion Matrices for Hybrid AE–XGBoost Model', '29'),
        ('Figure 6.2', 'Row-Normalized Confusion Matrices for Standalone Autoencoder', '30'),
        ('Figure 6.3', 'Reconstruction Threshold Sensitivity and Pareto Optimization Curves', '31'),
        ('Figure 6.4', 'Generalization Audits: Unseen Attack Detection and Chronological Split Decay', '32'),
        ('Figure 6.5', 'Statistical Concept Drift Tracking (DKS, PSI, JSD) Across Windows', '33'),
        ('Figure 6.6', 'TreeSHAP Global Feature Importance Ranking (Summary Plot)', '34'),
        ('Figure 6.7', 'End-to-End Pipeline Execution Latency Breakdown on Multi-Core CPU', '35'),
    ]

    table_data = [
        ('Table 2.1', 'Comparison of Existing NIDS Approaches, Methodologies, and Gaps', '6'),
        ('Table 4.1', 'Measurement and Evaluation Parameters for Model Assessment', '14'),
        ('Table 4.2', 'Autoencoder Bottleneck Layer Configuration and Dimensionality', '15'),
        ('Table 5.1', 'Cryptographically Audited Dataset Splits Enforcing Zero Leakage', '21'),
        ('Table 5.2', 'Experimental Setup Parameters and Hyperparameter Configurations', '24'),
        ('Table 5.3', 'System Test Cases, Inputs, Expected Outcomes, and Execution Status', '25'),
        ('Table 6.1', 'Overall Classification Performance on Held-Out Test Partitions', '27'),
        ('Table 6.2', 'Multi-Class Attack Detection Breakdown on CICIDS2018 (N = 100,670)', '28'),
        ('Table 6.3', 'Multi-Class Attack Detection Breakdown on NSL-KDD (N = 22,169)', '28'),
        ('Table 6.4', 'Reconstruction Threshold Strategy Comparison on CICIDS2018', '30'),
        ('Table 6.5', 'Leave-One-Attack-Out (LOAO) Unseen Attack Detection Performance', '32'),
        ('Table 6.6', 'Statistical Concept Drift Tracking Across Sequential Windows', '33'),
        ('Table 6.7', 'Computational Benchmark: Latency, Throughput, and Peak Memory (RSS)', '35'),
        ('Table 6.8', 'Benchmark Comparison Against Baseline Supervised Classifiers', '36'),
    ]

    target_files = [
        'report/Major_Project_Report_Final.docx',
        'report/Major_Project_Report.docx',
        'report/Major_Project_Report_Final_Updated.docx'
    ]

    for fpath in target_files:
        print(f"Updating {fpath}...")
        doc = docx.Document(fpath)
        update_table_of_contents(doc, toc_data)
        update_list_of_figures(doc, figure_data)
        update_list_of_tables(doc, table_data)
        doc.save(fpath)
        print(f"Successfully saved {fpath}")

