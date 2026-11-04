import docx
from lxml import etree
import shutil

src = 'report/Major_Project_Report_Final_Updated.docx'
part_b_out = 'report/Part B_26AI09.docx'

print("Generating Part B test...")
doc_b = docx.Document(src)
body_b = doc_b._body._body

ch1_elem_b = None
for p in doc_b.paragraphs:
    if p.text.strip().startswith("CHAPTER 1"):
        ch1_elem_b = p._p
        break

ch1_idx_b = list(body_b).index(ch1_elem_b)
print(f"Removing preliminary elements 0 to {ch1_idx_b}")
for elem in list(body_b)[:ch1_idx_b]:
    body_b.remove(elem)

# Strip all headerReference and footerReference from all sections
for s in doc_b.sections:
    s.header.is_linked_to_previous = False
    s.footer.is_linked_to_previous = False
    sectPr = s._sectPr
    for child in list(sectPr):
        tag = child.tag.split('}')[-1]
        if tag in ['headerReference', 'footerReference']:
            sectPr.remove(child)

doc_b.save(part_b_out)
print("Saved stripped Part B")

# Now add clean footer page numbers using add_part_b_page_numbers
import sys
sys.path.append('scripts')
from add_part_b_page_numbers import add_footer_page_number
add_footer_page_number(part_b_out)
shutil.copy2(part_b_out, 'report/Part B_Batch_number.docx')
print("Part B generation complete!")
