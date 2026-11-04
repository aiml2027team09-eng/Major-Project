import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def configure_a4_margins(doc):
    for sec in doc.sections:
        sec.page_width = Inches(8.27)   # 210 mm
        sec.page_height = Inches(11.69) # 297 mm
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)
        
        # Remove headers and footers completely (No page numbers!)
        sec.different_first_page_header_footer = False
        sec.header.is_linked_to_previous = False
        sec.footer.is_linked_to_previous = False
        
        for p in list(sec.header.paragraphs):
            p._p.getparent().remove(p._p)
        empty_hp = parse_xml(r'<w:p %s><w:pPr><w:pStyle w:val="Header"/></w:pPr></w:p>' % nsdecls('w'))
        sec.header._element.append(empty_hp)
        
        for p in list(sec.footer.paragraphs):
            p._p.getparent().remove(p._p)
        empty_fp = parse_xml(r'<w:p %s><w:pPr><w:pStyle w:val="Footer"/></w:pPr></w:p>' % nsdecls('w'))
        sec.footer._element.append(empty_fp)
        
        # Strip header/footer references from sectPr
        sectPr = sec._sectPr
        for child in list(sectPr):
            tag = child.tag.split('}')[-1]
            if tag in ['headerReference', 'footerReference']:
                sectPr.remove(child)

def set_cell_margins(cell, top=3, bottom=3, left=5, right=5):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(int(val * 20)))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_table_borders(table, color="B0B0B0", sz="4"):
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)

def add_p(doc, text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=3.5, line_spacing=1.06, font_size=10, bold=False, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.left_indent = Inches(0)
    p.paragraph_format.right_indent = Inches(0)
    if text:
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.font.bold = True
    r.font.italic = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_equation_box(doc, eq_text, eq_number):
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tbl.columns[0].width = Inches(5.6)
    tbl.columns[1].width = Inches(0.67)
    
    c0 = tbl.cell(0, 0)
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(1.5)
    p0.paragraph_format.space_after = Pt(1.5)
    r0 = p0.add_run(eq_text)
    r0.font.name = "Times New Roman"
    r0.font.size = Pt(9.5)
    r0.font.italic = True
    
    c1 = tbl.cell(0, 1)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p1.paragraph_format.space_before = Pt(1.5)
    p1.paragraph_format.space_after = Pt(1.5)
    r1 = p1.add_run(f"({eq_number})")
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(9.5)
    
    tblPr = tbl._tbl.tblPr
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="none"/>\n'
        f'  <w:bottom w:val="none"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'  <w:insideH w:val="none"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)

def add_figure_with_caption(doc, image_path, fig_num, caption_title, caption_desc, width_inches=5.8):
    if os.path.exists(image_path):
        p_img = doc.add_paragraph()
        p_img.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.paragraph_format.keep_with_next = True
        r_img = p_img.add_run()
        r_img.add_picture(image_path, width=Inches(width_inches))
        
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(8)
        
        r_tag = p_cap.add_run(f"FIGURE {fig_num}: ")
        r_tag.font.name = "Times New Roman"
        r_tag.font.size = Pt(9.5)
        r_tag.font.bold = True
        
        r_title = p_cap.add_run(f"{caption_title}. ")
        r_title.font.name = "Times New Roman"
        r_title.font.size = Pt(9.5)
        r_title.font.bold = True
        
        r_desc = p_cap.add_run(caption_desc)
        r_desc.font.name = "Times New Roman"
        r_desc.font.size = Pt(9.0)
        r_desc.font.italic = False

def add_table_caption(doc, table_num, title):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    
    r_tag = p.add_run(f"TABLE {table_num}: ")
    r_tag.font.name = "Times New Roman"
    r_tag.font.size = Pt(9.5)
    r_tag.font.bold = True
    
    r_title = p.add_run(title)
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(9.5)
    r_title.font.bold = True
    return p

print("Loaded base formatting utilities.")
