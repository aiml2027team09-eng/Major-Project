import win32com.client as win32
import os

word = win32.Dispatch("Word.Application")
word.Visible = False
try:
    doc_path = os.path.abspath('report/Part B_26AI09.docx')
    doc = word.Documents.Open(doc_path)
    
    # Let's inspect Page 1 and Page 2
    # In Word, we can go to page 1 and page 2 using Selection or Range
    print(f"Total pages: {doc.ComputeStatistics(2)}")
    
    # Find Section 1.3 and 1.4
    rng = doc.Content
    rng.Find.Execute("1.3 Motivation")
    p13_page = rng.Information(3)
    
    rng = doc.Content
    rng.Find.Execute("1.4 Objectives")
    p14_page = rng.Information(3)
    p14_vert = rng.Information(6)
    
    print(f"1.3 Motivation is on Page {p13_page}")
    print(f"1.4 Objectives is on Page {p14_page}, vertical pos = {p14_vert} pt")
    
    # What else is on p14_page before 1.4 Objectives?
    # Let's check paragraph right before 1.4 Objectives
    for i, p in enumerate(doc.Paragraphs):
        txt = p.Range.Text.strip()
        if "1.4 Objectives" in txt:
            print(f"1.4 Objectives is at paragraph index {i+1}")
            prev_p = doc.Paragraphs(i) # 1-based previous paragraph
            print(f"Previous paragraph page: {prev_p.Range.Information(3)}, vert={prev_p.Range.Information(6)}, text: {repr(prev_p.Range.Text.strip()[:60])}")
            break
            
    # Check Listing B.1
    rng = doc.Content
    rng.Find.Execute("Listing B.1 provides")
    b1_intro_page = rng.Information(3)
    b1_intro_vert = rng.Information(6)
    
    rng = doc.Content
    rng.Find.Execute("Listing B.1: Real-Time")
    b1_title_page = rng.Information(3)
    b1_title_vert = rng.Information(6)
    
    print(f"Listing B.1 intro is on Page {b1_intro_page}, vert={b1_intro_vert}")
    print(f"Listing B.1 title is on Page {b1_title_page}, vert={b1_title_vert}")
    
    doc.Close(0)
finally:
    word.Quit()
