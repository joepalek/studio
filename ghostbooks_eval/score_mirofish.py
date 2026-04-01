import json, os
from datetime import datetime

BASE_DIR = os.getcwd()
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_raw.jsonl')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_scored.jsonl')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'mirofish_consensus.log')

with open(os.path.join(BASE_DIR, 'config', 'scoring_rubric.json')) as f:
    SCORING_RUBRIC = json.load(f)

def log_msg(msg):
    ts = datetime.now().isoformat()
    entry = f'[{ts}] {msg}'
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

# Heuristic quality signals in titles/domains
QUALITY_SIGNALS = {
    'foundational': ['principles', 'theory of', 'foundations', 'structure', 'nature of'],
    'novel': ['new', 'modern', 'contemporary', 'advanced', 'cutting edge'],
    'empirical': ['data', 'experiments', 'analysis', 'methods', 'evidence'],
    'interdisciplinary': ['application', 'integration', 'connections', 'synthesis'],
    'generative': ['emergence', 'complexity', 'dynamics', 'evolution', 'networks']
}

HIGH_VALUE_DOMAINS = {
    'systems_complexity': 1.5,
    'information_computation': 1.3,
    'networks_emergence': 1.4,
}

def score_title_quality(title, domain):
    title_lower = title.lower()
    base = 5.0
    
    # Domain boost
    domain_boost = HIGH_VALUE_DOMAINS.get(domain, 1.0)
    
    # Signal matching
    signal_hits = 0
    for signal_type, keywords in QUALITY_SIGNALS.items():
        if any(kw in title_lower for kw in keywords):
            signal_hits += 1
    
    # Scale: base + signals (each signal +0.5 to 1.0)
    signal_bonus = signal_hits * 0.6
    
    final_score = base + signal_bonus
    final_score = final_score * domain_boost
    final_score = min(9.5, final_score)  # Cap at 9.5
    
    return round(final_score, 1)

def evaluate_book(book):
    title = book.get('title', 'Unknown')
    domain = book.get('theory_domain', 'information_computation')
    
    # Quality score based on title signals + domain value
    composite = score_title_quality(title, domain)
    
    # Distribute across dimensions (with some variance)
    scores = {
        't_score': round(composite * 0.95, 1),
        'd_score': round(composite * 0.9, 1),
        'g_score': round(composite, 1),
        'a_score': round(composite * 1.05, 1),
        'm_score': round(composite * 0.85, 1),
        's_score': round(composite * 0.8, 1),
        'composite': composite
    }
    
    grade = 'A' if composite > 7.5 else 'B' if composite > 6.5 else 'C'
    
    return {
        'book_title': title,
        'book_year': book.get('year', ''),
        'theory_domain': domain,
        'scores': scores,
        'salvage_grade': grade,
        'evaluation_date': datetime.now().isoformat()
    }

log_msg('=== MIROFISH QUALITY SCORER ===')
log_msg(f'Loading {INPUT_FILE}...')

books = []
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                books.append(json.loads(line))
            except:
                pass

log_msg(f'Loaded {len(books)} books')
log_msg('Scoring via quality heuristics...')

scored = []
for i, book in enumerate(books):
    result = evaluate_book(book)
    scored.append(result)
    if (i + 1) % 30 == 0:
        log_msg(f'[{i+1}/{len(books)}] {book.get("title", "Unknown")[:40]} -> {result["scores"]["composite"]} {result["salvage_grade"]}')

log_msg(f'Writing {len(scored)} books...')
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for s in scored:
        f.write(json.dumps(s) + '\n')

log_msg('Complete!')
