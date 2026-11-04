import docx

doc = docx.Document('report/Major_Project_Report_Final.docx')
body = doc._body._body
for idx in range(68, 85):
    elem = body[idx]
    xml = elem.xml
    tag = elem.tag.split('}')[-1]
    text = ""
    if tag == 'p':
        text = docx.text.paragraph.Paragraph(elem, doc).text[:40]
    elif tag == 'tbl':
        text = f"tbl ({len(elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr'))} rows)"
    has_pb = 'type="page"' in xml or 'lastRenderedPageBreak' in xml
    has_sp = 'sectPr' in xml
    print(f"{idx:2d} | {tag:4s} | pb={str(has_pb):5s} | sp={str(has_sp):5s} | {text}")
