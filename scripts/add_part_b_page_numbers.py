import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import qn

def add_footer_page_number(doc_path):
    print(f"Adding Arabic page numbering to: {doc_path}")
    doc = docx.Document(doc_path)
    
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.text = ""
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # XML for PAGE field
        fld_xml = parse_xml(
            f'<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            f'  <w:pPr><w:jc w:val="center"/></w:pPr>\n'
            f'  <w:r><w:fldChar w:fldCharType="begin"/></w:r>\n'
            f'  <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>\n'
            f'  <w:r><w:fldChar w:fldCharType="separate"/></w:r>\n'
            f'  <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:t>1</w:t></w:r>\n'
            f'  <w:r><w:fldChar w:fldCharType="end"/></w:r>\n'
            f'</w:p>'
        )
        
        # Replace children of p._p
        for child in list(p._p):
            p._p.remove(child)
        for child in list(fld_xml):
            p._p.append(child)
            
        # Ensure sectPr has pgNumType start="1"
        sectPr = section._sectPr
        pgNum = sectPr.find(qn('w:pgNumType'))
        if pgNum is None:
            pgNum = OxmlElement('w:pgNumType')
            sectPr.append(pgNum)
        pgNum.set(qn('w:start'), '1')
        if qn('w:fmt') in pgNum.attrib:
            del pgNum.attrib[qn('w:fmt')] # decimal
            
    doc.save(doc_path)
    print(f"Successfully added Arabic page numbers to: {doc_path}")

if __name__ == '__main__':
    add_footer_page_number('report/Part B_26AI09.docx')
    add_footer_page_number('report/Part B_Batch_number.docx')
