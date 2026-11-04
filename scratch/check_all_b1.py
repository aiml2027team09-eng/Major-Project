import docx, glob

for fn in sorted(glob.glob('report/*.docx')):
    if '~$' in fn: continue
    try:
        doc = docx.Document(fn)
        for i, p in enumerate(doc.paragraphs):
            if 'Listing B.1: Real-Time' in p.text:
                prev_p = doc.paragraphs[i-1] if i > 0 else None
                prev_text = prev_p.text[:40].encode('ascii', 'replace').decode() if prev_p else 'None'
                print(f"{fn} -> P{i}: prev_p=[{repr(prev_text)}]")
    except Exception as e:
        print(f"{fn} -> error {e}")
