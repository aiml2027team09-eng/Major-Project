import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/figures_tables_pages.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

print("=== FIGURES IN BODY ===")
for fig in data['Figures']:
    if fig['Page'] > 9: # in body
        print(f"{fig['Number']:12s} | Page {fig['Page']:2d} | {fig['Title'][:60]}")

print("\n=== TABLES IN BODY ===")
for tbl in data['Tables']:
    if tbl['Page'] > 9: # in body
        print(f"{tbl['Number']:12s} | Page {tbl['Page']:2d} | {tbl['Title'][:60]}")
