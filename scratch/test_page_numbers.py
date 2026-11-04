import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import shutil

src = "report/Major_Project_Report_Final.docx"
test_out = "report/test_page_numbers.docx"
shutil.copy2(src, test_out)

doc = docx.Document(test_out)

# 1. Clean up paragraphs between Acknowledgements and Abstract
ack_idx = None
abstract_idx = None
for i, p in enumerate(doc.paragraphs[:100]):
    if i > 60 and "Ansh Pawaskar" in p.text:
        ack_idx = i
    if p.text.strip() == "ABSTRACT":
        abstract_idx = i

print(f"Acknowledgements end idx: {ack_idx}, Abstract idx: {abstract_idx}")
assert ack_idx is not None and abstract_idx is not None

# Paragraphs between ack_idx and abstract_idx
# Specifically, P74 has sectPr. P75, P76, P77, P78 are empty or contain extra page breaks.
sect_break_p = None
p_to_remove = []

for j in range(ack_idx + 1, abstract_idx):
    p = doc.paragraphs[j]
    if len(p._element.xpath("./w:pPr/w:sectPr")) > 0:
        sect_break_p = p
    else:
        p_to_remove.append(p)

print(f"sect_break_p found: {sect_break_p is not None}")
print(f"paragraphs to remove: {len(p_to_remove)}")

# In sect_break_p, remove any runs (which contain <w:br w:type="page"/>)
if sect_break_p is not None:
    for r in list(sect_break_p.runs):
        sect_break_p._p.remove(r._r)

# Remove the redundant empty paragraphs
for p in p_to_remove:
    p._p.getparent().remove(p._p)

print("Cleaned up redundant breaks between Ack and Abstract.")

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

# Section 0: Title page
set_footer_empty(doc.sections[0])
set_pgNumType(doc.sections[0], start="1")

# Section 1: Certificate
set_footer_empty(doc.sections[1])
set_pgNumType(doc.sections[1])

# Section 2: Declaration & Acknowledgements
set_footer_empty(doc.sections[2])
set_pgNumType(doc.sections[2])

# Section 3: Abstract to Abbreviations
doc.sections[3].start_type = WD_SECTION_START.NEW_PAGE
for el in doc.sections[3]._sectPr.xpath('./w:type'):
    doc.sections[3]._sectPr.remove(el)
set_footer_page_number(doc.sections[3], default_text="v")
set_pgNumType(doc.sections[3], fmt="lowerRoman", start="5")

# Section 4: Chapters starting at Chapter 1
doc.sections[4].start_type = WD_SECTION_START.NEW_PAGE
set_footer_page_number(doc.sections[4], default_text="1")
set_pgNumType(doc.sections[4], fmt="decimal", start="1")

doc.save(test_out)
print("Saved test document successfully.")
