import docx

doc = docx.Document("report/test_page_numbers.docx")

print("Total sections:", len(doc.sections))
for i, sec in enumerate(doc.sections):
    print(f"=== SECTION {i} ===")
    print("  start_type:", sec.start_type)
    print("  diff_first_page:", sec.different_first_page_header_footer)
    print("  footer linked:", sec.footer.is_linked_to_previous)
    pgNum = sec._sectPr.xpath("./w:pgNumType")
    print("  pgNumType:", [x.attrib for x in pgNum])
    print("  footer XML:", sec.footer._element.xml[:180].strip())

print("\n=== FRONT MATTER PARAGRAPHS & BREAKS ===")
for i, p in enumerate(doc.paragraphs[:95]):
    xml = p._element.xml
    pb = 1 if 'type="page"' in xml else 0
    sp = 1 if '<w:sectPr' in xml else 0
    t = p.text.strip()
    if pb or sp or any(k in t for k in ["ABSTRACT", "TABLE OF CONTENTS", "LIST OF FIGURES", "LIST OF TABLES", "ABBREVIATIONS", "CHAPTER 1"]):
        print(f"P{i}: pb={pb} sp={sp} text={repr(t[:40])}")
