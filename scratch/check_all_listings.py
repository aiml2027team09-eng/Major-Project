import docx

doc = docx.Document('report/Major_Project_Report_Final_Updated.docx')
body = doc._body._body

for i, el in enumerate(body):
    txt = ''.join(el.itertext()).strip()
    if 'Listing ' in txt:
        tag = el.tag.split('}')[-1]
        print(f"Elem {i:3d} ({tag}): text={repr(txt[:65])}")
        pPr = el.xpath('./w:pPr')
        if pPr:
            sp = pPr[0].xpath('./w:spacing')
            if sp:
                print(f"    spacing: {sp[0].attrib}")
