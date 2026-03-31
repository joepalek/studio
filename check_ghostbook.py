import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("G:/My Drive/Projects/_studio/ghostbooks_eval/data/books_scored.jsonl",
          encoding='utf-8', errors='replace') as f:
    lines = [json.loads(l) for l in f if l.strip()]

composites = [b['scores']['composite'] for b in lines if 'scores' in b]
real = [c for c in composites if c != 6.02]
print(f"Total scored: {len(lines)}")
print(f"Records with real (non-mock) scores: {len(real)}")
if real:
    print(f"Real score range: {min(real):.2f} - {max(real):.2f}")
    print(f"Real avg: {sum(real)/len(real):.2f}")
    grades = {}
    for b in lines:
        if b['scores']['composite'] != 6.02:
            g = b.get('salvage_grade','?')
            grades[g] = grades.get(g,0)+1
    print("Grade dist (real):", grades)
    print("\nTop 10 real scores:")
    top = sorted([b for b in lines if b['scores']['composite'] != 6.02],
                 key=lambda x: x['scores']['composite'], reverse=True)[:10]
    for b in top:
        print(f"  [{b['scores']['composite']:.2f} {b.get('salvage_grade','?')}] {b.get('book_title','?')[:65]}")
else:
    print("All records still have mock score 6.02 — eval_gemini.py output not in this file")
    print("Check if eval is still running or if it wrote to a different file")
