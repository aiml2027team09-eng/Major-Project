import docx
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

def set_footer_empty(sec):
    sec.different_first_page_header_footer = False
    sec.footer.is_linked_to_previous = False
    ftr = sec.footer
    for p in list(ftr.paragraphs):
        p._p.getparent().remove(p._p)
    empty_p = parse_xml(r'<w:p %s><w:pPr><w:pStyle w:val="Footer"/></w:pPr></w:p>' % nsdecls('w'))
    ftr._element.append(empty_p)

def set_footer_page_number(sec, default_text="1"):
    sec.different_first_page_header_footer = False
    sec.footer.is_linked_to_previous = False
    ftr = sec.footer
    for p in list(ftr.paragraphs):
        p._p.getparent().remove(p._p)
    p_xml = parse_xml(r'''
        <w:p %s>
            <w:pPr>
                <w:pStyle w:val="Footer"/>
                <w:jc w:val="center"/>
            </w:pPr>
            <w:fldSimple w:instr="PAGE">
                <w:r>
                    <w:rPr>
                        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
                        <w:sz w:val="24"/>
                    </w:rPr>
                    <w:t>%s</w:t>
                </w:r>
            </w:fldSimple>
        </w:p>
    ''' % (nsdecls('w'), default_text))
    ftr._element.append(p_xml)

def set_pgNumType(sec, fmt=None, start=None):
    for el in sec._sectPr.xpath('./w:pgNumType'):
        sec._sectPr.remove(el)
    attrs = []
    if fmt is not None:
        attrs.append(f'w:fmt="{fmt}"')
    if start is not None:
        attrs.append(f'w:start="{start}"')
    if attrs:
        xml_str = f'<w:pgNumType %s {" ".join(attrs)}/>' % nsdecls('w')
        sec._sectPr.append(parse_xml(xml_str))

def configure_part_a(file_path):
    print(f"Configuring page numbers for Part A: {file_path}")
    doc = docx.Document(file_path)
    
    # Section 0: Title page
    set_footer_empty(doc.sections[0])
    set_pgNumType(doc.sections[0], start="1")
    
    # Section 1: Certificate
    if len(doc.sections) > 1:
        set_footer_empty(doc.sections[1])
        set_pgNumType(doc.sections[1])
        
    # Section 2: Declaration & Acknowledgements
    if len(doc.sections) > 2:
        set_footer_empty(doc.sections[2])
        set_pgNumType(doc.sections[2])
        
    # Section 3: Abstract through Abbreviations
    if len(doc.sections) > 3:
        set_footer_page_number(doc.sections[3], default_text="v")
        set_pgNumType(doc.sections[3], fmt="lowerRoman", start="5")
        
    doc.save(file_path)
    print(f"-> Successfully saved Part A: {file_path}")

def configure_part_b(file_path):
    print(f"Configuring page numbers for Part B: {file_path}")
    doc = docx.Document(file_path)
    
    for i, sec in enumerate(doc.sections):
        # Remove all headerReference elements from sectPr so Part B has cleanly NO header
        for el in sec._sectPr.xpath('./w:headerReference'):
            sec._sectPr.remove(el)
            
        # Centered Arabic page number in footer
        set_footer_page_number(sec, default_text="1")
        if i == 0:
            set_pgNumType(sec, fmt="decimal", start="1")
        else:
            set_pgNumType(sec, fmt="decimal")
            
    doc.save(file_path)
    print(f"-> Successfully saved Part B: {file_path}")

if __name__ == '__main__':
    configure_part_a('report/Part A_26AI09.docx')
    configure_part_a('report/Part A_Batch_number.docx')
    configure_part_b('report/Part B_26AI09.docx')
    configure_part_b('report/Part B_Batch_number.docx')
