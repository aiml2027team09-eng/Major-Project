import docx

doc_a = docx.Document('report/Major_Project_Report_Final_Updated.docx')
body_a = doc_a._body._body
ch1_elem_a = None
for p in doc_a.paragraphs:
    if p.text.strip().startswith('CHAPTER 1'):
        ch1_elem_a = p._p
        break
ch1_idx_a = list(body_a).index(ch1_elem_a)
for elem in list(body_a)[ch1_idx_a:]:
    body_a.remove(elem)

last_p = None
for child in reversed(list(body_a)):
    if child.tag.endswith('p'):
        last_p = child
        break

sectPr_in_p = last_p.xpath('./w:pPr/w:sectPr')
print('sectPr found in last paragraph:', len(sectPr_in_p))
if sectPr_in_p:
    sp = sectPr_in_p[0]
    sp.getparent().remove(sp)
    body_a.append(sp)

print('doc_a.sections now:', len(doc_a.sections))
for i, s in enumerate(doc_a.sections):
    pg = [el.attrib for el in s._sectPr.xpath('./w:pgNumType')]
    print(f'Part A Section {i}: type={s.start_type}, pgNumType={pg}')

doc_b = docx.Document('report/Major_Project_Report_Final_Updated.docx')
body_b = doc_b._body._body
ch1_elem_b = None
for p in doc_b.paragraphs:
    if p.text.strip().startswith('CHAPTER 1'):
        ch1_elem_b = p._p
        break
ch1_idx_b = list(body_b).index(ch1_elem_b)
for elem in list(body_b)[:ch1_idx_b]:
    body_b.remove(elem)

print('doc_b.sections now:', len(doc_b.sections))
for i, s in enumerate(doc_b.sections):
    pg = [el.attrib for el in s._sectPr.xpath('./w:pgNumType')]
    print(f'Part B Section {i}: type={s.start_type}, pgNumType={pg}')

