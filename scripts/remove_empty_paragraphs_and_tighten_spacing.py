import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import re

def remove_empty_paragraphs_and_tighten(doc_path):
    print(f"Opening {doc_path} to remove empty paragraphs and tighten spacing...")
    doc = docx.Document(doc_path)
    body = doc._body._body
    
    # 1. Identify CHAPTER 1 index so we only remove empty paragraphs in the BODY
    ch1_idx = None
    for i, el in enumerate(body):
        tag = el.tag.split('}')[-1]
        if tag == 'p':
            txt = ''.join(el.itertext()).strip()
            if txt.startswith("CHAPTER 1"):
                ch1_idx = i
                break
                
    if ch1_idx is None:
        ch1_idx = 0 # If document is Part B, CHAPTER 1 is at the very beginning
        
    print(f"Body starts at element index: {ch1_idx}")
    
    # 2. Collect purely useless empty paragraphs in the body
    empty_to_remove = []
    for i in range(ch1_idx, len(body)):
        el = body[i]
        tag = el.tag.split('}')[-1]
        if tag == 'p':
            txt = ''.join(el.itertext()).strip()
            has_draw = len(el.xpath('.//w:drawing')) > 0
            has_pb = len(el.xpath('.//w:br[@w:type="page"]')) > 0
            has_sectPr = len(el.xpath('./w:pPr/w:sectPr')) > 0
            if not txt and not has_draw and not has_pb and not has_sectPr:
                empty_to_remove.append(el)
                
    print(f"Removing {len(empty_to_remove)} purely useless empty paragraphs from body...")
    for el in empty_to_remove:
        el.getparent().remove(el)
        
    # 3. Tighten spacing across all paragraphs in the body
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
            
        # A. Chapter Headings (CHAPTER 1, etc.)
        if txt.startswith("CHAPTER "):
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            continue
            
        # B. Major Section Headings (e.g. 1.1 Background, 1.4 Objectives, 2.3 Comparative Analysis)
        if re.match(r'^\d+\.\d+\s+[A-Z]', txt) or txt in ['REFERENCES', 'APPENDICES']:
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # C. Subsection Headings (e.g. 3.3.1, 4.3.2, 5.2.1, Appendix A:, Appendix B:)
        if re.match(r'^\d+\.\d+\.\d+\s+', txt) or txt.startswith("Appendix A:") or txt.startswith("Appendix B:"):
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # D. Listing Introductions (e.g. "Listing B.1 provides...", "Listing 5.1 demonstrates...")
        if re.match(r'^Listing\s+\w+\.\d+\s+(provides|demonstrates|details)', txt):
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # E. Listing Captions (e.g. "Listing B.1: Real-Time...", "Listing 5.1: Cryptographic...")
        if re.match(r'^Listing\s+\w+\.\d+:', txt):
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.keep_with_next = True
            continue
            
        # F. Figure and Table Captions
        if re.match(r'^(Figure|Table)\s+\d+\.\d+:', txt):
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # G. Lists and Bullet Items
        is_bullet = txt.startswith("•") or txt.startswith("-") or re.match(r'^\d+\.\s+', txt)
        if is_bullet:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.25
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            continue
            
        # H. Standard Body Paragraphs
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)

    doc.save(doc_path)
    print(f"-> Successfully saved cleaned and tightened document: {doc_path}")

if __name__ == '__main__':
    remove_empty_paragraphs_and_tighten('report/Major_Project_Report_Final_Updated.docx')
    import shutil
    shutil.copy2('report/Major_Project_Report_Final_Updated.docx', 'report/Major_Project_Report.docx')
