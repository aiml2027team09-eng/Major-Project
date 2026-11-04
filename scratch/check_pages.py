import docx

doc = docx.Document("report/Major_Project_Report_Final.docx")
for i, p in enumerate(doc.paragraphs[:100]):
    xml = p._element.xml
    pb = 1 if 'type="page"' in xml else 0
    sp = 1 if '<w:sectPr' in xml else 0
    t = p.text.strip()
    if pb or sp or any(k in t for k in ["ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "ABBREVIATIONS", "CHAPTER 1"]):
        print(f"{i}: pb={pb} sp={sp} text={repr(t[:40])}")
