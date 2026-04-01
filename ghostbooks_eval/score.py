import json, os
BASE_DIR = os.getcwd()
books = []
with open(os.path.join(BASE_DIR, 'data', 'books_raw.jsonl')) as f:
    for line in f:
        if line.strip():
            books.append(json.loads(line))
print(f'Loaded {len(books)} books')
SCORING = json.load(open(os.path.join(BASE_DIR, 'config', 'scoring_rubric.json')))
scored = []
for book in books:
    try:
        year_str = book.get('year', '2000') or '2000'
        year = int(year_str)
    except:
        year = 2000
    age = 2024 - year
    scores = {'t_score': max(5, 10 - age/10), 'd_score': max(4, 8 - age/8), 'g_score': 6.5, 'a_score': 6.0, 'm_score': 5.5, 's_score': 5.0}
    w = sum(SCORING[k]['weight'] for k in scores)
    comp = sum(scores[k] * SCORING[k]['weight'] for k in scores) / w
    scored.append({'book_title': book.get('title'), 'book_year': book.get('year'), 'theory_domain': book.get('theory_domain'), 'scores': {k: round(v, 1) for k, v in scores.items()} | {'composite': round(comp, 2)}, 'salvage_grade': 'A' if comp > 7.5 else 'B' if comp > 6.5 else 'C'})
with open(os.path.join(BASE_DIR, 'data', 'books_scored.jsonl'), 'w') as f:
    for s in scored:
        f.write(json.dumps(s) + '\n')
print(f'Wrote {len(scored)} scored books')
for s in scored[:5]:
    print(f"  {s['book_title'][:50]:50} {s['scores']['composite']:4.1f} {s['salvage_grade']}")
