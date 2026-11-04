import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

combined_text = (
    "The primary empirical findings of this study establish three core conclusions: "
    "first, regarding the resolution of threshold collapse, rigid parametric Gaussian rules (μ + 3σ) "
    "completely fail on heavy-tailed network traffic—dropping attack recall to 0.00%—whereas validation "
    "optimization using Youden's J-statistic establishes optimal non-parametric thresholds (τ* = 0.1973 "
    "on CICIDS2018; τ* = 0.0840 on NSL-KDD), securing 99.70% attack recall. Second, establishing zero-day "
    "defense-in-depth under Leave-One-Attack-Out testing, the unsupervised Autoencoder successfully detected "
    "93.11% of unseen DoS attacks and 82.22% of unseen Probe attacks through reconstruction error gating alone. "
    "Third, line-rate operational efficiency is achieved by restricting TreeSHAP computation strictly to anomaly "
    "alerts, eliminating 90% of explainability overhead, while extensive profiling on standard CPU hardware "
    "verified an inference latency of 0.1830 ms per flow (5,464 flows/s) with a peak memory footprint of 527.0 MB RSS."
)

target_files = [
    'report/Major_Project_Report_Final.docx',
    'report/Major_Project_Report.docx',
    'report/Major_Project_Report_Final_Updated.docx'
]

for fpath in target_files:
    doc = docx.Document(fpath)
    
    # Locate section 7.2
    idx_72 = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == "7.2 Conclusions":
            idx_72 = i
            break
            
    if idx_72 is None:
        print(f"Could not find '7.2 Conclusions' in {fpath}")
        continue
        
    print(f"Found '7.2 Conclusions' at index {idx_72} in {fpath}")
    
    # Identify paragraphs 1, 2, 3 under 7.2
    # In doc.paragraphs, idx_72 + 1, idx_72 + 2, idx_72 + 3
    p1 = doc.paragraphs[idx_72 + 1]
    p2 = doc.paragraphs[idx_72 + 2]
    p3 = doc.paragraphs[idx_72 + 3]
    
    # Update p1 with combined text
    p1.clear()
    r = p1.add_run(combined_text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    p1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p1.paragraph_format.line_spacing = 1.3
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(6)
    
    # Remove p2 and p3 from document body
    p2._p.getparent().remove(p2._p)
    p3._p.getparent().remove(p3._p)
    
    doc.save(fpath)
    print(f"Successfully updated {fpath}")
