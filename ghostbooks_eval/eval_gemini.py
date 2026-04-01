import json, os, requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.getcwd()
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_raw.jsonl')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_scored.jsonl')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'evaluate_gemini.log')

with open(os.path.join(BASE_DIR, 'config', 'theory_domains.json')) as f: THEORY_DOMAINS = json.load(f)
with open(os.path.join(BASE_DIR, 'config', 'scoring_rubric.json')) as f: SCORING_RUBRIC = json.load(f)
with open(os.path.join(BASE_DIR, 'config', 'character_prompts.json')) as f: CHARACTERS = json.load(f)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
MAX_WORKERS = 3

def log_msg(msg):
    ts = datetime.now().isoformat()
    entry = f'[{ts}] {msg}'
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def get_domain_experts(domain):
    if domain not in THEORY_DOMAINS: return list(CHARACTERS.keys())[:2]
    experts = THEORY_DOMAINS[domain].get('experts', [])
    return experts[:2] if experts else list(CHARACTERS.keys())[:2]

def call_gemini(prompt):
    if not GEMINI_API_KEY: return None
    try:
        url = f'{GEMINI_URL}?key={GEMINI_API_KEY}'
        payload = {'contents': [{'parts': [{'text': prompt}]}]}
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts: return parts[0].get('text', '').strip()
    except: pass
    return None

def evaluate_with_character(book_record, character_name, domain):
    character = CHARACTERS.get(character_name, {})
    system_prompt = character.get('system_prompt', '')
    expertise = character.get('expertise', '')
    book_title = book_record.get('title', 'Unknown')
    book_author = book_record.get('author', 'Unknown')
    book_year = book_record.get('year', 'Unknown')
    description = book_record.get('description', '')[:300]
    user_prompt = f'You are {character_name}. {expertise}\n\nBook: {book_title}\nAuthor: {book_author}\nYear: {book_year}\nDescription: {description}\n\nRate 1-10: t_score, d_score, g_score, a_score, m_score, s_score. Respond ONLY with JSON: {{"t_score": <1-10>, "d_score": <1-10>, "g_score": <1-10>, "a_score": <1-10>, "m_score": <1-10>, "s_score": <1-10>}}'
    full_prompt = f'{system_prompt}\n\n{user_prompt}'
    response = call_gemini(full_prompt)
    if response:
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                scores = json.loads(json_str)
                return scores
        except: pass
    return {'t_score': 5, 'd_score': 5, 'g_score': 5, 'a_score': 5, 'm_score': 5, 's_score': 5}

def evaluate_book(book):
    domain = book.get('theory_domain', '')
    experts = get_domain_experts(domain)
    all_scores = {}
    for expert in experts:
        all_scores[expert] = evaluate_with_character(book, expert, domain)
    aggregate = {k: sum(all_scores[e].get(k, 5) for e in experts) / len(experts) for k in ['t_score', 'd_score', 'g_score', 'a_score', 'm_score', 's_score']}
    for k in aggregate: aggregate[k] = round(aggregate[k], 1)
    w = sum(SCORING_RUBRIC[k]['weight'] for k in aggregate)
    composite = round(sum(aggregate[k] * SCORING_RUBRIC[k]['weight'] for k in aggregate) / w, 2) if w > 0 else 0
    aggregate['composite'] = composite
    grade = 'A' if composite > 7.5 else 'B' if composite > 6.5 else 'C'
    return {'book_title': book.get('title', 'Unknown'), 'book_year': book.get('year', ''), 'theory_domain': domain, 'scores': aggregate, 'salvage_grade': grade, 'evaluation_date': datetime.now().isoformat()}

def load_books():
    books = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): books.append(json.loads(line))
    return books

log_msg('Loading books...')
books = load_books()
log_msg(f'Loaded {len(books)} books')
log_msg('Starting evaluation with Gemini 2.5 Flash...')
scored_books = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(evaluate_book, book): (i, book) for i, book in enumerate(books)}
    for future in as_completed(futures):
        i, book = futures[future]
        try:
            scored = future.result()
            scored_books.append(scored)
            log_msg(f'[{i+1}/{len(books)}] {book.get("title", "Unknown")[:40]} -> {scored.get("scores", {}).get("composite", 0):.1f} {scored.get("salvage_grade")}')
        except Exception as e:
            log_msg(f'ERROR [{i}]: {e}')

log_msg(f'Writing {len(scored_books)} books to {OUTPUT_FILE}...')
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for book in scored_books:
        f.write(json.dumps(book) + '\n')
log_msg('Done!')
