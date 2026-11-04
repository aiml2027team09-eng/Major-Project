import docx
import shutil
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def generate_batch_parts(source_path, part_a_out, part_b_out):
    print(f"Reading master source from: {source_path}")
    
    # 1. GENERATE PART A
    doc_a = docx.Document(source_path)
    body_a = doc_a._body._body
    
    ch1_elem_a = None
    for p in doc_a.paragraphs:
        if p.text.strip().startswith("CHAPTER 1"):
            ch1_elem_a = p._p
            break
            
    if ch1_elem_a is None:
        raise ValueError("Could not find CHAPTER 1 in source document!")
        
    ch1_idx_a = list(body_a).index(ch1_elem_a)
    print(f"Part A: Removing elements from index {ch1_idx_a} to end ({len(body_a)} total)")
    for elem in list(body_a)[ch1_idx_a:]:
        body_a.remove(elem)
        
    # Move sectPr from last paragraph to body child to keep valid 4-section structure
    last_p = None
    for child in reversed(list(body_a)):
        if child.tag.endswith('p'):
            last_p = child
            break
            
    if last_p is not None:
        sectPr_in_p = last_p.xpath('./w:pPr/w:sectPr')
        if sectPr_in_p:
            sp = sectPr_in_p[0]
            sp.getparent().remove(sp)
            body_a.append(sp)
            
    doc_a.save(part_a_out)
    print(f"-> Saved Part A to: {part_a_out}")
    
    # 2. GENERATE PART B
    doc_b = docx.Document(source_path)
    body_b = doc_b._body._body
    
    ch1_elem_b = None
    for p in doc_b.paragraphs:
        if p.text.strip().startswith("CHAPTER 1"):
            ch1_elem_b = p._p
            break
            
    ch1_idx_b = list(body_b).index(ch1_elem_b)
    print(f"Part B: Removing preliminary elements from 0 to {ch1_idx_b}")
    for elem in list(body_b)[:ch1_idx_b]:
        body_b.remove(elem)
        
    # Ensure doc_b ends with a structural paragraph before sectPr if last element is table
    last_child_b = list(body_b)[-1]
    if last_child_b.tag.endswith('tbl'):
        zero_p = parse_xml(r'<w:p %s><w:pPr><w:spacing w:before="0" w:after="0" w:line="20" w:lineRule="exact"/><w:rPr><w:sz w:val="2"/></w:rPr></w:pPr></w:p>' % nsdecls('w'))
        body_b.append(zero_p)
        
    doc_b.save(part_b_out)
    print(f"-> Saved Part B to: {part_b_out}")

if __name__ == '__main__':
    src = 'report/Major_Project_Report_Final_Updated.docx'
    generate_batch_parts(src, 'report/Part A_26AI09.docx', 'report/Part B_26AI09.docx')
    shutil.copy2('report/Part A_26AI09.docx', 'report/Part A_Batch_number.docx')
    shutil.copy2('report/Part B_26AI09.docx', 'report/Part B_Batch_number.docx')
    print("All batch files successfully generated and synchronized!")
