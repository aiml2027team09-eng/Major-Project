import docx
from lxml import etree
import copy

def create_parts(source_path, part_a_path, part_b_path):
    # ------------------ CREATE PART A ------------------
    doc_a = docx.Document(source_path)
    body_a = doc_a._body._body
    
    # Locate Chapter 1 heading element
    ch1_elem = None
    for p in doc_a.paragraphs:
        if p.text.strip().startswith("CHAPTER 1"):
            ch1_elem = p._p
            break
            
    if ch1_elem is None:
        raise ValueError("Could not find CHAPTER 1 in source document!")
        
    ch1_idx_a = list(body_a).index(ch1_elem)
    print(f"Part A: Removing elements from index {ch1_idx_a} to end ({len(body_a)} total elements)")
    
    # Remove all elements from ch1_idx_a to the end
    elems_to_remove_a = list(body_a)[ch1_idx_a:]
    for elem in elems_to_remove_a:
        body_a.remove(elem)
        
    doc_a.save(part_a_path)
    print(f"Successfully saved Part A to {part_a_path}")
    
    # ------------------ CREATE PART B ------------------
    doc_b = docx.Document(source_path)
    body_b = doc_b._body._body
    
    # Locate Chapter 1 heading element
    ch1_elem_b = None
    for p in doc_b.paragraphs:
        if p.text.strip().startswith("CHAPTER 1"):
            ch1_elem_b = p._p
            break
            
    ch1_idx_b = list(body_b).index(ch1_elem_b)
    print(f"Part B: Removing preliminary elements from 0 to {ch1_idx_b}")
    
    # Remove all preliminary elements before Chapter 1
    elems_to_remove_b = list(body_b)[:ch1_idx_b]
    for elem in elems_to_remove_b:
        body_b.remove(elem)
        
    # Remove all headers and footers from all sections in Part B
    for s in doc_b.sections:
        s.header.is_linked_to_previous = False
        for p in s.header.paragraphs:
            p.text = ""
        s.footer.is_linked_to_previous = False
        for p in s.footer.paragraphs:
            p.text = ""
            
        # Strip XML headerReference and footerReference from sectPr
        sectPr = s._sectPr
        for child in list(sectPr):
            tag = child.tag.split('}')[-1]
            if tag in ['headerReference', 'footerReference']:
                sectPr.remove(child)
                
    doc_b.save(part_b_path)
    print(f"Successfully saved Part B (without headers/footers) to {part_b_path}")

if __name__ == '__main__':
    src = 'report/Major_Project_Report_Final_Updated.docx'
    create_parts(src, 'report/Part A_26AI01.docx', 'report/Part B_26AI01.docx')
    create_parts(src, 'report/Part A_Batch_number.docx', 'report/Part B_Batch_number.docx')
