import docx, sys, re
sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document('report/Part B_26AI09.docx')

print(f"Total Paragraphs: {len(doc.paragraphs)}")

potential_triggers = []

for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if not t or len(t) < 40:
        continue
        
    # Check for phrases that frequently appear in other NIDS theses on the internet
    phrases = [
        "is defined as the ratio of",
        "confusion matrix is a table",
        "precision is the ratio",
        "recall is the ratio",
        "support vector machine",
        "k-nearest neighbor",
        "decision tree is a",
        "network intrusion detection system is a system",
        "distributed denial of service attack is",
        "in this section we discuss",
        "as shown in figure",
        "in order to",
        "it can be seen that"
    ]
    
    matches = [ph for ph in phrases if ph in t.lower()]
    if matches:
        potential_triggers.append((i, matches, t[:90]))

print(f"Found {len(potential_triggers)} potential generic phrase occurrences:")
for idx, m, snippet in potential_triggers[:10]:
    print(f"[{idx:3d}] Matches: {m} -> {snippet}...")
