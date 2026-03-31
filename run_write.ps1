$env:PYTHONIOENCODING = "utf-8"
Set-Location "G:\My Drive\Projects\_studio"
python -c "
import json
with open('ghostbooks_eval/data/books_raw.jsonl', encoding='utf-8', errors='replace') as f:
    lines = [json.loads(l) for l in f if l.strip()]
print(f'Total raw records: {len(lines)}')
print('Sample titles:')
for b in lines[:5]:
    print(f'  [{b.get(chr(116)+chr(104)+chr(101)+chr(111)+chr(114)+chr(121)+chr(95)+chr(100)+chr(111)+chr(109)+chr(97)+chr(105)+chr(110),\"?\")}] {b.get(\"title\",\"?\")[:70]}')
domains = {}
for b in lines:
    d = b.get(\"theory_domain\",\"unknown\")
    domains[d] = domains.get(d,0)+1
print(\"By domain:\", domains)
has_desc = sum(1 for b in lines if b.get('description'))
print(f'Records with description: {has_desc}/{len(lines)}')
"
