import docx

doc = docx.Document('report/Major_Project_Report_Final_Updated.docx')
body = doc._body._body

useless_elems = []
for i, el in enumerate(body):
    tag = el.tag.split('}')[-1]
    if tag == 'p':
        txt = ''.join(el.itertext()).strip()
        has_draw = len(el.xpath('.//w:drawing')) > 0
        has_pb = len(el.xpath('.//w:br[@w:type="page"]')) > 0
        has_sectPr = len(el.xpath('./w:pPr/w:sectPr')) > 0
        if not txt and not has_draw and not has_pb and not has_sectPr:
            prv = body[i-1].tag.split('}')[-1] if i > 0 else 'START'
            nxt = body[i+1].tag.split('}')[-1] if i < len(body)-1 else 'END'
            prv_t = ''.join(body[i-1].itertext()).strip()[:40].encode('ascii', 'replace').decode() if i > 0 else ''
            nxt_t = ''.join(body[i+1].itertext()).strip()[:40].encode('ascii', 'replace').decode() if i < len(body)-1 else ''
            print(f"Elem {i:3d}: [{prv:3s}] {repr(prv_t):42s} ---> [{nxt:3s}] {repr(nxt_t)}")
            useless_elems.append(el)

print(f"\nTotal empty paragraphs found: {len(useless_elems)}")
