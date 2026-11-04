import docx, json, re

doc = docx.Document('report/Major_Project_Report_Final.docx')

targets = []

for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if not t:
        continue
    # Heading Chapter
    if re.match(r'^CHAPTER\s+\d+', t, re.IGNORECASE):
        targets.append({'index': i, 'type': 'CHAPTER', 'text': t})
    # Heading Section / Subsection
    elif re.match(r'^\d+\.\d+(\.\d+)?\s+', t):
        targets.append({'index': i, 'type': 'SECTION', 'text': t})
    # Special subsections in Ch 3 and Ch 4
    elif t in ["Functional & Non-Functional Requirements", "Hardware & Software Requirements"]:
        targets.append({'index': i, 'type': 'SUBSECTION', 'text': t})
    elif t in [
        "Autoencoder Latent Topology & Manifold Projection",
        "Sequence Diagram of Packet Ingestion and Prediction",
        "Activity Diagram of Tiered Detection and Alert Routing",
        "Data Flow Diagram (DFD Level-1) for Flow Processing",
        "Class Diagram and Use Case Diagram"
    ]:
        targets.append({'index': i, 'type': 'SUBSECTION', 'text': t})
    elif t.startswith('REFERENCES') or t.startswith('APPENDICES') or t.startswith('Appendix '):
        targets.append({'index': i, 'type': 'BACKMATTER', 'text': t})
    elif re.match(r'^Figure\s+\d+\.\d+\s*:', t):
        targets.append({'index': i, 'type': 'FIGURE', 'text': t})
    elif re.match(r'^Table\s+\d+\.\d+\s*:', t):
        targets.append({'index': i, 'type': 'TABLE', 'text': t})

with open('scratch/target_paragraphs.json', 'w', encoding='utf-8') as f:
    json.dump(targets, f, indent=2)

print(f"Collected {len(targets)} clean targets:")
for item in targets:
    print(f"[{item['index']:3d}] {item['type']:10s} | {item['text'][:65]}")

print(f"Collected {len(targets)} target paragraphs.")
for item in targets[:15]:
    print(f"[{item['index']:3d}] {item['type']:10s} | {item['text']}")
