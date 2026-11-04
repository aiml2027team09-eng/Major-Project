import docx

doc = docx.Document('report/Part B_26AI09.docx')
print(f"Total paragraphs in Part B: {len(doc.paragraphs)}")

for i, p in enumerate(doc.paragraphs):
    if not p.text.strip():
        prv = doc.paragraphs[i-1].text[:50].encode('ascii', 'replace').decode('ascii') if i > 0 else 'START'
        nxt = doc.paragraphs[i+1].text[:50].encode('ascii', 'replace').decode('ascii') if i < len(doc.paragraphs)-1 else 'END'
        pBef = bool(p._p.xpath('.//w:pageBreakBefore'))
        brP = bool(p._p.xpath('.//w:br[@w:type="page"]'))
        print(f"Empty P{i}: pBef={pBef}, brP={brP} | Prev: {repr(prv)} | Next: {repr(nxt)}")
