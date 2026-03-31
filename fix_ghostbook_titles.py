"""
fix_ghostbook_titles.py
Joins books_scored.jsonl back to books_raw.jsonl by position index.
The scorer writes book_title from book.get('title') but all scored records
show 'Unknown' — this patches them with the real titles from raw.
Also exports high_signal_leads.jsonl (composite >= 5.5).
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "G:/My Drive/Projects/_studio/ghostbooks_eval/data"
RAW   = f"{BASE}/books_raw.jsonl"
SCORED = f"{BASE}/books_scored.jsonl"
LEADS  = f"{BASE}/high_signal_leads.jsonl"

raw = []
with open(RAW, encoding='utf-8', errors='replace') as f:
    for line in f:
        if line.strip():
            raw.append(json.loads(line))

scored = []
with open(SCORED, encoding='utf-8', errors='replace') as f:
    for line in f:
        if line.strip():
            scored.append(json.loads(line))

print(f"Raw: {len(raw)} | Scored: {len(scored)}")

# The scorer preserves order — join by index
fixed = 0
for i, book in enumerate(scored):
    if i < len(raw):
        r = raw[i]
        if book.get('book_title', 'Unknown') == 'Unknown':
            book['book_title'] = r.get('title', 'Unknown')
            book['book_author'] = r.get('author', '')
            book['archive_url'] = r.get('archive_url', '')
            book['identifier']  = r.get('identifier', '')
            book['description'] = r.get('description', '')[:300]
            fixed += 1

print(f"Fixed {fixed} titles")

# Write patched scored file
with open(SCORED, 'w', encoding='utf-8') as f:
    for b in scored:
        f.write(json.dumps(b) + '\n')

# Export leads (composite >= 5.5)
leads = [b for b in scored if b.get('scores', {}).get('composite', 0) >= 5.5]
leads.sort(key=lambda x: x['scores']['composite'], reverse=True)
with open(LEADS, 'w', encoding='utf-8') as f:
    for b in leads:
        f.write(json.dumps(b) + '\n')

print(f"High signal leads (>=5.5): {len(leads)}")
print("\nTop 15:")
for b in leads[:15]:
    c = b['scores']['composite']
    g = b.get('salvage_grade','?')
    t = b.get('book_title','?')[:65]
    d = b.get('theory_domain','?')
    print(f"  [{c:.2f} {g}] [{d}] {t}")
