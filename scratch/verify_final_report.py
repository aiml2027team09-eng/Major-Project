import docx

doc = docx.Document('report/Major_Project_Report_Final_Updated.docx')

print('=== 1. CHECK SECTION 1.4 SPACING ===')
for i, p in enumerate(doc.paragraphs):
    if '1.4 Objectives' in p.text:
        prev_p = doc.paragraphs[i-1]
        print(f"Previous paragraph ({i-1}): {prev_p.text[-60:]}")
        print(f"Previous spacing: before={prev_p.paragraph_format.space_before}, after={prev_p.paragraph_format.space_after}, line={prev_p.paragraph_format.line_spacing}")
        print(f"1.4 Objectives spacing: before={p.paragraph_format.space_before}, after={p.paragraph_format.space_after}, line={p.paragraph_format.line_spacing}")
        break

print('\n=== 2. CHECK LISTING B.1 SPACING ===')
for i, p in enumerate(doc.paragraphs):
    if 'Listing B.1:' in p.text:
        prev_p = doc.paragraphs[i-1]
        print(f"Previous paragraph ({i-1}): {prev_p.text[:60]}")
        print(f"Previous spacing: before={prev_p.paragraph_format.space_before}, after={prev_p.paragraph_format.space_after}, line={prev_p.paragraph_format.line_spacing}")
        print(f"Listing B.1 spacing: before={p.paragraph_format.space_before}, after={p.paragraph_format.space_after}, line={p.paragraph_format.line_spacing}")
        break

print('\n=== 3. CHECK CODE LISTINGS ALIGNMENT ===')
code_alignments = set()
font_names = set()
for t in doc.tables:
    if len(t.rows) == 1 and len(t.columns) == 1:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    code_alignments.add(str(p.paragraph_format.alignment))
                    for r in p.runs:
                        font_names.add(r.font.name)
print(f"Code paragraph alignments: {code_alignments}")
print(f"Code run font names: {font_names}")

print('\n=== 4. CHECK EMPTY BODY PARAGRAPHS ===')
empty_count = 0
for i, p in enumerate(doc.paragraphs[74:]):
    txt = p.text.strip()
    has_img = bool(p._p.xpath('.//w:drawing'))
    has_pb = bool(p._p.xpath('.//w:br[@w:type="page"]'))
    if not txt and not has_img and not has_pb:
        empty_count += 1
        print(f"Empty paragraph at body index {i}: XML={p._p.xml[:120]}")
print(f"Total non-structural empty body paragraphs: {empty_count}")

print('\n=== 5. CHECK PRELIMINARY TABLES (TOC, LOF, LOT) ===')
t1 = doc.tables[1] # TOC
print(f"TOC rows: {len(t1.rows)}, Sample TOC entries:")
for r in list(t1.rows)[1:6]:
    print(f"  {r.cells[0].text} | {r.cells[1].text} | Page {r.cells[2].text}")

t2 = doc.tables[2] # LOF
print(f"LOF rows: {len(t2.rows)}, Sample LOF entries:")
for r in list(t2.rows)[1:4]:
    print(f"  {r.cells[0].text} | {r.cells[1].text} | Page {r.cells[2].text}")

t3 = doc.tables[3] # LOT
print(f"LOT rows: {len(t3.rows)}, Sample LOT entries:")
for r in list(t3.rows)[1:4]:
    print(f"  {r.cells[0].text} | {r.cells[1].text} | Page {r.cells[2].text}")
