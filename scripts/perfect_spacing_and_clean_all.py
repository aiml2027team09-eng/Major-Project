import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import re
import shutil

def perfect_master_formatting(master_path):
    print(f"Applying perfect spacing and cleanup to: {master_path}")
    doc = docx.Document(master_path)
    body = doc._body._body
    
    # 1. Find where CHAPTER 1 begins
    ch1_idx = None
    for i, el in enumerate(body):
        tag = el.tag.split('}')[-1]
        if tag == 'p':
            txt = ''.join(el.itertext()).strip()
            if txt.startswith("CHAPTER 1"):
                ch1_idx = i
                break
                
    if ch1_idx is None:
        ch1_idx = 0
    print(f"Body starts at element index: {ch1_idx}")
    
    # 2. Iterate through body elements and clean empty paragraphs
    # Rule: An empty paragraph is kept ONLY if:
    #   - It contains a drawing (figure image)
    #   - It contains a pageBreak
    #   - It contains sectPr
    #   - It immediately follows a table AND precedes another table or sectPr (structural requirement for Word)
    # Otherwise, it is deleted!
    
    elems_to_remove = []
    for i in range(ch1_idx, len(body)):
        el = body[i]
        tag = el.tag.split('}')[-1]
        if tag == 'p':
            txt = ''.join(el.itertext()).strip()
            has_draw = len(el.xpath('.//w:drawing')) > 0
            has_pb = len(el.xpath('.//w:br[@w:type="page"]')) > 0
            has_sectPr = len(el.xpath('./w:pPr/w:sectPr')) > 0
            
            if not txt and not has_draw and not has_pb and not has_sectPr:
                prev_tag = body[i-1].tag.split('}')[-1] if i > 0 else None
                next_tag = body[i+1].tag.split('}')[-1] if i < len(body)-1 else None
                
                # Check if this empty p is needed as structural buffer
                is_structural = (prev_tag == 'tbl' and (next_tag == 'tbl' or next_tag == 'sectPr' or next_tag is None))
                if is_structural:
                    # Make it zero-height so Word doesn't crash and user sees NO blank line
                    pPr = el.xpath('./w:pPr')
                    if not pPr:
                        pPr = parse_xml(r'<w:pPr %s/>' % nsdecls('w'))
                        el.insert(0, pPr)
                    else:
                        pPr = pPr[0]
                    # remove existing spacing
                    for sp in pPr.xpath('./w:spacing'):
                        pPr.remove(sp)
                    for rPr in pPr.xpath('./w:rPr'):
                        pPr.remove(rPr)
                    pPr.append(parse_xml(r'<w:spacing %s w:before="0" w:after="0" w:line="20" w:lineRule="exact"/>' % nsdecls('w')))
                    pPr.append(parse_xml(r'<w:rPr %s><w:sz w:val="2"/></w:rPr>' % nsdecls('w')))
                else:
                    elems_to_remove.append(el)
                    
    print(f"Removing {len(elems_to_remove)} unwanted empty paragraphs...")
    for el in elems_to_remove:
        el.getparent().remove(el)
        
    # Ensure every table that precedes a sectPr or table has a zero-height paragraph
    for i, el in enumerate(list(body)[ch1_idx:]):
        tag = el.tag.split('}')[-1]
        if tag == 'tbl':
            # Check next element
            idx_in_body = list(body).index(el)
            if idx_in_body < len(body) - 1:
                next_el = body[idx_in_body + 1]
                next_tag = next_el.tag.split('}')[-1]
                if next_tag in ['tbl', 'sectPr']:
                    zero_p = parse_xml(r'<w:p %s><w:pPr><w:spacing w:before="0" w:after="0" w:line="20" w:lineRule="exact"/><w:rPr><w:sz w:val="2"/></w:rPr></w:pPr></w:p>' % nsdecls('w'))
                    el.addnext(zero_p)
            else:
                zero_p = parse_xml(r'<w:p %s><w:pPr><w:spacing w:before="0" w:after="0" w:line="20" w:lineRule="exact"/><w:rPr><w:sz w:val="2"/></w:rPr></w:pPr></w:p>' % nsdecls('w'))
                el.addnext(zero_p)

    # 3. Fine-tune paragraph spacing across the document
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
            
        # A. Chapter Title
        if txt.startswith("CHAPTER "):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            continue
            
        # B. Level 2 Section Headings (e.g. 1.4 Objectives)
        if re.match(r'^\d+\.\d+\s+[A-Z]', txt) or txt in ['REFERENCES', 'APPENDICES']:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # C. Level 3 Subsection Headings (e.g. 3.3.1, 4.3.2, 5.2.1, Appendix A, Appendix B)
        if re.match(r'^\d+\.\d+\.\d+\s+', txt) or txt.startswith("Appendix A:") or txt.startswith("Appendix B:"):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # D. Listing Introductions (e.g. "Listing B.1 provides...")
        if re.match(r'^Listing\s+\w+\.\d+\s+(provides|demonstrates|details)', txt):
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.keep_with_next = True
            continue
            
        # E. Listing Captions (e.g. "Listing B.1: Real-Time...")
        if re.match(r'^Listing\s+\w+\.\d+:', txt):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.keep_with_next = True
            continue
            
        # F. Figure and Table Captions
        if re.match(r'^(Figure|Table)\s+\d+\.\d+:', txt):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
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

    doc.save(master_path)
    print(f"-> Successfully saved master document: {master_path}")

if __name__ == '__main__':
    src = 'report/Major_Project_Report_Final_Updated.docx'
    perfect_master_formatting(src)
    shutil.copy2(src, 'report/Major_Project_Report.docx')
