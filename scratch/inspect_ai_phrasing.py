import docx, sys
sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document('report/Major_Project_Report_Final_Updated.docx')

sections_to_check = [
    (69, 72, "ABSTRACT"),
    (83, 86, "1.1 Background"),
    (86, 89, "1.2 Problem Statement"),
    (112, 120, "1.6 Significance"),
    (130, 136, "2.1 Introduction"),
    (142, 148, "2.4 Research Gap"),
    (318, 326, "6.2 Threshold Analysis"),
    (350, 360, "6.4 Latency & Comparisons"),
    (371, 375, "7.2 Conclusions")
]

for start, end, label in sections_to_check:
    print(f"\n{'='*20} {label} {'='*20}")
    for i in range(start, min(end, len(doc.paragraphs))):
        print(f"[{i}] {doc.paragraphs[i].text}")
