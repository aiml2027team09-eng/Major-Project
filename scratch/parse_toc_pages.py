import json

with open('scratch/toc_pages.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print(f"{'Type':12s} | {'Page':4s} | {'AdjPage':7s} | Heading Text")
print("-" * 75)

for item in data:
    txt = item['Text']
    # Filter out table numbers or decimals like 0.0003
    if (any(txt.startswith(f"{c}.") for c in range(1, 8)) or 
        txt.startswith('CHAPTER') or 
        txt.startswith('REFERENCES') or 
        txt.startswith('APPENDIC') or 
        txt.startswith('Appendix') or 
        'Requirements' in txt or 
        'Diagram' in txt or 
        'Topology' in txt):
        print(f"{item['Type']:12s} | {item['Page']:4d} | {item['AdjPage']:7d} | {txt}")
