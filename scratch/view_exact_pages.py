import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/exact_pages.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print(f"{'Type':10s} | {'Page':4s} | Text")
print("-" * 70)
for item in data:
    txt = item['OriginalText'].replace('\n', ' ')
    print(f"{item['Type']:10s} | {item['Page']:4d} | {txt[:65]}")
