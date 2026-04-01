import json, os, requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.getcwd()
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_raw.jsonl')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_scored.jsonl')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'evaluate_gemini.log')

with open(os.path.join(BASE_DIR, 'config', 'scoring_rubric.json')) as f:
    SCORING_RUBRIC = json.load(f)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
MAX_WORKERS = 3

def log_msg(msg):
    ts = datetime.now().isoformat()
    entry = f'[{ts}] {msg}'
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

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
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts: return parts[0].get('text', '')
    except Exception as e:
        pass
    return None

def evaluate_book(book):
    title = book.get('title', 'Unknown')
    desc = book.get('description', '')[:150]
    prompt = f'Rate this book 1-10 on theoretical soundness, temporal drift, data groundability, advancement potential, market value, content saturation.\nTitle: {title}\nDescription: {desc}\n\nRespond ONLY with JSON: {{"t_score": 1-10, "d_score": 1-10, "g_score": 1-10, "a_score": 1-10, "m_score": 1-10, "s_score": 1-10}}'
    
    response = call_gemini(prompt)
    if response:
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                scores = json.loads(response[json_start:json_end])
                for k in ['t_score', 'd_score', 'g_score', 'a_score', 'm_score', 's_score']:
                    if k not in scores: scores[k] = 5
                return scores
        except:
            pass
    return {'t_score': 5, 'd_score': 5, 'g_score': 5, 'a_score': 5, 'm_score': 5, 's_score': 5}

def run():
    log_msg('Loading books...')
    books = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip(): books.append(json.loads(line))
    log_msg(f'Loaded {len(books)} books. Evaluating...')
    
    scored = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(evaluate_book, book): (i, book) for i, book in enumerate(books)}
        for future in as_completed(futures):
            i, book = futures[future]
            try:
                scores = future.result()
                w = sum(SCORING_RUBRIC[k]['weight'] for k in scores)
                comp = round(sum(scores[k] * SCORING_RUBRIC[k]['weight'] for k in scores) / w, 2)
                scores['composite'] = comp
                grade = 'A' if comp > 7.5 else 'B' if comp > 6.5 else 'C'
                scored.append({'book_title': book.get('title'), 'book_year': book.get('year'), 'theory_domain': book.get('theory_domain'), 'scores': scores, 'salvage_grade': grade, 'evaluation_date': datetime.now().isoformat()})
                log_msg(f'[{i+1}/{len(books)}] {book.get("title")[:40]} -> {comp} {grade}')
            except Exception as e:
                log_msg(f'ERROR [{i}]: {e}')
    
    log_msg(f'Writing {len(scored)} books...')
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for s in scored: f.write(json.dumps(s) + '\n')
    log_msg('Done!')

run()
