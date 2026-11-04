import docx

doc = docx.Document('report/Major_Project_Report_Final_Updated.docx')
body = doc._body._body

for i in range(70, 115):
    el = body[i]
    tag = el.tag.split('}')[-1]
    txt = ''.join(el.itertext()).strip()[:60].encode('ascii', 'replace').decode()
    pBef = bool(el.xpath('.//w:pageBreakBefore'))
    brP = bool(el.xpath('.//w:br[@w:type="page"]'))
    sp = el.xpath('./w:pPr/w:spacing')
    sp_attr = sp[0].attrib if sp else ''
    kn = bool(el.xpath('./w:pPr/w:keepNext'))
    print(f"Elem {i:3d} ({tag}): pBef={pBef}, brP={brP}, kn={kn}, sp={sp_attr} | text={repr(txt)}")
