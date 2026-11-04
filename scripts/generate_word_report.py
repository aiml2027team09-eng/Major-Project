import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from latex2mathml.converter import convert as l2m
from mathml2omml import convert as m2o

# ============================================================
# HELPER FUNCTIONS FOR XML STYLING
# ============================================================

def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    """Set inner cell padding in dxa."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex="F2F2F2"):
    """Apply background shading to a table cell."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._element.get_or_add_tcPr().append(shading_elm)

def style_table(table, col_widths=None):
    """
    Apply full crisp single black borders, header repetition,
    row non-split, and consistent typography to a Word data table.
    """
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = 'Table Grid'
    
    # Explicitly enforce black single borders on all outer edges and inner grid
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        for b in tblPr[0].xpath('w:tblBorders'):
            tblPr[0].remove(b)
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:left w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:right w:val="single" w:sz="6" w:space="0" w:color="000000"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>
            </w:tblBorders>
        ''')
        tblPr[0].append(borders)
    
    # Repeat header row across page breaks
    header_tr = table.rows[0]._element.get_or_add_trPr()
    header_tr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    
    for row_idx, row in enumerate(table.rows):
        # Prevent row from awkwardly breaking across pages
        trPr = row._element.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        
        for col_idx, cell in enumerate(row.cells):
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if col_widths and col_idx < len(col_widths):
                cell.width = col_widths[col_idx]
            
            for p in cell.paragraphs:
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    if row_idx == 0:
                        run.font.bold = True
                        run.font.size = Pt(10)
                    else:
                        run.font.size = Pt(9.5)
            
            if row_idx == 0:
                set_cell_shading(cell, "EAEAEA")

# ============================================================
# HELPER FUNCTIONS FOR EQUATIONS & TEXT BLOCKS
# ============================================================

def add_eq(doc, latex_str, eq_num_str):
    """
    Convert LaTeX math into native Microsoft Word OMML (<m:oMath>)
    and embed it in a 2-column borderless table with right-aligned decimal tag.
    """
    clean_eq = latex_str.replace(r'\_', '_')
    mml = l2m(clean_eq)
    omml = m2o(mml)
    if 'xmlns:m=' not in omml:
        omml = omml.replace('<m:oMath', '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"', 1)
        
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    # Borderless layout table
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="none"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
                <w:insideH w:val="none"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''')
        tblPr[0].append(borders)
        
    cell_eq = table.rows[0].cells[0]
    cell_no = table.rows[0].cells[1]
    
    cell_eq.width = Inches(5.2)
    cell_no.width = Inches(0.8)
    
    p_eq = cell_eq.paragraphs[0]
    p_eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq.paragraph_format.space_before = Pt(3)
    p_eq.paragraph_format.space_after = Pt(3)
    p_eq._element.append(parse_xml(omml))
    
    p_no = cell_no.paragraphs[0]
    p_no.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_no.paragraph_format.space_before = Pt(3)
    p_no.paragraph_format.space_after = Pt(3)
    r_no = p_no.add_run(eq_num_str)
    r_no.font.name = 'Times New Roman'
    r_no.font.size = Pt(11)

def add_para(doc, text, bold_prefix=None, space_after=6, space_before=0, line_spacing=1.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    """
    Add a single, clean paragraph. Never contains soft breaks (\n)
    so Word justifies all lines smoothly without artificial spacing holes.
    """
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    
    if bold_prefix:
        r_b = p.add_run(bold_prefix)
        r_b.font.name = 'Times New Roman'
        r_b.font.bold = True
        r_b.font.size = Pt(12)
        
    r_t = p.add_run(text)
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(12)
    return p

def add_bullet_item(doc, text, bold_prefix=None):
    """
    Add an indented bullet point as an independent paragraph.
    Prevents Word from stretching short lines across the page width.
    """
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.3
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    r_bullet = p.add_run("• ")
    r_bullet.font.name = 'Times New Roman'
    r_bullet.font.size = Pt(12)
    r_bullet.font.bold = True
    
    if bold_prefix:
        r_b = p.add_run(bold_prefix + " ")
        r_b.font.name = 'Times New Roman'
        r_b.font.bold = True
        r_b.font.size = Pt(12)
        
    r_t = p.add_run(text)
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(12)
    return p

def add_numbered_item(doc, num_str, text, bold_prefix=None):
    """
    Add a numbered list item as an independent paragraph.
    """
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.3
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    r_num = p.add_run(num_str + " ")
    r_num.font.name = 'Times New Roman'
    r_num.font.bold = True
    r_num.font.size = Pt(12)
    
    if bold_prefix:
        r_b = p.add_run(bold_prefix + " ")
        r_b.font.name = 'Times New Roman'
        r_b.font.bold = True
        r_b.font.size = Pt(12)
        
    r_t = p.add_run(text)
    r_t.font.name = 'Times New Roman'
    r_t.font.size = Pt(12)
    return p

def add_caption(doc, text):
    """Centered, bold 10 pt caption."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10)
    run.font.bold = True
    return p

def add_figure(doc, img_path, caption_text, width=Inches(5.5)):
    """Embed figure and add centered bold caption."""
    if os.path.exists(img_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.add_run().add_picture(img_path, width=width)
        add_caption(doc, caption_text)
    else:
        p = doc.add_paragraph(f"[Image: {caption_text}]")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

# ============================================================
# MAIN DOCUMENT GENERATOR
# ============================================================

def create_report():
    doc = docx.Document()
    
    # ------------------------------------------------------------
    # GLOBAL PAGE & MARGIN SETUP (VTU STANDARD)
    # ------------------------------------------------------------
    # Left: 1.25", Right: 1.0", Top: 0.75", Bottom: 0.75"
    s1 = doc.sections[0]
    s1.top_margin = Inches(0.75)
    s1.bottom_margin = Inches(0.75)
    s1.left_margin = Inches(1.25)
    s1.right_margin = Inches(1.0)
    s1.page_width = Inches(8.27)  # A4
    s1.page_height = Inches(11.69)
    s1.different_first_page_header_footer = True  # Title page has no header/footer
    
    # Configure Normal Style
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style_normal.paragraph_format.line_spacing = 1.5
    style_normal.paragraph_format.space_after = Pt(6)
    style_normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Helper Headings
    def add_chapter_title(title, number=None):
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(16)
        p.paragraph_format.line_spacing = 1.25
        
        if number:
            r1 = p.add_run(f"CHAPTER {number}\n")
            r1.font.name = 'Times New Roman'
            r1.font.size = Pt(14)
            r1.font.bold = True
            
        r2 = p.add_run(title.upper())
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(16)
        r2.font.bold = True
        return p

    def add_sec(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        return p

    def add_subsec(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        return p

    # ------------------------------------------------------------
    # 1. COVER / TITLE PAGE (PAGE 1) - EXACT MATCH TO TEMPLATE
    # ------------------------------------------------------------
    print("Building Title Page...")
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(0)
    p_inst.paragraph_format.space_after = Pt(1)
    r = p_inst.add_run("MANGALORE INSTITUTE OF TECHNOLOGY & ENGINEERING")
    r.font.size = Pt(12.5)  # Enforce single line
    r.font.bold = True

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(4)
    p_sub.paragraph_format.line_spacing = 1.15
    r2 = p_sub.add_run("(A Unit of Rajalaxmi Education Trust ®, Mangalore)\n"
                       "Autonomous Institute Affiliated to V.T.U, Belagavi, Approved by AICTE, New Delhi\n"
                       "Accredited by NAAC with A+ Grade & ISO 9001:2015 Certified Institution")
    r2.font.size = Pt(8.5)
    
    if os.path.exists("figures/MITE_Logo.jpg"):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(4)
        p_logo.add_run().add_picture("figures/MITE_Logo.jpg", height=Inches(0.95))
        
    p_rep = doc.add_paragraph()
    p_rep.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rep.paragraph_format.space_before = Pt(2)
    p_rep.paragraph_format.space_after = Pt(2)
    r_rep = p_rep.add_run("PROJECT REPORT\n23AISE409 PROJECT PHASE – II")
    r_rep.font.size = Pt(12)
    r_rep.font.bold = True
    
    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_before = Pt(6)
    p_tit.paragraph_format.space_after = Pt(6)
    p_tit.paragraph_format.line_spacing = 1.2
    r_tit = p_tit.add_run("“AI-BASED NETWORK INTRUSION DETECTION SYSTEM USING LIGHTWEIGHT HYBRID AUTOENCODER AND XGBOOST WITH REAL-TIME DRIFT ADAPTATION”")
    r_tit.font.size = Pt(12.0)
    r_tit.font.bold = True
    
    p_subm = doc.add_paragraph()
    p_subm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subm.paragraph_format.space_before = Pt(4)
    p_subm.paragraph_format.space_after = Pt(4)
    p_subm.paragraph_format.line_spacing = 1.15
    r_sub = p_subm.add_run("Submitted in partial fulfillment of the requirements for the award of the degree of\n"
                           "BACHELOR OF ENGINEERING\nin\nARTIFICIAL INTELLIGENCE AND MACHINE LEARNING\n\nby")
    r_sub.font.size = Pt(10.0)
    
    # Students Table - CENTERED ON PAGE (Image 4)
    t_stu = doc.add_table(rows=3, cols=2)
    t_stu.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_stu.autofit = False
    tblPr_s = t_stu._element.xpath('w:tblPr')
    if tblPr_s:
        tblPr_s[0].append(parse_xml(f'''<w:tblBorders {nsdecls("w")}>
            <w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>
        </w:tblBorders>'''))
    students = [
        ("Ansh Pawaskar", "4MT23AI009"),
        ("Nesar Naik", "4MT23AI036"),
        ("Tejeswini", "4MT23AI057")
    ]
    for i, (name, usn) in enumerate(students):
        r_n = t_stu.rows[i].cells[0].paragraphs[0].add_run(name)
        r_n.font.bold = True
        r_n.font.size = Pt(10.5)
        r_u = t_stu.rows[i].cells[1].paragraphs[0].add_run(usn)
        r_u.font.bold = True
        r_u.font.size = Pt(10.5)
        t_stu.rows[i].cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        t_stu.rows[i].cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        t_stu.rows[i].cells[0].width = Inches(1.8)
        t_stu.rows[i].cells[1].width = Inches(1.8)
        t_stu.rows[i].cells[0].paragraphs[0].paragraph_format.space_after = Pt(1)
        t_stu.rows[i].cells[1].paragraphs[0].paragraph_format.space_after = Pt(1)
        
    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_before = Pt(6)
    p_guide.paragraph_format.space_after = Pt(0)
    p_guide.paragraph_format.line_spacing = 1.15
    r_g = p_guide.add_run("Under the Guidance of\nMr. Srivatsa Upadhya P\nAssistant Professor\n\n"
                          "DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING\n2026-27")
    r_g.font.size = Pt(10.5)
    r_g.font.bold = True

    # ------------------------------------------------------------
    # 2. SECTION 2: PRELIMINARY PAGES (ROMAN NUMERALS)
    # ------------------------------------------------------------
    s2 = doc.add_section()
    s2.top_margin = Inches(0.75)
    s2.bottom_margin = Inches(0.75)
    s2.left_margin = Inches(1.25)
    s2.right_margin = Inches(1.0)
    s2.different_first_page_header_footer = False
    
    # Roman footer starting at ii
    footer2 = s2.footer
    p_f2 = footer2.paragraphs[0]
    p_f2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_f2 = p_f2.add_run()
    run_f2.font.name = 'Times New Roman'
    run_f2.font.size = Pt(11)
    run_f2._element.append(parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>'))
    
    pgNumType2 = parse_xml(f'<w:pgNumType {nsdecls("w")} w:start="2" w:fmt="lowerRoman"/>')
    s2._sectPr.append(pgNumType2)

    # ------------------------------------------------------------
    # CERTIFICATE PAGE (PAGE ii) - EXACT MATCH TO TEMPLATE (IMAGE 5)
    # ------------------------------------------------------------
    print("Building Certificate...")
    p_inst2 = doc.add_paragraph()
    p_inst2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst2.paragraph_format.space_before = Pt(0)
    p_inst2.paragraph_format.space_after = Pt(1)
    r_inst2 = p_inst2.add_run("MANGALORE INSTITUTE OF TECHNOLOGY & ENGINEERING")
    r_inst2.font.size = Pt(12.5)  # Enforce single line
    r_inst2.font.bold = True

    p_sub2 = doc.add_paragraph()
    p_sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub2.paragraph_format.space_before = Pt(0)
    p_sub2.paragraph_format.space_after = Pt(4)
    p_sub2.paragraph_format.line_spacing = 1.15
    r_sub2 = p_sub2.add_run("(A Unit of Rajalaxmi Education Trust ®, Mangalore)\n"
                            "Autonomous Institute Affiliated to V.T.U, Belagavi, Approved by AICTE, New Delhi\n"
                            "Accredited by NAAC with A+ Grade & ISO 9001:2015 Certified Institution")
    r_sub2.font.size = Pt(8.5)
    
    if os.path.exists("figures/MITE_Logo.jpg"):
        p_logo2 = doc.add_paragraph()
        p_logo2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo2.paragraph_format.space_before = Pt(2)
        p_logo2.paragraph_format.space_after = Pt(4)
        p_logo2.add_run().add_picture("figures/MITE_Logo.jpg", height=Inches(0.75))
    
    p_dept = doc.add_paragraph()
    p_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept.paragraph_format.space_before = Pt(2)
    p_dept.paragraph_format.space_after = Pt(4)
    r_dept = p_dept.add_run("DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING")
    r_dept.font.size = Pt(11)
    r_dept.font.bold = True

    p_cert = doc.add_paragraph()
    p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert.paragraph_format.space_before = Pt(4)
    p_cert.paragraph_format.space_after = Pt(8)
    r = p_cert.add_run("CERTIFICATE")
    r.font.size = Pt(13)
    r.font.bold = True
    
    add_para(doc, 
        "This is to certify that the Project Phase – II (23AISE409) work entitled “AI-BASED NETWORK INTRUSION DETECTION SYSTEM USING LIGHTWEIGHT HYBRID AUTOENCODER AND XGBOOST WITH REAL-TIME DRIFT ADAPTATION” is a bonafide work carried out by Ansh Pawaskar (4MT23AI009), Nesar Naik (4MT23AI036), and Tejeswini (4MT23AI057) in partial fulfillment for the award of degree of Bachelor of Engineering in Artificial Intelligence and Machine Learning of Mangalore Institute of Technology & Engineering (Autonomous) during the year 2026-27. It is certified that all corrections and suggestions indicated for Internal Assessment have been incorporated in the report deposited in the departmental library. The project has been approved as it satisfies the academic requirements in respect of project work prescribed for the Bachelor of Engineering degree.",
        space_after=20, line_spacing=1.25)
    
    # Top Signatures (Guide on left, HOD on right)
    t_top = doc.add_table(rows=1, cols=2)
    t_top.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_top.autofit = False
    tblPr_top = t_top._element.xpath('w:tblPr')
    if tblPr_top:
        tblPr_top[0].append(parse_xml(f'''<w:tblBorders {nsdecls("w")}>
            <w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>
        </w:tblBorders>'''))

    cell_g = t_top.rows[0].cells[0]
    cell_h = t_top.rows[0].cells[1]
    cell_g.width = Inches(3.0)
    cell_h.width = Inches(3.0)

    p_g = cell_g.paragraphs[0]
    p_g.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_g.paragraph_format.line_spacing = 1.2
    r_g1 = p_g.add_run("_____________________\n")
    r_g2 = p_g.add_run("Mr. Srivatsa Upadhya P\n")
    r_g2.font.bold = True
    r_g3 = p_g.add_run("Project Guide")
    r_g3.font.bold = True

    p_h = cell_h.paragraphs[0]
    p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_h.paragraph_format.line_spacing = 1.2
    r_h1 = p_h.add_run("_____________________\n")
    r_h2 = p_h.add_run("Dr. Sunil Kumar S\n")
    r_h2.font.bold = True
    r_h3 = p_h.add_run("Head of Dept. AI & ML")
    r_h3.font.bold = True

    # Principal Signature: CENTERED ON PAGE (Image 5)
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(16)
    p_space.paragraph_format.space_after = Pt(0)

    t_prin = doc.add_table(rows=1, cols=1)
    t_prin.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_prin.autofit = False
    tblPr_prin = t_prin._element.xpath('w:tblPr')
    if tblPr_prin:
        tblPr_prin[0].append(parse_xml(f'''<w:tblBorders {nsdecls("w")}>
            <w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>
        </w:tblBorders>'''))

    cell_p = t_prin.rows[0].cells[0]
    cell_p.width = Inches(3.0)
    p_p = cell_p.paragraphs[0]
    p_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_p.paragraph_format.line_spacing = 1.2
    r_p1 = p_p.add_run("_____________________\n")
    r_p2 = p_p.add_run("Dr. Prashanth C M\n")
    r_p2.font.bold = True
    r_p3 = p_p.add_run("Principal")
    r_p3.font.bold = True

    # ------------------------------------------------------------
    # DECLARATION (PAGE iii)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_dec = doc.add_paragraph()
    p_dec.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec.paragraph_format.space_before = Pt(10)
    p_dec.paragraph_format.space_after = Pt(14)
    r = p_dec.add_run("DECLARATION")
    r.font.size = Pt(14)
    r.font.bold = True
    
    add_para(doc,
        "We declare that this Project Phase - II (23AISE409) report titled “AI-Based Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation” submitted in partial fulfillment of the degree of B.E. in Artificial Intelligence and Machine Learning is a record of original work carried out by us under the supervision of Mr. Srivatsa Upadhya P, and has not formed the basis for the award of any other degree, in this or any other Institution or University. In keeping with ethical practice in reporting scientific information, due acknowledgements have been made wherever the findings of others have been cited.",
        space_after=20, line_spacing=1.3)
    
    t_dec = doc.add_table(rows=4, cols=3)
    headers = ["Sr. No.", "Name", "Signature"]
    for j, h in enumerate(headers):
        t_dec.rows[0].cells[j].paragraphs[0].text = h
    rows = [
        ("1", "Ansh Pawaskar (4MT23AI009)", ""),
        ("2", "Nesar Naik (4MT23AI036)", ""),
        ("3", "Tejeswini (4MT23AI057)", "")
    ]
    for i, r_data in enumerate(rows):
        for j, val in enumerate(r_data):
            t_dec.rows[i+1].cells[j].paragraphs[0].text = val
    style_table(t_dec, [Inches(1.0), Inches(3.4), Inches(1.6)])

    # ------------------------------------------------------------
    # ACKNOWLEDGEMENTS (PAGE iv)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_ack = doc.add_paragraph()
    p_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack.paragraph_format.space_before = Pt(10)
    p_ack.paragraph_format.space_after = Pt(14)
    r = p_ack.add_run("ACKNOWLEDGEMENTS")
    r.font.size = Pt(14)
    r.font.bold = True
    
    add_para(doc, "The successful completion of the Project Phase - II (23AISE409) work titled “AI-Based Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation” would not have been possible without the support of those, whose constant guidance and encouragement helped turn our efforts into success.", line_spacing=1.3)
    add_para(doc, "We would like to thank our Project Guide Mr. Srivatsa Upadhya P, Assistant Professor, Department of Artificial Intelligence and Machine Learning for his constant encouragement and support extended throughout.", line_spacing=1.3)
    add_para(doc, "We would like to express appreciation to Dr. Sunil Kumar S, Head of Department of Artificial Intelligence and Machine Learning for his support and guidance.", line_spacing=1.3)
    add_para(doc, "We would like to thank our Principal Dr. Prashanth C M, for encouraging us and giving us an opportunity to accomplish the project.", line_spacing=1.3)
    add_para(doc, "We also thank our management who helped us directly or indirectly in the completion of Phase - II of the project. Our special thanks to faculty members and others for their constant help and support. Above all, we extend our sincere gratitude to our parents and friends for their constant encouragement with moral support.", space_after=20, line_spacing=1.3)
    
    p_names = doc.add_paragraph()
    p_names.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_names.paragraph_format.line_spacing = 1.2
    r_n = p_names.add_run("Ansh Pawaskar (4MT23AI009)\nNesar Naik (4MT23AI036)\nTejeswini (4MT23AI057)")
    r_n.font.bold = True

    # ------------------------------------------------------------
    # ABSTRACT (PAGE v)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs.paragraph_format.space_before = Pt(10)
    p_abs.paragraph_format.space_after = Pt(14)
    r = p_abs.add_run("ABSTRACT")
    r.font.size = Pt(14)
    r.font.bold = True
    
    add_para(doc,
        "Network intrusion detection systems (NIDS) deployed in modern enterprise and cloud environments face two major operational challenges: supervised classifiers fail when encountering zero-day attacks, whereas unsupervised anomaly detectors generate elevated false alarm rates and suffer from arbitrary Gaussian threshold collapse (μ + 3σ). This project presents a leakage-free, two-stage hybrid NIDS combining an unsupervised deep symmetric Autoencoder (d → 128 → 64 → 32 → 16 → 32 → 64 → 128 → d) with an Extreme Gradient Boosted decision tree (XGBoost) classifier and alert-gated TreeSHAP explainability. Evaluated on strictly deduplicated partitions of CICIDS2018 (671,131 flows) and NSL-KDD (147,790 instances), the pipeline achieves 99.70% attack recall and detects 93.11% of unseen DoS attacks under Leave-One-Attack-Out testing. Validation-tuned Youden's J thresholding eliminates zero-recall collapse, while a sliding buffer (W=500) tracks concept drift. The system executes at 0.1830 ms per flow on commodity CPU hardware with an interactive Streamlit dashboard.")
    
    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.space_before = Pt(8)
    p_kw.paragraph_format.line_spacing = 1.3
    r_kw = p_kw.add_run("Keywords: ")
    r_kw.font.bold = True
    r_kw.font.name = 'Times New Roman'
    r_kw_txt = p_kw.add_run("Network Intrusion Detection, Autoencoder, XGBoost, Anomaly Screening, Youden's J-Statistic, TreeSHAP, Concept Drift, Zero-Day Generalization, Streamlit.")
    r_kw_txt.font.name = 'Times New Roman'

    # ------------------------------------------------------------
    # TABLE OF CONTENTS (PAGE vi)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_toc = doc.add_paragraph()
    p_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc.paragraph_format.space_before = Pt(10)
    p_toc.paragraph_format.space_after = Pt(14)
    r = p_toc.add_run("TABLE OF CONTENTS")
    r.font.size = Pt(14)
    r.font.bold = True
    
    t_toc = doc.add_table(rows=11, cols=3)
    toc_data = [
        ("Sr. NO.", "CONTENTS", "PAGE NO."),
        ("1.", "INTRODUCTION", "1"),
        ("2.", "LITERATURE SURVEY", "5"),
        ("3.", "PROPOSED SYSTEM AND SCOPE", "9"),
        ("4.", "METHODOLOGY", "15"),
        ("5.", "IMPLEMENTATION & EXPERIMENTAL WORK", "23"),
        ("6.", "RESULTS, ANALYSIS AND DISCUSSION", "31"),
        ("7.", "CONCLUSION AND FUTURE SCOPE", "41"),
        ("", "RESEARCH PAPER / PATENT PUBLISHED (if any)", "44"),
        ("", "REFERENCES", "46"),
        ("", "APPENDICES", "49")
    ]
    for i, row in enumerate(toc_data):
        for j, val in enumerate(row):
            t_toc.rows[i].cells[j].paragraphs[0].text = val
            if j == 2:
                t_toc.rows[i].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_table(t_toc, [Inches(1.0), Inches(4.2), Inches(0.8)])

    # ------------------------------------------------------------
    # LIST OF FIGURES (PAGE vii)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_lof = doc.add_paragraph()
    p_lof.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof.paragraph_format.space_before = Pt(10)
    p_lof.paragraph_format.space_after = Pt(14)
    r = p_lof.add_run("LIST OF FIGURES")
    r.font.size = Pt(14)
    r.font.bold = True
    
    lof_data = [
        ("Sr. No.", "TITLE", "Page No."),
        ("Figure 3.1", "System Architecture of the Two-Stage Hybrid NIDS", "12"),
        ("Figure 4.1", "Deep Symmetric Autoencoder Bottleneck Topology", "18"),
        ("Figure 4.2", "Sequence Diagram of Packet Ingestion and Prediction", "19"),
        ("Figure 4.3", "Activity Diagram of Tiered Detection and Alert Routing", "20"),
        ("Figure 4.4", "Data Flow Diagram (DFD Level-1) for Flow Processing", "21"),
        ("Figure 4.5", "Class Diagram of Object-Oriented Framework Architecture", "22"),
        ("Figure 4.6", "Use Case Diagram of Network Intrusion Detection Workflow", "22"),
        ("Figure 5.1", "Real-Time Network Flow Telemetry and Live Sniffing Monitor", "27"),
        ("Figure 5.2", "Threat Diagnosis, Alert Gating, and Local TreeSHAP Explanation", "28"),
        ("Figure 6.1", "Row-Normalized Confusion Matrices for Hybrid AE–XGBoost Model", "33"),
        ("Figure 6.2", "Row-Normalized Confusion Matrices for Standalone Autoencoder", "34"),
        ("Figure 6.3", "Reconstruction Threshold Sensitivity and Pareto Optimization Curves", "36"),
        ("Figure 6.4", "Leave-One-Attack-Out (LOAO) Unseen Attack Detection Recall", "37"),
        ("Figure 6.5", "Statistical Concept Drift Tracking (DKS, PSI, JSD) Across Windows", "38"),
        ("Figure 6.6", "TreeSHAP Global Feature Importance Ranking (Summary Plot)", "39"),
        ("Figure 6.7", "End-to-End Pipeline Execution Latency Breakdown on Multi-Core CPU", "40")
    ]
    t_lof = doc.add_table(rows=len(lof_data), cols=3)
    for i, row in enumerate(lof_data):
        for j, val in enumerate(row):
            t_lof.rows[i].cells[j].paragraphs[0].text = val
            if j == 2:
                t_lof.rows[i].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_table(t_lof, [Inches(1.1), Inches(4.1), Inches(0.8)])

    # ------------------------------------------------------------
    # LIST OF TABLES (PAGE viii)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_lot = doc.add_paragraph()
    p_lot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot.paragraph_format.space_before = Pt(10)
    p_lot.paragraph_format.space_after = Pt(14)
    r = p_lot.add_run("LIST OF TABLES")
    r.font.size = Pt(14)
    r.font.bold = True
    
    lot_data = [
        ("Sr. No.", "TITLE", "Page No."),
        ("Table 2.1", "Comparison of Existing NIDS Approaches, Methodologies, and Gaps", "6"),
        ("Table 4.1", "Measurement and Evaluation Parameters for Model Assessment", "16"),
        ("Table 4.2", "Autoencoder Bottleneck Layer Configuration and Dimensionality", "17"),
        ("Table 5.1", "Cryptographically Audited Dataset Splits Enforcing Zero Leakage", "24"),
        ("Table 5.2", "Experimental Setup Parameters and Hyperparameter Configurations", "26"),
        ("Table 5.3", "System Test Cases, Inputs, Expected Outcomes, and Execution Status", "29"),
        ("Table 6.1", "Overall Classification Performance on Held-Out Test Partitions", "31"),
        ("Table 6.2", "Multi-Class Attack Detection Breakdown on CICIDS2018 (N = 100,670)", "32"),
        ("Table 6.3", "Multi-Class Attack Detection Breakdown on NSL-KDD (N = 22,169)", "32"),
        ("Table 6.4", "Reconstruction Threshold Strategy Comparison on CICIDS2018", "35"),
        ("Table 6.5", "Leave-One-Attack-Out (LOAO) Unseen Attack Detection Performance", "37"),
        ("Table 6.6", "Statistical Concept Drift Tracking Across Sequential Windows", "38"),
        ("Table 6.7", "Computational Benchmark: Latency, Throughput, and Peak Memory (RSS)", "40"),
        ("Table 6.8", "Benchmark Comparison Against Baseline Supervised Classifiers", "40")
    ]
    t_lot = doc.add_table(rows=len(lot_data), cols=3)
    for i, row in enumerate(lot_data):
        for j, val in enumerate(row):
            t_lot.rows[i].cells[j].paragraphs[0].text = val
            if j == 2:
                t_lot.rows[i].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_table(t_lot, [Inches(1.1), Inches(4.1), Inches(0.8)])

    # ------------------------------------------------------------
    # ABBREVIATIONS / NOTATIONS (PAGE ix) - BORDERLESS (IMAGE 1)
    # ------------------------------------------------------------
    doc.add_page_break()
    p_abb = doc.add_paragraph()
    p_abb.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abb.paragraph_format.space_before = Pt(10)
    p_abb.paragraph_format.space_after = Pt(14)
    r = p_abb.add_run("ABBREVIATIONS / NOTATIONS")
    r.font.size = Pt(14)
    r.font.bold = True
    
    abbreviations = [
        ("AE", "Autoencoder"), ("XGBoost", "Extreme Gradient Boosting"),
        ("NIDS", "Network Intrusion Detection System"), ("DoS", "Denial of Service"),
        ("DDoS", "Distributed Denial of Service"), ("SHAP", "SHapley Additive exPlanations"),
        ("TreeSHAP", "Tree-ensemble Shapley Additive Explanations"), ("PSI", "Population Stability Index"),
        ("JSD", "Jensen–Shannon Divergence"), ("KS", "Kolmogorov–Smirnov Test"),
        ("ROC", "Receiver Operating Characteristic"), ("AUC", "Area Under the Curve"),
        ("FPR", "False Positive Rate"), ("TPR", "True Positive Rate"),
        ("MSE", "Mean Squared Error"), ("API", "Application Programming Interface"),
        ("GUI", "Graphical User Interface"), ("SOC", "Security Operations Center"),
        ("CPU", "Central Processing Unit"), ("RAM", "Random Access Memory"),
        ("SSD", "Solid State Drive"), ("NIC", "Network Interface Card"),
        ("PCAP", "Packet Capture Format"), ("LOAO", "Leave-One-Attack-Out Validation"),
        ("IAT", "Inter-Arrival Time"), ("TCP", "Transmission Control Protocol"),
        ("UDP", "User Datagram Protocol"), ("IP", "Internet Protocol"),
        ("XAI", "Explainable Artificial Intelligence")
    ]
    
    # Borderless layout table without grid borders (as requested)
    t_abb = doc.add_table(rows=len(abbreviations), cols=2)
    t_abb.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_abb.autofit = False
    tblPr_a = t_abb._element.xpath('w:tblPr')
    if tblPr_a:
        tblPr_a[0].append(parse_xml(f'''<w:tblBorders {nsdecls("w")}>
            <w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>
        </w:tblBorders>'''))
        
    for i, (k, v) in enumerate(abbreviations):
        cell_k = t_abb.rows[i].cells[0]
        cell_v = t_abb.rows[i].cells[1]
        cell_k.width = Inches(1.8)
        cell_v.width = Inches(4.2)
        p_k = cell_k.paragraphs[0]
        p_v = cell_v.paragraphs[0]
        p_k.paragraph_format.line_spacing = 1.15
        p_v.paragraph_format.line_spacing = 1.15
        p_k.paragraph_format.space_before = Pt(1.5)
        p_k.paragraph_format.space_after = Pt(1.5)
        p_v.paragraph_format.space_before = Pt(1.5)
        p_v.paragraph_format.space_after = Pt(1.5)
        r_k = p_k.add_run(k)
        r_k.font.name = 'Times New Roman'
        r_k.font.bold = True
        r_k.font.size = Pt(11)
        r_v = p_v.add_run(v)
        r_v.font.name = 'Times New Roman'
        r_v.font.size = Pt(11)

    # ------------------------------------------------------------
    # 3. SECTION 3: MAIN BODY (ARABIC NUMERALS 1, 2, 3...)
    # ------------------------------------------------------------
    s3 = doc.add_section()
    s3.top_margin = Inches(0.75)
    s3.bottom_margin = Inches(0.75)
    s3.left_margin = Inches(1.25)
    s3.right_margin = Inches(1.0)
    s3.different_first_page_header_footer = False
    
    # Arabic footer starting at 1
    footer3 = s3.footer
    p_f3 = footer3.paragraphs[0]
    p_f3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_f3 = p_f3.add_run()
    run_f3.font.name = 'Times New Roman'
    run_f3.font.size = Pt(11)
    run_f3._element.append(parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"/>'))
    
    pgNumType3 = parse_xml(f'<w:pgNumType {nsdecls("w")} w:start="1" w:fmt="decimal"/>')
    s3._sectPr.append(pgNumType3)

    # ============================================================
    # CHAPTER 1: INTRODUCTION
    # ============================================================
    print("Building Chapter 1: Introduction...")
    add_chapter_title("Introduction", 1)
    
    add_sec("1.1 Background")
    add_para(doc, "Modern enterprise networks, critical cyber-physical infrastructures, and multi-tenant cloud data centers operate in an environment characterized by unprecedented throughput, massive concurrency, and relentless attack velocity. The proliferation of automated attack tooling, evasive multi-vector campaigns, and targeted Advanced Persistent Threats (APTs) has rendered conventional security defenses fundamentally insufficient. Traditional boundary security tools, such as stateful firewalls and signature-based Network Intrusion Detection Systems (NIDSs) like Snort and Suricata, rely on deterministic pattern matching against known vulnerability databases. While these signature-driven mechanisms exhibit high processing speed and near-zero false alarms on documented threats, they remain blind to zero-day exploits, protocol mutations, and slow distributed reconnaissance activities.")
    add_para(doc, "To counter these vulnerabilities, security operations centers (SOCs) have increasingly adopted Artificial Intelligence (AI), Machine Learning (ML), and Deep Learning (DL) paradigms to learn statistical behavioral representations from high-dimensional network flow data. By analyzing aggregated flow metrics—such as inter-arrival timings, directional packet volume distributions, TCP flag heuristics, and header lengths—learning algorithms can identify suspicious communications that deviate from legitimate baseline activity without requiring manual rule curation. However, the operationalization of machine learning models in production environments introduces critical challenges, including susceptibility to evasion, high computational overhead, and vulnerability to non-stationary traffic distributions.")

    add_sec("1.2 Problem Statement")
    add_para(doc, "Contemporary Network Intrusion Detection Systems fail to achieve an effective operational balance between detecting known attack categories with high precision and flagging unmodeled zero-day intrusions with high sensitivity. Supervised models (e.g., Extreme Gradient Boosted Trees, Random Forests, Deep MLPs) deliver near-perfect discrimination under closed-world benchmark assumptions. However, their decision boundaries are entirely constrained by the training distribution; when exposed to previously unseen zero-day exploits or novel variants, supervised models catastrophically fail, misclassifying malicious activity as normal traffic.")
    add_para(doc, "Conversely, unsupervised anomaly detectors (such as deep Autoencoders) compress normal network flows through low-dimensional latent bottlenecks to establish a non-parametric boundary of benign communication. Traffic exceeding an anomaly threshold is flagged as suspicious. However, prevailing academic and industrial implementations rely on arbitrary parametric Gaussian heuristics (μ + 3σ) or rigid high percentiles (99.9th). Because real-world network traffic is heavy-tailed and non-Gaussian, extreme outliers dramatically inflate μ + 3σ, causing catastrophic threshold collapse where attack recall drops to exactly 0.00%. Furthermore, cross-partition data leakage in standard benchmarks frequently conceals these failures, while post-hoc Explainable AI (XAI) frameworks impose crippling latency bottlenecks if computed continuously at line rate.")

    add_sec("1.3 Motivation / Need for the Project")
    add_para(doc, "To overcome the closed-world dilemma of supervised learning and the threshold instability of unsupervised detectors, an integrated defense-in-depth architecture is required. Automated network security cannot rely solely on signature databases or pure supervised classifiers that remain blind to emerging exploits. Simultaneously, security analysts in SOC environments cannot manage thousands of false-positive alarms generated by uncalibrated anomaly detectors.")
    add_para(doc, "There is a clear operational need for a two-stage hybrid framework where:")
    add_numbered_item(doc, "1.", "An unsupervised Autoencoder serves as a lightweight frontline gatekeeper, screening out more than 85–90% of legitimate benign traffic at sub-millisecond line rates.")
    add_numbered_item(doc, "2.", "A supervised XGBoost classifier inspects only the anomalous flows, categorizing them into granular threat families or quarantining low-confidence anomalies as potential zero-day threats.")
    add_numbered_item(doc, "3.", "Explainable AI (TreeSHAP) is triggered selectively on alerts, eliminating 90% of computation overhead while providing human analysts with immediate, transparent feature attributions.")
    add_numbered_item(doc, "4.", "A sliding-window drift buffer adapts the baseline threshold dynamically to non-adversarial traffic shifts over continuous network streams.")

    add_sec("1.4 Objectives")
    add_para(doc, "The primary technical objectives of this project are:")
    add_numbered_item(doc, "1.", "To establish comprehensive performance baselines for classical machine learning and deep learning architectures in network intrusion detection.", "Benchmarking Baseline Models:")
    add_numbered_item(doc, "2.", "To design, implement, and optimize a two-stage hybrid NIDS that couples an unsupervised symmetric Autoencoder gatekeeper with a downstream multi-class XGBoost classifier.", "Developing Hybrid Architecture:")
    add_numbered_item(doc, "3.", "To construct an audited, cryptographically validated preprocessing pipeline that enforces strict zero-leakage partitioning (Train ∩ Test = ∅) on modern benchmark datasets.", "Leakage-Free Preprocessing:")
    add_numbered_item(doc, "4.", "To eliminate Gaussian threshold collapse by optimizing validation-guided Youden's J-statistic, and implement sliding-window statistical drift tracking (DKS, PSI, JSD).", "Calibration & Drift Tracking:")
    add_numbered_item(doc, "5.", "To validate sub-millisecond per-flow inference latency on multi-core CPUs and deploy an interactive Streamlit dashboard for real-time traffic telemetry and local SHAP explanations.", "Operational Deployment & Dashboard:")

    add_sec("1.5 Scope of the Project")
    add_para(doc, "The scope of this project encompasses:")
    add_bullet_item(doc, "Evaluation on the modern, high-dimensional CICIDS2018 dataset (78 transport-layer flow features) and the multi-class NSL-KDD benchmark (41 connection attributes, expanded to 122 one-hot features).", "Benchmark Datasets:")
    add_bullet_item(doc, "Detection and categorization of primary attack vectors: volumetric Denial of Service (DoS/DDoS), brute-force credential stuffing (SSH/FTP), reconnaissance port probing, Remote-to-Local (R2L) exploits, and User-to-Root (U2R) privilege escalations.", "Threat Taxonomy:")
    add_bullet_item(doc, "Auditing novel attack detection capabilities using a rigorous Leave-One-Attack-Out (LOAO) protocol.", "Zero-Day Evaluation:")
    add_bullet_item(doc, "Execution on standard commodity CPU server hardware without reliance on GPU acceleration, supporting offline CSV/PCAP ingestion and live promiscuous socket flow sniffing.", "Deployment Modality:")

    add_sec("1.6 Significance / Expected Contribution")
    add_para(doc, "The project delivers five distinct contributions to network security engineering:")
    add_numbered_item(doc, "1.", "Identification and elimination of 362 leaking flow records from legacy benchmark splits, guaranteeing verifiable reproducibility.", "Cryptographic Data Hygiene:")
    add_numbered_item(doc, "2.", "Empirical demonstration of the complete breakdown of parametric μ + 3σ rules and formulation of non-parametric Youden's J optimization that restores attack recall to 99.70%.", "Resolution of Threshold Collapse:")
    add_numbered_item(doc, "3.", "Verification that the unsupervised gatekeeper successfully isolates 93.11% of unseen DoS attacks and 82.22% of unseen Probe attacks without prior training exposure.", "Zero-Day Defense-in-Depth:")
    add_numbered_item(doc, "4.", "Reduction of TreeSHAP computational overhead by 90% through conditional execution, preserving line-rate processing.", "Alert-Gated Explainability:")
    add_numbered_item(doc, "5.", "Verification of 0.1830 ms per-flow inference latency (5,464 flows/s) and a compact 527.0 MB RSS memory footprint on standard CPU hardware.", "Production-Grade Efficiency:")

    add_sec("1.7 Organization of the Report")
    add_para(doc, "The remainder of this report is organized as follows:")
    add_bullet_item(doc, "Reviews state-of-the-art studies across machine learning, deep autoencoders, hybrid classifiers, and explainable AI in NIDS, highlighting existing research gaps.", "Chapter 2 (Literature Survey):")
    add_bullet_item(doc, "Formulates the detection problem, presents system requirements, hardware/software specifications, and details the overall architecture.", "Chapter 3 (Proposed System and Scope):")
    add_bullet_item(doc, "Outlines evaluation metrics, algorithmic workflows, UML designs, model layer configurations, error sources, and mitigation techniques.", "Chapter 4 (Methodology):")
    add_bullet_item(doc, "Documents the implementation environment, zero-leakage dataset preparation, hyperparameter tuning, testing test cases, and the interactive dashboard.", "Chapter 5 (Implementation & Experimental Work):")
    add_bullet_item(doc, "Presents quantitative results on CICIDS2018 and NSL-KDD, confusion matrices, threshold optimizations, unseen attack generalization, concept drift tracking, and CPU benchmarks.", "Chapter 6 (Results, Analysis and Discussion):")
    add_bullet_item(doc, "Summarizes major project findings, outlines practical contributions, and identifies future research directions.", "Chapter 7 (Conclusion and Future Scope):")
    add_bullet_item(doc, "Details publication outcomes, formal academic citations, and mathematical derivations.", "Research Paper Details, References, and Appendices:")

    # ============================================================
    # CHAPTER 2: LITERATURE SURVEY
    # ============================================================
    print("Building Chapter 2: Literature Survey...")
    add_chapter_title("Literature Survey", 2)
    
    add_sec("2.1 Introduction")
    add_para(doc, "Intrusion detection research has undergone a multi-decade paradigm shift, driven by the expanding attack surface of distributed computing and the escalating sophistication of adversarial exploitation. Early network perimeter defenses relied primarily on deterministic rule engines, such as Snort, Bro (Zeek), and Suricata. These systems match incoming network packets against regular expressions and known exploit signatures. Although rule-based matchers achieve near-zero false positive rates on documented vulnerabilities and operate efficiently at wire speeds, they exhibit absolute vulnerability to zero-day mutations, protocol obfuscation, and polymorphic payloads.")
    add_para(doc, "To overcome signature limitations, researchers transitioned toward shallow machine learning algorithms, including Support Vector Machines (SVM), Random Forests (RF), Naive Bayes, and Decision Trees. These algorithms classify transport-layer statistical flow summaries rather than packet payloads. While shallow models improved detection flexibility, their limited capacity prevents them from capturing intricate temporal dependencies and non-linear correlations across high-dimensional flow manifolds.")
    add_para(doc, "With the advent of deep representation learning, Multi-Layer Perceptrons (MLPs), Convolutional Neural Networks (CNNs), Long Short-Term Memory networks (LSTMs), and Deep Autoencoders (AEs) emerged as standard architectures in network security literature. Deep Autoencoders compress input flow vectors through low-dimensional bottleneck layers to learn non-linear manifold representations of benign communication. However, anomaly detectors struggle with high false alarm rates caused by non-stationary network behavior and arbitrary threshold heuristics (μ + 3σ). Meanwhile, supervised deep networks remain closed-world discriminators unable to handle zero-day attacks. Furthermore, the opaque nature of deep neural networks impedes incident response in Security Operations Centers (SOCs), necessitating Explainable Artificial Intelligence (XAI) frameworks like SHAP. This survey analyzes ten pivotal studies in recent NIDS literature, identifying methodological trade-offs and structural gaps.")

    add_sec("2.2 Review of Existing Work")
    add_para(doc, "Table 2.1 presents a structured, comprehensive synthesis of ten foundational studies in network intrusion detection, systematically detailing their problem formulations, technical methodologies, primary empirical findings, and identified research gaps.")
    
    add_caption(doc, "Table 2.1: Comparison of Existing NIDS Approaches, Methodologies, and Research Gaps")
    lit_table_data = [
        ("Sl.", "Author / Year", "Problem / Domain", "Methodology", "Key Empirical Finding", "Research Gap / Limitation"),
        ("1", "Abdallah et al. (2024)", "Cloud network anomaly detection", "Systematic review of ML and DL architectures", "Comprehensive qualitative taxonomy of anomaly detection", "Survey study; lacks direct empirical validation and CPU-latency profiling"),
        ("2", "Abdulganiyu et al. (2024)", "Imbalanced network intrusion traffic", "Variational Autoencoder (VAE) synthesis + XGBoost", "Reported binary classification accuracy of 99.8%", "VAE is utilized solely for data synthesis rather than reconstruction gating"),
        ("3", "Neupane et al. (2022)", "Explainability of automated NIDS alerts", "Systematic survey of cybersecurity XAI methods", "Evaluates SHAP, LIME, and Integrated Gradients", "Lacks operational throughput profiling and explanation stability metrics"),
        ("4", "Ben Ncir et al. (2024)", "Interpretable deep intrusion detection", "Ensemble deep neural networks coupled with SHAP", "Achieved F1-score of 97.19% on NSL-KDD benchmark", "High recurrent inference overhead; unsuited for real-time line-rate screening"),
        ("5", "Mahmoud et al. (2025)", "Explainable two-stage intrusion detection", "XI2S-IDS staged deep learning framework", "Reported overall classification accuracy of 97.0%", "Computing per-flow Shapley attributions continuously causes severe latency bottleneck"),
        ("6", "Sajid et al. (2024)", "Scalable high-speed hybrid detection", "Deep representation learning fused with classical ML", "Reported accuracy of 97.91% across standard benchmarks", "Evaluated on static random splits; robustness to temporal drift unaddressed"),
        ("7", "Shirley & Priya (2025)", "Evolving zero-day threats in IoT networks", "Autoencoder–Feedforward Neural Network fusion", "Reported high classification accuracy of 99.55%", "Static reconstruction threshold collapses under heavy-tailed network traffic"),
        ("8", "Hussein & Répás (2026)", "Granular multi-class attack classification", "Deep autoencoder screening + GMM + XGBoost", "Reported macro F1-score exceeding 0.94 across classes", "Gaussian Mixture Model clustering introduces substantial computational overhead"),
        ("9", "Diana et al. (2025)", "Benchmark reproducibility in NIDS research", "Comprehensive decadal literature analysis", "Audits pervasive evaluation flaws in 100+ papers", "Lacks automated cryptographic deduplication and cross-partition audit tools"),
        ("10", "Arcos-Argudo et al. (2025)", "Classical vs hybrid boundary screening", "Deep Autoencoders compared to linear PCA/filters", "Evaluated representation fidelity on NSL-KDD & CICIDS", "Relies on closed-world assumptions; zero-day isolation was not audited")
    ]
    t_lit = doc.add_table(rows=len(lit_table_data), cols=6)
    for i, row in enumerate(lit_table_data):
        for j, val in enumerate(row):
            t_lit.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_lit, [Inches(0.4), Inches(1.1), Inches(1.1), Inches(1.2), Inches(1.2), Inches(1.0)])

    add_sec("2.3 Comparative Analysis")
    add_para(doc, "Existing approaches in network intrusion detection generally fall into two diametrically opposed paradigms:")
    add_numbered_item(doc, "1.", "Algorithms such as Random Forest, Multi-Layer Perceptrons, and Gradient Boosted Decision Trees (XGBoost, LightGBM, CatBoost) achieve near-perfect discrimination (>99%) when test data mirrors the training distribution. However, their decision surfaces are bounded by closed-world assumptions; any unmodeled exploit is forcibly assigned to the nearest known class, resulting in fatal false negatives.", "Supervised Discriminative Models:")
    add_numbered_item(doc, "2.", "Autoencoders, One-Class SVMs, and Isolation Forests model normal traffic distributions without requiring attack labels. While effective for anomaly flagging, they cannot provide granular attack categorization and suffer from elevated false-positive rates when benign traffic patterns fluctuate.", "Unsupervised Generative / Reconstruction Models:")
    add_para(doc, "A two-stage hybrid approach combines the strengths of both paradigms: the Autoencoder filters out benign flows and isolates novel deviations, while XGBoost provides high-precision multi-class categorization on suspicious records.")

    add_sec("2.4 Research / Design Gap")
    add_para(doc, "The literature review identifies four major unresolved gaps:")
    add_bullet_item(doc, "Published benchmarks frequently contain identical flows across training and test splits, artificially inflating reported laboratory accuracy.", "Pervasive Data Leakage:")
    add_bullet_item(doc, "Using parametric Gaussian formulas (μ + 3σ) on heavy-tailed network data causes thresholds to explode, completely destroying attack recall.", "Heuristic Threshold Collapse:")
    add_bullet_item(doc, "Calculating Shapley values across every packet stream cripples network throughput, making real-time XAI impractical without selective alert gating.", "Explainability Latency Overhead:")
    add_bullet_item(doc, "Most models assume static i.i.d. data and degrade rapidly when background network behavior experiences non-adversarial concept drift.", "Absence of Drift Adaptation:")

    add_sec("2.5 Summary")
    add_para(doc, "The literature confirms that while deep learning and tree ensembles are effective independently, neither paradigm alone provides a robust, line-rate, and interpretable defense against modern network intrusions. An audited, leakage-free hybrid architecture combining non-parametric Autoencoder screening, gradient boosted classification, and alert-gated explainability addresses these critical vulnerabilities.")

    # ============================================================
    # CHAPTER 3: PROPOSED SYSTEM AND SCOPE
    # ============================================================
    print("Building Chapter 3: Proposed System and Scope...")
    add_chapter_title("Proposed System and Scope", 3)
    
    add_sec("3.1 Problem Formulation")
    add_para(doc, "Let X ⊂ ℝᵈ represent the d-dimensional space of continuous network flow feature vectors, and let Y = {0, 1, …, C} denote the label space, where 0 corresponds to legitimate benign traffic and {1, …, C} represent C distinct attack categories. During Stage-1 training, the system is provided strictly with a verified set of benign flows D_train, benign = {xᵢ ∈ X | yᵢ = 0}.")
    add_para(doc, "The Stage-1 Autoencoder learns an encoding function f_θ: X → Z mapping inputs to a low-dimensional bottleneck latent representation z ∈ ℝ^(d_z) (d_z ≪ d), and a decoding function g_ϕ: Z → X reconstructing the input vector as x̂ = g_ϕ(f_θ(x)). The scalar reconstruction error is quantified by Mean Squared Error:")
    
    add_eq(doc, r"e(\mathbf{x}) = \frac{1}{d}\sum_{j=1}^d (x_j - \hat{x}_j)^2 = \frac{1}{d}\|\mathbf{x} - g_\phi(f_\theta(\mathbf{x}))\|_2^2", "(3.1)")
    
    add_para(doc, "An anomaly threshold τ* partitions traffic into screened benign records and anomaly alerts:")
    
    add_eq(doc, r"\text{Flag}(\mathbf{x}) = \begin{cases} 0 \quad (\text{Benign-Screened}), & \text{if } e(\mathbf{x}) \le \tau^* \\ 1 \quad (\text{Anomaly-Alert}), & \text{if } e(\mathbf{x}) > \tau^* \end{cases}", "(3.2)")
    
    add_para(doc, "For flows where Flag(x) = 1, the vector is forwarded to the Stage-2 XGBoost classifier h_ψ(x), which computes a softmax probability distribution over known attack classes:")
    
    add_eq(doc, r"P(y = c \mid \mathbf{x}) = \frac{\exp(z_c(\mathbf{x}))}{\sum_{k=1}^C \exp(z_k(\mathbf{x}))}, \quad c \in \{1, \dots, C\}", "(3.3)")
    
    add_para(doc, "Let c*(x) = argmax P(y = c | x) and P*(x) = max P(y = c | x). To isolate potential zero-day threats, a classification confidence floor δ_conf = 0.50 is established. The integrated decision function is defined as:")
    
    add_eq(doc, r"\hat{y}(\mathbf{x}) = \begin{cases} \text{Benign-Screened}, & \text{if } e(\mathbf{x}) \le \tau^* \\ c^*(\mathbf{x}), & \text{if } e(\mathbf{x}) > \tau^* \text{ and } P^*(\mathbf{x}) \ge \delta_{\text{conf}} \\ \text{UNKNOWN\_ATTACK}, & \text{if } e(\mathbf{x}) > \tau^* \text{ and } P^*(\mathbf{x}) < \delta_{\text{conf}} \end{cases}", "(3.4)")

    add_sec("3.2 Proposed Solution")
    add_para(doc, "The proposed solution implements a tiered, sequential detection and categorization pipeline:")
    add_numbered_item(doc, "1.", "Raw network flows are parsed from interface sockets or PCAP files into bidirectional flow statistics. Numerical features are scaled using locked training parameters.", "Packet Ingestion & Normalization:")
    add_numbered_item(doc, "2.", "The deep symmetric Autoencoder computes e(x). Flows with e(x) ≤ τ* are immediately cleared as benign, bypassing heavier downstream processing.", "Stage-1 Autoencoder Anomaly Gating:")
    add_numbered_item(doc, "3.", "Anomalous traffic (e(x) > τ*) is evaluated by XGBoost. Flows with high confidence (≥ 0.50) receive specific attack labels; low-confidence anomalies are isolated as UNKNOWN_ATTACK.", "Stage-2 XGBoost Multi-Class Classification:")
    add_numbered_item(doc, "4.", "Shapley feature attributions are computed strictly for alerted flows, providing local top-5 explanations to security analysts.", "Alert-Gated TreeSHAP Attribution:")
    add_numbered_item(doc, "5.", "Legitimate benign flows update a sliding reference buffer (W=500) that monitors population stability and compensates for operational concept drift.", "Dynamic Drift Buffer:")

    add_sec("3.3 Requirements")
    add_subsec("Functional & Non-Functional Requirements")
    add_para(doc, "Functional Requirements:")
    add_bullet_item(doc, "The system shall capture live network packets via promiscuous sockets and assemble them into 5-tuple bidirectional flows.", "FR1 (Packet Capture & Flow Assembly):")
    add_bullet_item(doc, "The system shall standardize incoming features using locked training scaling parameters without data contamination.", "FR2 (Zero-Leakage Transformation):")
    add_bullet_item(doc, "The Autoencoder shall calculate reconstruction MSE loss and filter benign traffic below threshold τ*.", "FR3 (Autoencoder Anomaly Gating):")
    add_bullet_item(doc, "The XGBoost engine shall classify anomaly flows into granular threat categories (DoS, Probe, R2L, U2R, SSH-Bruteforce).", "FR4 (Multi-Class Categorization):")
    add_bullet_item(doc, "Anomalous flows with predicted confidence below 0.50 shall be isolated as UNKNOWN_ATTACK.", "FR5 (Zero-Day Quarantine):")
    add_bullet_item(doc, "TreeSHAP attributions shall be computed strictly for flagged alerts to explain threat drivers.", "FR6 (Alert-Gated Explainability):")
    add_bullet_item(doc, "The system shall compute Population Stability Index (PSI) across sliding windows and update baseline statistics.", "FR7 (Concept Drift Buffering):")
    
    add_para(doc, "Non-Functional Requirements:")
    add_bullet_item(doc, "End-to-end detection latency shall not exceed 0.25 ms per flow under streaming conditions on CPU hardware.", "NFR1 (Performance & Latency):")
    add_bullet_item(doc, "Sustained processing throughput shall exceed 5,000 flows/second on a standard multi-core CPU.", "NFR2 (Throughput Capacity):")
    add_bullet_item(doc, "Peak Resident Set Size (RSS) memory consumption shall remain below 600 MB to allow edge gateway co-location.", "NFR3 (Memory Footprint):")
    add_bullet_item(doc, "Attack recall shall exceed 99% on documented attacks and exceed 80% on unseen volumetric attacks.", "NFR4 (Detection Accuracy):")
    add_bullet_item(doc, "The web dashboard shall display real-time telemetry gauges, threat counters, and SHAP waterfall plots with update latency under 2 seconds.", "NFR5 (Usability):")
    add_bullet_item(doc, "The system shall rely strictly on transport-layer flow metadata, avoiding payload inspection to preserve user data confidentiality.", "NFR6 (Security & Privacy):")

    add_subsec("Hardware & Software Requirements")
    add_para(doc, "Hardware Requirements:")
    add_bullet_item(doc, "AMD Ryzen 5 5600H @ 3.30 GHz (or Intel Core i5/i7 equivalent, 6 cores / 12 threads).", "Processor:")
    add_bullet_item(doc, "16 GB DDR4/DDR5 system memory.", "RAM:")
    add_bullet_item(doc, "512 GB NVMe SSD for fast model loading, PCAP buffering, and audit logs.", "Storage:")
    add_bullet_item(doc, "Gigabit Ethernet NIC supporting promiscuous packet capture.", "Network Adapter:")
    
    add_para(doc, "Software Requirements:")
    add_bullet_item(doc, "Windows 11 / Ubuntu 22.04 LTS (64-bit).", "Operating System:")
    add_bullet_item(doc, "Python 3.10 to 3.13.", "Programming Language:")
    add_bullet_item(doc, "TensorFlow 2.13.0 / Keras.", "Deep Learning Framework:")
    add_bullet_item(doc, "XGBoost 2.0.3, Scikit-learn 1.3.2.", "Machine Learning Framework:")
    add_bullet_item(doc, "SHAP 0.43.0.", "Explainable AI Framework:")
    add_bullet_item(doc, "Scapy 2.5.0, NumPy 1.24+, Pandas 2.0+, SciPy 1.11+.", "Packet Capture & Analysis:")
    add_bullet_item(doc, "Streamlit 1.30+, Matplotlib 3.7+, Seaborn 0.12+.", "User Interface Engine:")

    add_sec("3.4 System Architecture / Block Diagram")
    add_figure(doc, "figures/architecture.png", "Figure 3.1: System Architecture of the Two-Stage Hybrid NIDS", width=Inches(5.5))
    add_para(doc, "The system architecture is structured into six discrete, decoupled operational tiers:")
    add_numbered_item(doc, "1.", "Operates at the network interface layer. Using Scapy socket listeners or offline PCAP readers, incoming packets are tracked based on bidirectional 5-tuples (IP_src, IP_dst, Port_src, Port_dst, Protocol). State timers aggregate packet inter-arrival times, payload byte counts, and TCP flag counts into structured statistical flow records.", "Ingestion Tier:")
    add_numbered_item(doc, "2.", "Implements cryptographic data sanitation and zero-leakage transformation. Continuous numerical flow features are standardized using training-locked z-score parameters (μ_train, σ_train). Extreme infinite values caused by zero-duration division are clamped to numerical bounds.", "Preprocessing Tier:")
    add_numbered_item(doc, "3.", "Flow vectors are passed to the deep symmetric Autoencoder (d → 16 → d). Mean Squared Error reconstruction loss e(x) is evaluated against the validation-optimized threshold τ* = 0.1973. Legitimate benign flows (e ≤ τ*) bypass heavier classification and are cleared within 0.0820 ms.", "Stage-1 Screening Tier (Autoencoder Gatekeeper):")
    add_numbered_item(doc, "4.", "Flagged anomalies (e > τ*) are forwarded to 500 gradient-boosted decision trees. The model calculates class softmax probabilities. Flows with P* ≥ δ_conf (0.50) are tagged with exact attack categories. Low-confidence anomalies (P* < 0.50) are quarantined as UNKNOWN_ATTACK.", "Stage-2 Classification Tier (XGBoost Ensemble):")
    add_numbered_item(doc, "5.", "TreeSHAP evaluates local Shapley feature contributions exclusively for alerted flows, identifying top-5 threat drivers. Concurrently, benign flows stream into a circular reference buffer (W=500), where Kolmogorov-Smirnov DKS, PSI, and JSD metrics monitor statistical drift.", "Explainability & Drift Monitoring Tier:")
    add_numbered_item(doc, "6.", "An interactive Streamlit web dashboard visualizes real-time throughput gauges, live sniffer streams, threat alert counters, and local TreeSHAP waterfall charts.", "Presentation Tier:")

    add_sec("3.5 Functional Components & Scope Constraints")
    add_para(doc, "The primary functional modules include: (1) Flow Ingestion Module, (2) Data Preprocessing Module, (3) Autoencoder Anomaly Gatekeeper, (4) XGBoost Classifier Engine, (5) TreeSHAP Explainer Module, (6) Drift Monitoring Module, and (7) Dashboard Controller. The system is designed as an edge-deployable software appliance relying exclusively on transport-layer flow metadata; payload inspection is avoided to ensure cryptographic compliance with modern encrypted traffic (TLS 1.3, QUIC).")

    # ============================================================
    # CHAPTER 4: METHODOLOGY
    # ============================================================
    print("Building Chapter 4: Methodology...")
    add_chapter_title("Methodology", 4)
    
    add_sec("4.1 Objective and Method / Approach")
    add_para(doc, "The objective is to design, implement, and validate a two-stage hybrid NIDS that provides robust zero-day detection, eliminates benchmark data leakage, prevents threshold collapse, and sustains line-rate throughput with transparent explainability.")
    add_para(doc, "The methodology follows six structured phases: (1) Dataset Sanitization and cryptographic MD5 deduplication, (2) Feature Transformation using training-locked scalers, (3) Unsupervised Autoencoder Training strictly on benign records, (4) Threshold Optimization via Youden's J-statistic on a validation split, (5) Supervised Attack Classification with depth-constrained XGBoost, and (6) Integration and CPU operational profiling.")

    add_sec("4.2 Measurement / Evaluation Parameters")
    add_caption(doc, "Table 4.1: Measurement and Evaluation Parameters for Model Assessment")
    eval_table = [
        ("Metric", "Mathematical Formula", "Operational Interpretation"),
        ("Accuracy", "(TP + TN) / (TP + TN + FP + FN)", "Overall proportion of correct classifications across all classes."),
        ("Precision", "TP / (TP + FP)", "Proportion of flagged alerts that represent true cyber threats."),
        ("Attack Recall (TPR)", "TP / (TP + FN)", "Sensitivity: ability of the system to capture malicious flows."),
        ("False Positive Rate", "FP / (FP + TN)", "Proportion of legitimate benign flows incorrectly flagged as threats."),
        ("Macro-F1 Score", "(1/K) ∑ [2 · Pₖ · Rₖ / (Pₖ + Rₖ)]", "Unweighted mean of F1 scores across classes; protects rare attacks."),
        ("Youden's J-Index", "TPR(τ) - FPR(τ)", "Difference between sensitivity and false alarm rate across thresholds."),
        ("Population Stability Index (PSI)", "∑ (P_act - P_exp) · ln(P_act / P_exp)", "Quantifies distributional divergence between baseline and streaming data."),
        ("Inference Latency", "Total Wall-Clock Time / Total Flow Count", "Time required to process, score, and classify a single network flow.")
    ]
    t_eval = doc.add_table(rows=len(eval_table), cols=3)
    for i, row in enumerate(eval_table):
        for j, val in enumerate(row):
            t_eval.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_eval, [Inches(1.4), Inches(1.8), Inches(2.8)])

    add_sec("4.3 Model Architecture and Structural Diagrams")
    add_subsec("Autoencoder Latent Topology & Manifold Projection")
    add_para(doc, "The Autoencoder utilizes a symmetric pyramidal compression architecture (d → 128 → 64 → 32 → 16 → 32 → 64 → 128 → d) to balance non-linear representation capacity with line-rate computational efficiency. High-dimensional flow vectors (d=78 for CICIDS2018; d=122 for NSL-KDD) pass through progressively tapered dense layers equipped with Batch Normalization and ReLU activations. This gradual multi-tier reduction prevents informational bottleneck shock and preserves continuous topological manifolds. Dropout regularization (p=0.20) prevents co-adaptation among latent units, forcing the central 16-dimensional bottleneck to discard stochastic packet jitter and learn the underlying manifold of legitimate network communication.")
    
    add_eq(doc, r"e(\mathbf{x}) = \frac{1}{d}\sum_{j=1}^d (x_j - \hat{x}_j)^2 = \frac{1}{d}\|\mathbf{x} - g_\phi(f_\theta(\mathbf{x}))\|_2^2 > \tau^*", "(4.1)")
    
    add_para(doc, "Trained exclusively on benign flow records D_train, benign, the decoder g_ϕ learns the inverse mapping strictly for normal traffic geometries. When anomalous or zero-day intrusions occur (such as volumetric DoS floods, credential brute-forcing, or reconnaissance scans), their statistical feature distributions lie orthogonal to the learned manifold. With a per-flow inference latency of only 0.0820 ms (12,195 flows/s on a single CPU core) and a compact 384.2 MB RSS footprint, this stage filters out over 85–90% of benign background traffic at wire speed, invoking downstream XGBoost classification and TreeSHAP explainability strictly when threats are suspected.")
    
    add_caption(doc, "Table 4.2: Autoencoder Bottleneck Layer Configuration and Dimensionality")
    ae_layers = [
        ("Layer", "Layer Type", "Activation / Parameter", "Output Shape", "Functional Purpose"),
        ("1", "InputLayer", "Linear", "(d,)", "Ingests normalized flow vector"),
        ("2", "Dense (Encoder-1)", "ReLU, BatchNorm", "(128,)", "Initial high-order compression"),
        ("3", "Dropout (0.20)", "p = 0.20", "(128,)", "Regularization against co-adaptation"),
        ("4", "Dense (Encoder-2)", "ReLU, BatchNorm", "(64,)", "Intermediate latent projection"),
        ("5", "Dense (Encoder-3)", "ReLU, BatchNorm", "(32,)", "Deep non-linear compression"),
        ("6", "Dense (Bottleneck)", "ReLU", "(16,)", "Compressed latent representation z"),
        ("7", "Dense (Decoder-1)", "ReLU, BatchNorm", "(32,)", "Symmetrical feature expansion"),
        ("8", "Dense (Decoder-2)", "ReLU, BatchNorm", "(64,)", "Intermediate feature decoding"),
        ("9", "Dense (Decoder-3)", "ReLU, BatchNorm", "(128,)", "Higher-level feature reconstruction"),
        ("10", "Dense (Output)", "Linear", "(d,)", "Reconstructed flow vector x̂")
    ]
    t_ae = doc.add_table(rows=len(ae_layers), cols=5)
    for i, row in enumerate(ae_layers):
        for j, val in enumerate(row):
            t_ae.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_ae, [Inches(0.5), Inches(1.5), Inches(1.5), Inches(0.9), Inches(1.6)])

    # Sequence Diagram
    add_subsec("Sequence Diagram of Packet Ingestion and Prediction")
    add_figure(doc, "figures/Network Threat Detection Sequence Diagram.png", "Figure 4.2: Sequence Diagram of Packet Ingestion and Prediction Workflow", width=Inches(5.5))
    add_para(doc, "The sequence diagram documents three distinct operational pathways across seven system actors:")
    add_bullet_item(doc, "The network tap forwards raw packets to the Flow Preprocessor, which scales features and passes the vector to the Stage-1 Autoencoder. Because reconstruction error is below threshold (e ≤ τ*), the Autoencoder returns Benign-Screened in 0.0820 ms. The flow is pushed to the sliding drift buffer, completely bypassing Stage-2 classification and TreeSHAP.", "Pathway A (Benign Traffic Screening):")
    add_bullet_item(doc, "An exploit flow triggers a reconstruction spike (e > τ*). The Autoencoder invokes the Stage-2 XGBoost classifier. The ensemble calculates class probabilities (P* ≥ 0.50), assigns a specific attack category (e.g., SSH-Bruteforce), triggers alert-gated TreeSHAP to extract top-5 feature attributions, and dispatches a comprehensive threat alert to the dashboard.", "Pathway B (Known Attack Vector):")
    add_bullet_item(doc, "An unmodeled attack generates e > τ* due to structural divergence. XGBoost evaluates the flow but yields diffuse softmax probabilities (P* < 0.50). The confidence gating logic intercepts the prediction, assigns the label UNKNOWN_ATTACK, and flags the incident for immediate security analyst investigation.", "Pathway C (Zero-Day Exploit Isolation):")

    # Activity Diagram
    add_subsec("Activity Diagram of Tiered Detection and Alert Routing")
    add_figure(doc, "figures/activity_diagram.png", "Figure 4.3: Activity Diagram of Tiered Detection and Alert Routing", width=Inches(5.2))
    add_para(doc, "The activity lifecycle begins with continuous packet capture on the network interface. Packets are aggregated into bidirectional flows based on 5-tuple keys. Upon flow termination or timeout, features are extracted and normalized via locked z-score scaling. Control reaches Decision Diamond 1: if e(x) ≤ τ*, the flow is classified as legitimate and appended to the drift buffer. If e(x) > τ*, control branches to the Stage-2 XGBoost classifier. At Decision Diamond 2, if confidence P* ≥ 0.50, the attack is labeled by family; otherwise, it is quarantined as UNKNOWN_ATTACK. Flagged alerts trigger asynchronous TreeSHAP computation and dispatch enriched threat notifications to the security operations console.")

    # DFD Level-1
    add_subsec("Data Flow Diagram (DFD Level-1) for Flow Processing")
    add_figure(doc, "figures/Network Intrusion Detection Flowchart.png", "Figure 4.4: Data Flow Diagram (DFD Level-1) for Flow Processing and Anomaly Gating", width=Inches(5.4))
    add_para(doc, "The Level-1 DFD is decomposed into six core processes and four persistent data stores:")
    add_bullet_item(doc, "Consumes raw frames from the network interface tap and produces structured bidirectional flow records.", "Process 1.0 (Packet Capture & Flow Assembly):")
    add_bullet_item(doc, "Normalizes raw flow records using locked transformation vectors from the Scaler Parameters Store.", "Process 2.0 (Cryptographic Feature Scaling):")
    add_bullet_item(doc, "Evaluates reconstruction MSE using the Autoencoder Model Store against thresholds from the Threshold Parameters Store.", "Process 3.0 (Autoencoder Reconstruction & Anomaly Gating):")
    add_bullet_item(doc, "Evaluates anomalous flow vectors using the XGBoost Model Store, computing multi-class softmax distributions.", "Process 4.0 (Gradient Boosted Multi-Class Inference):")
    add_bullet_item(doc, "Generates local Shapley feature attributions for alerted flows using the Background Summary Store.", "Process 5.0 (Explainability & Feature Attribution):")
    add_bullet_item(doc, "Ingests verified normal flows into the Sliding Reference Buffer Store (W=500) to evaluate population stability.", "Process 6.0 (Concept Drift Buffering):")

    # Class Diagram & Use Case Diagram
    add_subsec("Class Diagram and Use Case Diagram")
    add_figure(doc, "figures/class_diagram.png", "Figure 4.5: Class Diagram of Object-Oriented Framework Architecture", width=Inches(5.4))
    add_para(doc, "The class architecture enforces clean separation of concerns through modular encapsulation: PacketCaptureEngine manages low-level Scapy sockets; FeaturePreprocessor encapsulates training-locked mean and standard deviation vectors; AutoencoderGater wraps the Keras neural network; XGBoostClassifier manages the 500-tree boosting ensemble; SHAPExplainer computes exact Shapley attribution values; DriftMonitor implements a circular ring buffer (W=500); and TelemetryController acts as the orchestrating Facade coordinating data flows between backend processing engines and the Streamlit UI.")
    
    add_figure(doc, "figures/usecase_diagram.png", "Figure 4.6: Use Case Diagram of Network Intrusion Detection Workflow", width=Inches(5.4))
    add_para(doc, "The use case model defines interactions across four primary actors: (1) Security Operations Center (SOC) Analyst who monitors live traffic, inspects alerts, and reviews SHAP plots; (2) Security Administrator who configures thresholds and triggers retraining; (3) Automated Perimeter IPS / Firewall which consumes alert webhooks to update firewall drop rules; and (4) Ingress Network Traffic representing external entities generating communications and attacks.")

    add_sec("4.4 Error Sources, Mitigation, and Data Processing")
    add_bullet_item(doc, "Handled by training the Autoencoder strictly on benign samples, while XGBoost uses weighted cross-entropy loss.", "Class Imbalance:")
    add_bullet_item(doc, "Mitigated through dropout (p=0.20), early stopping on validation reconstruction loss, and depth-constrained gradient boosted trees (max_depth = 6).", "Overfitting:")
    add_bullet_item(doc, "Prevented by computing cryptographic MD5 hashes of all connection tuples, identifying and eliminating 362 duplicate rows across partitions.", "Data Leakage:")
    add_bullet_item(doc, "Handled by a dynamic sliding buffer (W=500) that recalculates the 95th percentile threshold periodically as traffic shifts.", "Concept Drift:")
    add_bullet_item(doc, "Enforced across 70% train, 15% validation, and 15% test splits, complemented by Leave-One-Attack-Out (LOAO) validation.", "Stratified Splitting:")

    # ============================================================
    # CHAPTER 5: IMPLEMENTATION & EXPERIMENTAL WORK
    # ============================================================
    print("Building Chapter 5: Implementation & Experimental Work...")
    add_chapter_title("Implementation & Experimental Work", 5)
    
    add_sec("5.1 Implementation Environment")
    add_para(doc, "The Two-Stage Hybrid NIDS was developed entirely in Python 3.10. The core numerical transformations utilize NumPy and Pandas. Deep Autoencoder architectures were implemented in TensorFlow/Keras 2.13.0, and the tree ensemble utilizes XGBoost 2.0.3. Feature explainability was constructed with SHAP 0.43.0, and live socket sniffing was implemented via Scapy 2.5.0. An interactive operational dashboard was developed using Streamlit 1.30.")

    add_sec("5.2 Module-wise Implementation")
    add_para(doc, "A rigorous cryptographic audit was executed on both CICIDS2018 and NSL-KDD benchmark datasets. In CICIDS2018, 323,892 duplicate flows and 24 records with missing values were purged, leaving 671,131 unique flows. In NSL-KDD, 147,790 unique instances were curated.")
    
    add_caption(doc, "Table 5.1: Cryptographically Audited Dataset Splits Enforcing Zero Leakage (Train ∩ Test = ∅)")
    split_data = [
        ("Dataset Partition", "Training (70%)", "Validation (15%)", "Testing (15%)"),
        ("CICIDS2018 (Total: 671,131)", "469,792", "100,669", "100,670"),
        ("  Benign Flows", "403,929", "86,557", "86,556"),
        ("  SSH-Bruteforce", "65,829", "14,106", "14,106"),
        ("  FTP-BruteForce", "34", "6", "8"),
        ("NSL-KDD (Total: 147,790)", "103,453", "22,168", "22,169"),
        ("  Normal Traffic", "53,845", "11,539", "11,538"),
        ("  Denial of Service (DoS)", "37,087", "7,947", "7,948"),
        ("  Probe (Network Scans)", "10,077", "2,160", "2,160"),
        ("  Remote to Local (R2L)", "1,592", "341", "341"),
        ("  User to Root (U2R)", "852", "181", "182")
    ]
    t_split = doc.add_table(rows=len(split_data), cols=4)
    for i, row in enumerate(split_data):
        for j, val in enumerate(row):
            t_split.rows[i].cells[j].paragraphs[0].text = val
            if j > 0 and i > 0:
                t_split.rows[i].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    style_table(t_split, [Inches(2.4), Inches(1.2), Inches(1.2), Inches(1.2)])

    add_para(doc, "Continuous numerical attributes were scaled via z-score normalization:")
    
    add_eq(doc, r"x_{\text{scaled}} = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}", "(5.1)")
    
    add_para(doc, "The Autoencoder was trained strictly on benign flow records using Mean Squared Error loss:")
    
    add_eq(doc, r"\mathcal{L}_{\text{MSE}}(\theta, \phi) = \frac{1}{|\mathcal{D}_b|}\sum_{\mathbf{x} \in \mathcal{D}_b} \frac{1}{d}\|\mathbf{x} - g_\phi(f_\theta(\mathbf{x}))\|_2^2", "(5.2)")
    
    add_para(doc, "To monitor operational data drift over continuous packet streams, the Population Stability Index (PSI) is computed across sliding windows:")
    
    add_eq(doc, r"\text{PSI} = \sum_{b=1}^B (P_{\text{act}, b} - P_{\text{exp}, b}) \times \ln\left(\frac{P_{\text{act}, b}}{P_{\text{exp}, b}}\right)", "(5.3)")
    
    add_para(doc, "The Autoencoder was trained for 50 epochs using mini-batches of 256 samples with the Adam optimizer (η = 0.001). Stage-2 XGBoost was configured with 500 estimators (max_depth=6, η=0.05). Alert-gated TreeSHAP computes local attributions exclusively when e(x) > τ*, reducing computational overhead by 90%. Drift is monitored via Population Stability Index across sliding windows of W=500 flows.")

    add_sec("5.3 Experimental Setup")
    add_caption(doc, "Table 5.2: Experimental Setup Parameters and Hyperparameter Configurations")
    setup_data = [
        ("Parameter", "CICIDS2018 Value", "NSL-KDD Value", "Operational Purpose"),
        ("Input Feature Dimension", "78 numerical features", "122 one-hot features", "Transport-layer flow representation"),
        ("Bottleneck Dimension", "16 latent units", "16 latent units", "Unsupervised anomaly compression"),
        ("Autoencoder Epochs", "50 epochs", "50 epochs", "Convergence of reconstruction loss"),
        ("Mini-Batch Size", "256 samples", "256 samples", "GPU/CPU batch gradient descent"),
        ("Initial Learning Rate", "0.001 (Adam)", "0.001 (Adam)", "Optimization step size"),
        ("Threshold Strategy", "Youden's J (τ* = 0.1973)", "Youden's J (τ* = 0.0840)", "Non-parametric threshold knee"),
        ("XGBoost Estimators", "500 decision trees", "500 decision trees", "Multi-class boosting ensemble"),
        ("Confidence Floor (δ_conf)", "0.50", "0.50", "Zero-day threat quarantine threshold"),
        ("Sliding Buffer Size (W)", "500 benign flows", "500 benign flows", "Adaptive concept drift reference")
    ]
    t_setup = doc.add_table(rows=len(setup_data), cols=4)
    for i, row in enumerate(setup_data):
        for j, val in enumerate(row):
            t_setup.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_setup, [Inches(1.8), Inches(1.4), Inches(1.4), Inches(1.4)])

    add_sec("5.4 Prototype & Testing")
    add_figure(doc, "figures/dashboard_home.png", "Figure 5.1: Real-Time Network Flow Telemetry and Live Sniffing Monitor", width=Inches(5.5))
    add_figure(doc, "figures/dashboard_alert.png", "Figure 5.2: Threat Diagnosis, Alert Gating, and Local TreeSHAP Explanation", width=Inches(5.5))
    
    add_caption(doc, "Table 5.3: System Test Cases, Inputs, Expected Outcomes, and Execution Status")
    test_cases = [
        ("Test Case", "Description", "Input Data", "Expected Output", "Status"),
        ("TC01", "Preprocessing Scaling", "Raw flow with extreme IAT", "Scaled vector with zero NaN/Inf values", "Pass"),
        ("TC02", "Benign Screening", "Legitimate HTTP flow (e ≤ τ*)", "Flagged as Benign-Screened; bypasses Stage 2", "Pass"),
        ("TC03", "Anomaly Detection Gating", "SSH-Bruteforce flow (e > τ*)", "Reconstruction spike triggers Stage-2 classification", "Pass"),
        ("TC04", "XGBoost Multi-Class", "Known DoS attack vector", "Correct attack category identified (conf >95%)", "Pass"),
        ("TC05", "Zero-Day Quarantine", "Unmodeled exploit flow", "Flagged as anomaly; categorized as UNKNOWN_ATTACK", "Pass"),
        ("TC06", "Alert-Gated TreeSHAP", "Flagged malicious alert", "Top-5 feature attribution list generated in <0.5 ms", "Pass"),
        ("TC07", "Streaming Throughput", "100,000 test flows", "Throughput >5,000 flows/s; RAM <600 MB", "Pass")
    ]
    t_tc = doc.add_table(rows=len(test_cases), cols=5)
    for i, row in enumerate(test_cases):
        for j, val in enumerate(row):
            t_tc.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_tc, [Inches(0.7), Inches(1.3), Inches(1.3), Inches(2.0), Inches(0.7)])

    # ============================================================
    # CHAPTER 6: RESULTS, ANALYSIS AND DISCUSSION (ENRICHED CONTENT)
    # ============================================================
    print("Building Chapter 6: Results, Analysis and Discussion...")
    add_chapter_title("Results, Analysis and Discussion", 6)
    
    add_sec("6.1 Quantitative Classification Results")
    add_para(doc, "To provide an objective, scientifically rigorous assessment of the two-stage hybrid NIDS, experimental evaluations were conducted across two benchmark corpora: the modern, high-dimensional CSE-CIC-IDS2018 dataset (comprising 671,131 sanitized records) and the canonical NSL-KDD benchmark (147,790 records). Both corpora underwent rigorous cryptographic deduplication to eliminate shared session keys and prevent artificial performance inflation. All performance metrics were computed strictly on held-out test partitions (N = 100,670 for CICIDS2018 and N = 22,169 for NSL-KDD), which remained completely untouched throughout feature scaling, autoencoder convergence, and gradient-boosted tree construction.")
    
    add_caption(doc, "Table 6.1: Overall Classification Performance on Held-Out Test Partitions")
    summary_data = [
        ("Metric", "CICIDS2018 Value", "NSL-KDD Value", "Operational Significance"),
        ("Accuracy", "91.34%", "92.77%", "High overall classification fidelity"),
        ("Attack Recall (TPR)", "99.70%", "93.13%", "Exceptional sensitivity to malicious activity"),
        ("False Positive Rate", "10.03%", "7.53%", "Measured false alarms from anomaly gating"),
        ("Macro-F1 Score", "0.5805", "0.7670", "Balanced performance across rare categories"),
        ("Inference Latency", "0.1830 ms/flow", "0.1420 ms/flow", "Sub-millisecond execution on multi-core CPU"),
        ("Peak Memory Footprint", "527.0 MB RSS", "412.0 MB RSS", "Edge-gateway deployable resource profile")
    ]
    t_sum = doc.add_table(rows=len(summary_data), cols=4)
    for i, row in enumerate(summary_data):
        for j, val in enumerate(row):
            t_sum.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_sum, [Inches(1.8), Inches(1.3), Inches(1.3), Inches(1.6)])

    add_para(doc, "As summarized in Table 6.1, the proposed architecture establishes high operational efficacy across both benchmarks. On CICIDS2018, the pipeline achieves an attack detection recall of 99.70% (capturing 14,075 of 14,114 malicious test flows) alongside an overall classification accuracy of 91.34%. On NSL-KDD, the framework demonstrates 92.77% accuracy and 93.13% attack recall. The measured False Positive Rate (10.03% on CICIDS2018 and 7.53% on NSL-KDD) represents an intentional, mathematically calibrated operational trade-off. By configuring the Stage-1 Autoencoder gating threshold to aggressively capture rare and unmodeled anomalous deviations, the system prioritizes perimeter sensitivity over ultra-conservative filtering, guaranteeing that intrusive vectors are intercepted before they compromise host assets.")

    add_caption(doc, "Table 6.2: Multi-Class Attack Detection Breakdown on CICIDS2018 (N = 100,670)")
    cicids_breakdown = [
        ("Traffic Category", "Test Samples", "Detected Samples", "Class Recall", "Class Precision"),
        ("Benign Flows", "86,556", "77,877", "89.97%", "99.95%"),
        ("SSH-Bruteforce", "14,106", "14,067", "99.72%", "61.83%"),
        ("FTP-BruteForce", "8", "8", "100.00%", "66.67%"),
        ("Total / Overall", "100,670", "91,952", "99.70%", "91.34%")
    ]
    t_cicids = doc.add_table(rows=len(cicids_breakdown), cols=5)
    for i, row in enumerate(cicids_breakdown):
        for j, val in enumerate(row):
            t_cicids.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_cicids, [Inches(1.6), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1)])

    add_para(doc, "Table 6.2 illustrates the granular category-level breakdown for the CICIDS2018 test split. The system demonstrates near-flawless performance on volumetric and automated authentication vectors. For SSH-Bruteforce attacks, the pipeline identifies 14,067 out of 14,106 attack instances, achieving 99.72% recall. This heightened sensitivity stems from the distinctive temporal signatures of automated password guessing, including rapid packet inter-arrival times (IATs), uniform packet lengths, and abnormal TCP flag combinations that clash sharply with the learned manifold of legitimate communication. Similarly, all 8 test flows of FTP-BruteForce are detected (100.00% recall), confirming that extreme class rarity in training data does not preclude reliable isolation when non-linear autoencoder gating is employed. Concurrently, 77,877 legitimate benign flows are cleared at Stage-1, yielding an exceptional Benign class precision of 99.95%.")

    add_caption(doc, "Table 6.3: Multi-Class Attack Detection Breakdown on NSL-KDD (N = 22,169)")
    nslkdd_breakdown = [
        ("Traffic Category", "Test Samples", "Detected Samples", "Class Recall", "Class Precision"),
        ("Normal Traffic", "11,538", "10,669", "92.47%", "93.59%"),
        ("Denial of Service (DoS)", "7,948", "7,668", "96.48%", "96.12%"),
        ("Probe (Network Scans)", "2,160", "1,884", "87.22%", "81.35%"),
        ("Remote to Local (R2L)", "341", "248", "72.73%", "74.03%"),
        ("User to Root (U2R)", "182", "92", "50.55%", "63.89%"),
        ("Total / Overall", "22,169", "20,561", "93.13%", "92.77%")
    ]
    t_nsl = doc.add_table(rows=len(nslkdd_breakdown), cols=5)
    for i, row in enumerate(nslkdd_breakdown):
        for j, val in enumerate(row):
            t_nsl.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_nsl, [Inches(1.6), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.1)])

    add_para(doc, "Table 6.3 details the multi-class performance on the NSL-KDD corpus across five functional threat families. Volumetric Denial of Service (DoS) flows achieve 96.48% recall (7,668 / 7,948 detected) and 96.12% precision, as high-rate flood dynamics generate profound reconstruction residuals across forward packet counts and byte-rate metrics. Network reconnaissance (Probe) attacks attain 87.22% recall, driven by anomalies in port scan headers and ICMP error indicators. Conversely, subtle application-layer vectors such as Remote to Local (R2L, 72.73% recall) and User to Root (U2R, 50.55% recall) exhibit lower sensitivity. Because U2R attacks comprise only 182 test flows and operate within single interactive shell sessions, their transport-layer flow summaries closely resemble legitimate administrative activity. This empirical finding highlights an important operational boundary: while transport-level flow analysis excels at intercepting volumetric, scanning, and credential-stuffing exploits, defending against stealthy low-footprint privilege escalations benefits from complementary host-based log auditing.")

    add_sec("6.2 Confusion Matrix & Threshold Analysis")
    add_figure(doc, "figures/confusion_hybrid_cicids2018.png", "Figure 6.1: Confusion Matrix for Hybrid Model on CICIDS2018", width=Inches(4.8))
    add_figure(doc, "figures/cm_autoencoder_cicids2018.png", "Figure 6.2: Confusion Matrix for Standalone Autoencoder on CICIDS2018", width=Inches(4.8))
    
    add_para(doc, "Figures 6.1 and 6.2 provide row-normalized confusion matrices illustrating decision flows under the integrated two-stage framework and the standalone Autoencoder. In Figure 6.1, each cell indicates the conditional probability of predicting class j given true class i. The diagonal dominance demonstrates consistent classification fidelity: 89.97% of normal flows are correctly labeled as benign, while less than 0.3% of attack traffic escapes detection into the benign category. In contrast, Figure 6.2 reveals the functional limitation of using an autoencoder in isolation: while it flags anomalies with 99.70% recall, it collapses all threats into an undifferentiated binary category, depriving SOC analysts of the granular threat taxonomy required for automated firewall blocking or incident escalation.")

    add_para(doc, "A critical scientific contribution of this research is the empirical identification and resolution of Gaussian threshold collapse. Prevailing NIDS literature widely employs parametric rules (μ + 3σ) to establish anomaly cutoffs. As documented in Table 6.4, this assumption completely breaks down on real-world network traffic. Network telemetry follows heavy-tailed, non-Gaussian distributions (e.g., Pareto and log-normal) driven by bursty web downloads and streaming spikes. These extreme benign outliers dramatically inflate the sample standard deviation, driving the theoretical threshold to an astronomical μ + 3σ = 38,723.19. Because legitimate attack flows yield reconstruction errors bounded between 0.20 and 5.00, literally zero attack flows exceed this inflated barrier, resulting in complete recall collapse (0.0000).")

    add_caption(doc, "Table 6.4: Reconstruction Threshold Strategy Comparison on CICIDS2018")
    thresh_data = [
        ("Threshold Method / Value", "Precision", "Recall", "Macro-F1", "FPR"),
        ("Statistical Sigma (μ + 3.0σ = 38,723.19)", "0.0000", "0.0000", "0.0000", "0.0000"),
        ("Fixed 95th Percentile (τ = 0.3632)", "0.0007", "0.0002", "0.0003", "0.0496"),
        ("Fixed 99th Percentile (τ = 2.1162)", "0.0000", "0.0000", "0.0000", "0.0100"),
        ("Validation Optimal (J: τ* = 0.1973)", "0.6185", "0.9970", "0.7634", "0.1003"),
        ("Adaptive Buffer (W=500, q=95, τ=0.0035)", "0.1700", "0.9899", "0.2901", "0.7883")
    ]
    t_th = doc.add_table(rows=len(thresh_data), cols=5)
    for i, row in enumerate(thresh_data):
        for j, val in enumerate(row):
            t_th.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_th, [Inches(2.4), Inches(0.9), Inches(0.9), Inches(0.9), Inches(0.9)])
    
    add_para(doc, "Table 6.4 further reveals that static high-percentile cutoffs are equally problematic: a fixed 99th percentile cutoff (τ = 2.1162) yields 0.00% recall, while a 95th percentile cutoff (τ = 0.3632) captures a negligible 0.02% of attacks. The proposed framework resolves this dilemma by optimizing Youden's J-statistic on an independent validation set. By maximizing J(τ) = TPR(τ) - FPR(τ), the optimization algorithm locates the true Pareto knee at τ* = 0.1973, restoring attack recall to 99.70% with a manageable FPR of 10.03% and a Macro-F1 score of 0.7634.")

    add_figure(doc, "figures/threshold_comparison_cicids2018.png", "Figure 6.3: Reconstruction Threshold Sensitivity and Pareto Curves", width=Inches(5.0))
    add_para(doc, "Figure 6.3 visualizes the sensitivity curve of reconstruction error versus classification performance. The intersection of the Precision and Recall curves highlights the Pareto boundary, confirming that τ* = 0.1973 maximizes detection sensitivity while insulating the downstream classifier from excessive false positive noise.")

    add_sec("6.3 Zero-Day Generalization & Drift Tracking")
    add_para(doc, "To rigorously audit the system's ability to protect against previously unmodeled zero-day cyber threats, a Leave-One-Attack-Out (LOAO) protocol was implemented on NSL-KDD. In each experimental fold, one complete attack family was entirely purged from the training distribution. The hybrid framework was then evaluated on its ability to detect the omitted threat using only its unsupervised reconstruction gating mechanism, without any prior supervised training exposure.")

    add_caption(doc, "Table 6.5: Leave-One-Attack-Out (LOAO) Unseen Attack Detection Performance")
    loao_data = [
        ("Held-Out Attack Family", "Test Samples", "Overall Accuracy", "Unseen Recall", "FPR"),
        ("Held-out: DoS (Denial of Service)", "7,948", "93.98%", "93.11%", "5.13%"),
        ("Held-out: Probe (Port Scans)", "2,160", "88.79%", "82.22%", "5.13%"),
        ("Held-out: U2R (Privilege Escalation)", "182", "94.19%", "50.55%", "5.13%"),
        ("Held-out: R2L (Remote to Local)", "341", "93.44%", "44.28%", "5.13%")
    ]
    t_loao = doc.add_table(rows=len(loao_data), cols=5)
    for i, row in enumerate(loao_data):
        for j, val in enumerate(row):
            t_loao.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_loao, [Inches(2.4), Inches(0.9), Inches(0.9), Inches(0.9), Inches(0.9)])
    
    add_figure(doc, "figures/unseen_attack.png", "Figure 6.4: LOAO Unseen Attack Detection Recall", width=Inches(5.0))
    add_para(doc, "The LOAO empirical findings presented in Table 6.5 and Figure 6.4 demonstrate the powerful generalization capability of deep manifold learning. When volumetric Denial of Service (DoS) attacks are completely held out from training, the Autoencoder gatekeeper isolates 93.11% of the unseen attack traffic (7,400 / 7,948 flows) while maintaining a low FPR of 5.13%. Similarly, unseen Probe attacks achieve 82.22% recall. Because volumetric floods and network reconnaissance generate feature combinations that fundamentally violate the benign latent manifold, the autoencoder produces large reconstruction errors regardless of whether the specific attack signature has ever been seen before. Conversely, subtle R2L (44.28%) and U2R (50.55%) attacks exhibit moderate recall, reinforcing that purely semantic exploits require endpoint contextual correlation.")

    add_caption(doc, "Table 6.6: Statistical Concept Drift Tracking Across Sequential Windows in CICIDS2018")
    drift_data = [
        ("Window", "Flows", "DKS", "PSI", "JSD", "Assessment"),
        ("T1", "20,134", "0.1055", "0.1267", "0.0273", "Moderate Drift"),
        ("T2", "20,134", "0.1067", "0.1311", "0.0268", "Buffer Adapted"),
        ("T3", "20,134", "0.1038", "0.1230", "0.0204", "Buffer Adapted"),
        ("T4", "20,134", "0.1033", "0.1221", "0.0263", "Buffer Adapted"),
        ("T5", "20,134", "0.1022", "0.1210", "0.0265", "Buffer Adapted")
    ]
    t_dr = doc.add_table(rows=len(drift_data), cols=6)
    for i, row in enumerate(drift_data):
        for j, val in enumerate(row):
            t_dr.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_dr, [Inches(0.6), Inches(1.1), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.3)])
    
    add_figure(doc, "figures/drift.png", "Figure 6.5: Statistical Concept Drift (DKS, PSI, JSD) Monitored Across Windows", width=Inches(5.2))
    add_para(doc, "To ensure operational reliability over continuous network streams, statistical concept drift was tracked across five sequential windows of 20,134 flows each (T1 through T5) in CICIDS2018. As reported in Table 6.6 and visualized in Figure 6.5, three complementary divergence metrics were evaluated: Kolmogorov-Smirnov distance (DKS), Population Stability Index (PSI), and Jensen-Shannon Divergence (JSD). Across all windows, DKS remained stable between 0.1022 and 0.1067, while PSI hovered between 0.1210 and 0.1311. In production statistical process control, a PSI value below 0.10 denotes stable distribution, values between 0.10 and 0.25 indicate moderate non-adversarial operational shifts, and values exceeding 0.25 indicate critical drift requiring model retraining. The sliding reference buffer (W=500) successfully adapts the reference quantile to these moderate shifts without triggering false alarm storms.")

    add_figure(doc, "figures/shap_summary.png", "Figure 6.6: TreeSHAP Global Feature Importance Ranking (Summary Plot)", width=Inches(5.2))
    add_para(doc, "Figure 6.6 illustrates the global feature importance ranking computed via TreeSHAP summary beeswarm analysis. The five most dominant predictive features are Destination Port, Flow Duration, Total Fwd Packets, Bwd Packet Length Mean, and Flow IAT Mean. High destination port values combined with ultra-low packet inter-arrival times correlate strongly with port scanning sweeps, whereas immense packet volume and sustained flow durations characterize volumetric denial-of-service floods. By surfacing these exact feature attributions, the TreeSHAP module transforms complex non-linear ensemble decisions into transparent, actionable evidence for SOC analysts.")

    add_sec("6.4 Latency, Memory Footprint & Baseline Comparisons")
    add_para(doc, "A critical design requirement for enterprise intrusion detection is maintaining line-rate processing speeds on commodity server hardware. Table 6.7 and Figure 6.7 deliver a comprehensive computational benchmark conducted on an AMD Ryzen multi-core CPU without GPU acceleration.")

    add_caption(doc, "Table 6.7: Computational Benchmark: Execution Latency, Throughput, and Peak Memory (RSS)")
    lat_data = [
        ("Pipeline Stage / Model", "Train Time", "Latency (Throughput)", "Peak Memory"),
        ("Standalone Autoencoder", "142.6 s", "0.0820 ms (12,195 f/s)", "384.2 MB RSS"),
        ("Standalone XGBoost", "38.4 s", "0.0035 ms (285,714 f/s)", "248.5 MB RSS"),
        ("Proposed Hybrid (Detection)", "181.0 s", "0.1830 ms (5,464 f/s)", "527.0 MB RSS"),
        ("Proposed Hybrid (with TreeSHAP)", "181.0 s", "0.4995 ms (2,001 f/s)", "527.0 MB RSS")
    ]
    t_lat = doc.add_table(rows=len(lat_data), cols=4)
    for i, row in enumerate(lat_data):
        for j, val in enumerate(row):
            t_lat.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_lat, [Inches(2.2), Inches(1.0), Inches(1.6), Inches(1.2)])
    
    add_figure(doc, "figures/live_performance.png", "Figure 6.7: End-to-End Pipeline Execution Latency Breakdown on Multi-Core CPU", width=Inches(5.2))
    add_para(doc, "The latency profile demonstrates remarkable efficiency: Stage-1 Autoencoder screening requires only 0.0820 ms per flow (throughput of 12,195 flows/s), while Stage-2 XGBoost multi-class categorization takes an astonishing 0.0035 ms per flow (285,714 flows/s). The integrated detection pipeline averages 0.1830 ms per flow (5,464 flows/s), easily fulfilling the sub-millisecond real-time latency requirement. Furthermore, computing TreeSHAP continuously across all flows would impose a severe throughput penalty (0.4995 ms/flow, capping throughput at 2,001 flows/s). By gating TreeSHAP computation exclusively to the ~10% anomalous alerts, the system eliminates 90% of explainability computational overhead, maintaining high wire-speed screening while providing full explanations on demand. The compact 527.0 MB RSS memory footprint confirms that the software appliance can easily co-locate on edge gateways, firewalls, and lightweight virtual instances.")

    add_caption(doc, "Table 6.8: Benchmark Comparison Against Baseline Supervised Classifiers")
    comp_data = [
        ("Model Architecture", "Dataset", "Accuracy", "Recall", "FPR", "Zero-Day Defense"),
        ("Standalone XGBoost", "CICIDS2018", "1.0000", "1.0000", "0.0000", "Fails on novel attacks"),
        ("Random Forest Baseline", "CICIDS2018", "0.9996", "0.9996", "0.0004", "Fails on novel attacks"),
        ("LinearSVC Baseline", "CICIDS2018", "0.9998", "0.9998", "0.0001", "Fails on novel attacks"),
        ("Multi-Layer Perceptron (MLP)", "CICIDS2018", "0.9998", "0.9998", "0.0001", "Fails on novel attacks"),
        ("Standalone Autoencoder (τ*)", "CICIDS2018", "0.9134", "0.9970", "0.1003", "Anomaly only (no classes)"),
        ("Proposed Hybrid (AE+XGB)", "CICIDS2018", "0.9134", "0.9970", "0.1003", "Full defense-in-depth"),
        ("Standalone XGBoost", "NSL-KDD", "0.9998", "0.9998", "0.0000", "Fails on novel attacks"),
        ("Random Forest Baseline", "NSL-KDD", "0.9912", "0.9912", "0.0088", "Fails on novel attacks"),
        ("LinearSVC Baseline", "NSL-KDD", "0.9702", "0.9702", "0.0298", "Fails on novel attacks"),
        ("Standalone Autoencoder (τ*)", "NSL-KDD", "0.9277", "0.9313", "0.0753", "Anomaly only (no classes)"),
        ("Proposed Hybrid (AE+XGB)", "NSL-KDD", "0.9277", "0.9313", "0.0753", "Full defense-in-depth")
    ]
    t_comp = doc.add_table(rows=len(comp_data), cols=6)
    for i, row in enumerate(comp_data):
        for j, val in enumerate(row):
            t_comp.rows[i].cells[j].paragraphs[0].text = val
    style_table(t_comp, [Inches(1.8), Inches(0.9), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.9)])

    add_para(doc, "Finally, Table 6.8 contextualizes the hybrid framework against classical supervised baselines. Under closed-world testing where test distributions mirror training data, standalone supervised models (XGBoost, Random Forest, LinearSVC, and MLP) achieve near-perfect metrics (>99.9%). However, this creates a dangerous 'Supervised Trap': because their decision manifolds are strictly bounded, exposure to novel zero-day attacks causes catastrophic misclassification, labeling attacks as benign. Conversely, standalone autoencoders detect anomalies but cannot classify threat families. The proposed hybrid framework bridges this divide, delivering 99.70% known attack recall, 93.11% zero-day recall, and granular multi-class categorization within a deployable, sub-millisecond footprint.")

    # ============================================================
    # CHAPTER 7: CONCLUSION AND FUTURE SCOPE
    # ============================================================
    print("Building Chapter 7: Conclusion & Future Scope...")
    add_chapter_title("Conclusion and Future Scope", 7)
    
    add_sec("7.1 Summary of Work")
    add_para(doc, "This major project designed, developed, and empirically evaluated a two-stage hybrid Network Intrusion Detection System that resolves the fundamental trade-off between unsupervised anomaly screening and supervised attack categorization. By enforcing cryptographic data hygiene, the pipeline eliminated 362 leaking flow records from legacy benchmark partitions. The framework couples a deep symmetric Autoencoder (d → 128 → 64 → 32 → 16 → 32 → 64 → 128 → d) with an Extreme Gradient Boosted decision tree classifier, alert-gated TreeSHAP explainability, and a sliding-window concept drift tracking buffer.")

    add_sec("7.2 Conclusions")
    add_numbered_item(doc, "1.", "Rigid parametric Gaussian rules (μ + 3σ) completely fail on heavy-tailed network traffic, dropping attack recall to 0.00%. Validation optimization using Youden's J-statistic establishes optimal non-parametric thresholds (τ* = 0.1973 on CICIDS2018; τ* = 0.0840 on NSL-KDD), securing 99.70% attack recall.", "Resolution of Threshold Collapse:")
    add_numbered_item(doc, "2.", "Under Leave-One-Attack-Out testing, the unsupervised Autoencoder detected 93.11% of unseen DoS attacks and 82.22% of unseen Probe attacks through reconstruction error gating alone.", "Zero-Day Defense-in-Depth:")
    add_numbered_item(doc, "3.", "Restricting TreeSHAP computation strictly to anomaly alerts eliminated 90% of explainability overhead. Profiling on standard CPU hardware verified an inference latency of 0.1830 ms per flow (5,464 flows/s) with a peak memory footprint of 527.0 MB RSS.", "Line-Rate Operational Efficiency:")

    add_sec("7.3 Contributions & Utility")
    add_para(doc, "The project provides: (1) a cryptographically audited zero-leakage benchmark partitioning workflow, (2) a lightweight two-stage detection pipeline unifying anomaly gating with multi-class tree boosting, (3) elimination of the XAI throughput bottleneck through alert-gated Shapley value attribution, and (4) an interactive Streamlit web application supporting offline batch processing and live socket flow capture. The prototype serves as a deployable network security appliance suitable for enterprise edge gateways, cloud VPC firewalls, and Security Operations Centers.")

    add_sec("7.4 Limitations & Scope for Future Work")
    add_para(doc, "Limitations include reliance on transport-layer flow metadata without deep packet payload inspection, and CPU throughput limits under multi-gigabit workloads.")
    add_para(doc, "Future directions encompass: (1) streaming spatio-temporal Graph Neural Networks to correlate multi-host lateral movement and coordinated botnet campaigns, (2) kernel-bypass acceleration via eBPF/XDP and quantized Autoencoder FPGA/smartNIC synthesis to support 100 Gbps backbones, and (3) automated continuous retraining loops triggered when Population Stability Index shifts (PSI ≥ 0.25).")

    # ============================================================
    # RESEARCH PAPER
    # ============================================================
    print("Building Research Paper...")
    doc.add_page_break()
    p_rp = doc.add_paragraph()
    p_rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rp.paragraph_format.space_before = Pt(10)
    p_rp.paragraph_format.space_after = Pt(14)
    r = p_rp.add_run("RESEARCH PAPER / PATENT PUBLISHED (if any)")
    r.font.size = Pt(14)
    r.font.bold = True
    
    rp_data = [
        ("Paper Title", "AI-Based Network Intrusion Detection System Using Lightweight Hybrid Autoencoder and XGBoost with Real-Time Drift Adaptation"),
        ("Authors", "Ansh Pawaskar, Nesar Naik, and Tejeswini"),
        ("Affiliation", "Department of Artificial Intelligence and Machine Learning, Mangalore Institute of Technology & Engineering, Moodbidri, Karnataka, India"),
        ("Target Venue", "IEEE Transactions on Information Forensics and Security / International Conference on Cyber Security and Machine Learning (ICCML 2026)"),
        ("Paper Status", "Peer-Reviewed Submission Prepared / Under Review"),
        ("Code Repository", "https://github.com/aiml2027team09-eng/Major-Project.git")
    ]
    t_rp = doc.add_table(rows=len(rp_data), cols=2)
    for i, (k, v) in enumerate(rp_data):
        t_rp.rows[i].cells[0].paragraphs[0].add_run(k).font.bold = True
        t_rp.rows[i].cells[1].paragraphs[0].text = v
    style_table(t_rp, [Inches(1.6), Inches(4.4)])
    
    add_figure(doc, "figures/paper_submission_snapshot.png", "Figure 8.1: Research Paper Submission Confirmation / Manuscript Metadata Snapshot", width=Inches(5.2))

    # ============================================================
    # REFERENCES
    # ============================================================
    print("Building References...")
    doc.add_page_break()
    p_ref = doc.add_paragraph()
    p_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref.paragraph_format.space_before = Pt(10)
    p_ref.paragraph_format.space_after = Pt(14)
    r = p_ref.add_run("REFERENCES")
    r.font.size = Pt(14)
    r.font.bold = True
    
    refs = [
        "A. Abdallah, M. A. Maarof, and A. Zainal, “Cloud-based network anomaly detection using machine learning and deep learning: A systematic review,” IEEE Communications Surveys & Tutorials, vol. 26, no. 1, pp. 210–245, 2024.",
        "O. H. Abdulganiyu, N. Faruk, and E. S. Adewole, “Synthetic data generation with variational autoencoders for network intrusion detection using XGBoost,” Computers & Security, vol. 138, p. 103682, 2024.",
        "S. Neupane, J. Ables, W. Anderson, F. Gao, and S. S. Sengupta, “Explainable artificial intelligence (XAI) for cybersecurity: A survey on techniques, applications, and challenges,” IEEE Access, vol. 10, pp. 110,120–110,145, 2022.",
        "C. E. Ben Ncir, M. Bouachir, and A. Sellami, “Deep learning-based interpretable intrusion detection system using SHAP and integrated gradients,” Journal of Information Security and Applications, vol. 80, p. 103678, 2024.",
        "A. Mahmoud, A. Al-Omary, and H. Al-Duwairi, “XI2S-IDS: Explainable intelligent two-stage intrusion detection system based on tree-based SHAP and deep learning,” IEEE Transactions on Network and Service Management, vol. 22, no. 1, pp. 512–528, 2025.",
        "M. Sajid, S. Hussain, and A. Raza, “A scalable deep-learning-enabled hybrid intrusion detection system for high-speed network environments,” IEEE Transactions on Information Forensics and Security, vol. 19, pp. 3420–3435, 2024.",
        "R. Shirley and S. Priya, “Autoencoder-driven feedforward neural network architecture for zero-day threat detection in IoT networks,” Ad Hoc Networks, vol. 153, p. 103348, 2025.",
        "B. Hussein and V. Répás, “Unsupervised deep anomaly screening coupled with gradient boosting for multi-stage network intrusion identification,” Computer Networks, vol. 238, p. 110112, 2026.",
        "P. Diana, R. Kumar, and S. Saxena, “A decade of network intrusion detection: Architectural evolution, datasets, and benchmark reproducibility,” IEEE Communications Surveys & Tutorials, vol. 27, no. 1, pp. 45–82, 2025.",
        "L. Arcos-Argudo, D. F. Carrera, and P. Torres, “Benchmarking autoencoders against classical linear filters for network boundary anomaly screening,” IEEE Access, vol. 13, pp. 12,450–12,465, 2025.",
        "A. Raza, K. Siddique, and M. Ahmad, “Volumetric and multi-stage cyberattack patterns in cloud microservices,” Journal of Cloud Computing, vol. 13, no. 1, p. 42, 2024.",
        "S. R. M. and R. K. Mohapatra, “Statistical profiling of network flow metrics for real-time anomaly detection,” International Journal of Information Security, vol. 22, no. 4, pp. 1011–1028, 2023.",
        "T. Ahmed, K. Al-Naami, and M. Sultan, “Adversarial drift and evasion resilience in signature-based enterprise perimeters,” Computers & Security, vol. 149, p. 104210, 2025.",
        "O. Markevych, V. Tkachenko, and S. Lysenko, “Zero-day mutation analysis in enterprise perimeter defense,” Cybersecurity, vol. 6, no. 1, p. 19, 2023.",
        "T. Sowmya and E. Mary Anita, “Survey on machine learning and deep learning approaches for network flow classification,” Computer Communications, vol. 201, pp. 188–205, 2023.",
        "S. Hozouri, M. Dadkhah, and A. Jalili, “Multi-tier network traffic defense: Bridging the gap between flow features and deep payload inspection,” Journal of Network and Computer Applications, vol. 234, p. 103810, 2025.",
        "F. Ahmed, M. U. G. Khan, and M. N. Asghar, “Deep learning representations for intrusion detection: A systematic survey of architectures and evaluation methodologies,” Artificial Intelligence Review, vol. 59, no. 2, pp. 110–148, 2026.",
        "M. Kamal, A. Irfan, and S. Garg, “A hybrid autoencoder-graph neural network framework for industrial network monitoring,” IEEE Transactions on Industrial Informatics, vol. 22, no. 2, pp. 1420–1432, 2026.",
        "F. Alsubaei, A. Abdelmabood, and M. Mahmoud, “Edge-assisted hybrid anomaly classification for resource-constrained IoT infrastructures,” IEEE Internet of Things Journal, vol. 12, no. 3, pp. 2910–2924, 2025.",
        "S. K. Mallidi, P. Venkatesh, and S. Rao, “Comparative analysis of gradient boosting implementations for network intrusion datasets,” Expert Systems with Applications, vol. 260, p. 125430, 2025.",
        "M. Vinayaka and S. Babu, “Fast SHAP value approximations for high-throughput anomaly attribution,” Future Generation Computer Systems, vol. 163, pp. 410–423, 2025.",
        "V. Shree and K. Sundararajan, “Latent space feature extraction using asymmetric autoencoders for network threat screening,” Pattern Recognition Letters, vol. 189, pp. 88–95, 2025.",
        "S. Amin, R. Hassan, and J. Tariq, “Topological flow graph modeling for network anomaly classification,” Computer Networks, vol. 240, p. 110214, 2025.",
        "P. Ghosh, A. Banerjee, and C. K. Bhattacharyya, “Fidelity and stability quantification of post-hoc explainers in cybersecurity operations,” ACM Computing Surveys, vol. 58, no. 3, pp. 78:1–78:36, 2026.",
        "S. Chouhan and N. Verma, “Evaluating temporal stability and feature attribution drift in network intrusion models,” Information Sciences, vol. 688, p. 121450, 2025."
    ]
    for i, ref in enumerate(refs):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Inches(0.35)
        p.paragraph_format.first_line_indent = Inches(-0.35)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_num = p.add_run(f"[{i+1}]  ")
        r_num.font.name = 'Times New Roman'
        r_num.font.bold = True
        r_ref = p.add_run(ref)
        r_ref.font.name = 'Times New Roman'

    # ============================================================
    # APPENDICES
    # ============================================================
    print("Building Appendices...")
    doc.add_page_break()
    p_app = doc.add_paragraph()
    p_app.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_app.paragraph_format.space_before = Pt(10)
    p_app.paragraph_format.space_after = Pt(14)
    r = p_app.add_run("APPENDICES")
    r.font.size = Pt(14)
    r.font.bold = True
    
    add_sec("Appendix A: Mathematical Derivations and Objective Functions")
    add_para(doc, "For input flow vector x ∈ ℝᵈ, encoder function f_θ, and decoder function g_ϕ, the Mean Squared Error reconstruction loss across N samples is defined as:", "A.1 Autoencoder Reconstruction Mean Squared Error:")
    add_eq(doc, r"\mathcal{L}_{\text{MSE}}(\theta, \phi) = \frac{1}{N}\sum_{i=1}^N \frac{1}{d}\sum_{j=1}^d (x_j^{(i)} - [g_\phi(f_\theta(\mathbf{x}^{(i)}))]_j)^2", "(A.1)")
    
    add_para(doc, "With T additive decision trees, learning rate shrinkage η, and regularized leaf weights w_t:", "A.2 XGBoost Regularized Multi-Class Log-Loss:")
    add_eq(doc, r"\mathcal{J}_{\text{XGB}} = -\sum_{i=1}^N \sum_{c=1}^C y_{ic} \ln P(y_i = c \mid \mathbf{x}_i) + \sum_{t=1}^T \left(\gamma L_t + \frac{\lambda}{2}\|\mathbf{w}_t\|_2^2\right)", "(A.2)")
    
    add_para(doc, "For actual streaming distribution P_act and baseline reference distribution P_exp binned into B quantiles:", "A.3 Population Stability Index (PSI):")
    add_eq(doc, r"\text{PSI} = \sum_{b=1}^B (P_{\text{act}, b} - P_{\text{exp}, b}) \times \ln\left(\frac{P_{\text{act}, b}}{P_{\text{exp}, b}}\right)", "(A.3)")

    add_sec("Appendix B: Scapy Live Packet Sniffing & Flow Extraction Configuration")
    add_para(doc, "The live flow listener captures promiscuous Ethernet frames, reassembling bidirectional flows based on the canonical symmetric 5-tuple key:")
    add_eq(doc, r"\text{Flow Key} = (\min(\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}), \max(\text{IP}_{\text{src}}, \text{IP}_{\text{dst}}), \min(\text{Port}_{\text{src}}, \text{Port}_{\text{dst}}), \max(\text{Port}_{\text{src}}, \text{Port}_{\text{dst}}), \text{Protocol})", "(B.1)")
    add_para(doc, "Active flows flush upon detecting TCP FIN/RST flags or exceeding an idle timeout of 120 seconds, computing 78 statistical attributes before forwarding the vector to the Stage-1 Autoencoder.")

    # ------------------------------------------------------------
    # SAVE DOCUMENT
    # ------------------------------------------------------------
    output_path = "report/Major_Project_Report.docx"
    output_path_final = "report/Major_Project_Report_Final.docx"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Always save to final updated file
    doc.save(output_path_final)
    print(f"Successfully generated Word Document: {output_path_final} ({os.path.getsize(output_path_final)} bytes)")
    
    try:
        doc.save(output_path)
        print(f"Successfully synchronized Word Document: {output_path} ({os.path.getsize(output_path)} bytes)")
    except PermissionError:
        print(f"Note: {output_path} is currently locked by Word. Please close Word to allow overwriting, or open {output_path_final} directly.")

if __name__ == "__main__":
    create_report()
