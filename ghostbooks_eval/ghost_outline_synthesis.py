import json, os, requests
from datetime import datetime

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, 'ghost_outlines')
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEY_FILE = os.path.join(BASE_DIR, 'anthropic_key.txt')
ANTHROPIC_API_KEY = ''
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        raw = f.read()
        ANTHROPIC_API_KEY = raw.decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-opus-4-20250514'

TARGETS = [
    {'title': 'Linked: the new science of networks', 'domain': 'networks_emergence', 'score': 8.7, 'concepts': ['scale-free networks', 'network topology', 'degree distribution'], 'audience': 'Systems thinkers, organizational leaders'},
    {'title': 'Nonlinear Waves 1: Dynamics and Evolution', 'domain': 'systems_complexity', 'score': 8.4, 'concepts': ['nonlinear dynamics', 'wave propagation', 'emergence'], 'audience': 'Physics/engineering professionals'},
    {'title': 'Automata, Computability and Complexity: Theory and Applications', 'domain': 'information_computation', 'score': 8.1, 'concepts': ['computational models', 'automata theory', 'complexity classes'], 'audience': 'Computer scientists, AI practitioners'}
]

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_claude(system_prompt, user_prompt):
    if not ANTHROPIC_API_KEY: return None
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': MODEL, 'max_tokens': 2000, 'system': system_prompt, 'messages': [{'role': 'user', 'content': user_prompt}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, time
$code = @'
import json, os, requests
from datetime import datetime

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, 'ghost_outlines')
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEY_FILE = os.path.join(BASE_DIR, 'anthropic_key.txt')
ANTHROPIC_API_KEY = ''
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        raw = f.read()
        ANTHROPIC_API_KEY = raw.decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-opus-4-20250514'

TARGETS = [
    {'title': 'Linked: the new science of networks', 'domain': 'networks_emergence', 'score': 8.7, 'concepts': ['scale-free networks', 'network topology', 'degree distribution'], 'audience': 'Systems thinkers, organizational leaders'},
    {'title': 'Nonlinear Waves 1: Dynamics and Evolution', 'domain': 'systems_complexity', 'score': 8.4, 'concepts': ['nonlinear dynamics', 'wave propagation', 'emergence'], 'audience': 'Physics/engineering professionals'},
    {'title': 'Automata, Computability and Complexity: Theory and Applications', 'domain': 'information_computation', 'score': 8.1, 'concepts': ['computational models', 'automata theory', 'complexity classes'], 'audience': 'Computer scientists, AI practitioners'}
]

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_claude(system_prompt, user_prompt):
    if not ANTHROPIC_API_KEY: return None
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': MODEL, 'max_tokens': 2000, 'system': system_prompt, 'messages': [{'role': 'user', 'content': user_prompt}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content and content[0].get('type') == 'text': return content[0].get('text', '')
        else:
            log_msg(f'API error: {resp.status_code}')
    except Exception as e:
        log_msg(f'Exception: {e}')
    return None

def gen_thesis(book):
    system = 'You are a scholarly ghostwriter. Create a 2-3 sentence thesis statement that captures the core generative insight. Be original and defensible.'
    user = f'Book: {book["title"]}\nDomain: {book["domain"]}\nConcepts: {", ".join(book["concepts"])}\nAudience: {book["audience"]}\n\nGenerate a compelling thesis statement.'
    return call_claude(system, user)

def gen_chapters(book, thesis):
    system = 'Generate exactly 6 chapters with titles and 2-3 sentence descriptions. Format: JSON array [{"chapter": 1, "title": "...", "description": "..."}, ...]. Only JSON, no preamble.'
    user = f'Source: {book["title"]}\nThesis: {thesis}\nAudience: {book["audience"]}\n\nCreate 6-chapter outline. Return ONLY JSON.'
    response = call_claude(system, user)
    if response:
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start: return json.loads(response[json_start:json_end])
        except: pass
    return []

def gen_concept_map(book, thesis, chapters):
    system = 'Create a Mermaid flowchart (graph TD) showing concept dependencies. 8-10 nodes max. Only mermaid code, no explanation.'
    chapter_titles = ' → '.join([ch.get('title', '') for ch in chapters])
    user = f'Book: {book["title"]}\nThesis: {thesis}\nChapters: {chapter_titles}\n\nCreate Mermaid flowchart of concept dependencies.'
    return call_claude(system, user)

def gen_expansion(book, thesis):
    system = 'Identify 3-4 expansion vectors for this thesis beyond source domain. Format: plain text bullets (- prefix).'
    user = f'Book: {book["title"]}\nThesis: {thesis}\n\nWhat 3-4 novel angles extend this thesis?'
    return call_claude(system, user)

def synthesize(book):
    log_msg(f'\nSYNTHESIZING: {book["title"][:50]}')
    log_msg('  Generating thesis...')
    thesis = gen_thesis(book)
    if not thesis: return None
    log_msg(f'  ✓ Thesis OK')
    log_msg('  Generating chapters...')
    chapters = gen_chapters(book, thesis)
    if not chapters: return None
    log_msg(f'  ✓ {len(chapters)} chapters OK')
    log_msg('  Generating concept map...')
    concept_map = gen_concept_map(book, thesis, chapters) or '(map generation failed)'
    log_msg('  Generating expansion angles...')
    expansion = gen_expansion(book, thesis) or '(expansion generation failed)'
    outline = {'book_source': book['title'], 'domain': book['domain'], 'score': book['score'], 'thesis': thesis, 'chapters': chapters, 'concept_map': concept_map, 'expansion': expansion, 'generated_at': datetime.now().isoformat()}
    return outline

def save(outline, idx):
    if not outline: return
    slug = outline['book_source'].lower().replace(' ', '_')[:30]
    json_path = os.path.join(OUTPUT_DIR, f'{idx}_{slug}_outline.json')
    with open(json_path, 'w', encoding='utf-8') as f: json.dump(outline, f, indent=2)
    log_msg(f'  Saved: {json_path}')

log_msg('=== GHOST BOOK OUTLINE SYNTHESIS ===')
log_msg(f'Model: {MODEL}')
log_msg(f'Output: {OUTPUT_DIR}')
outlines = []
for i, book in enumerate(TARGETS, 1):
    outline = synthesize(book)
    if outline:
        outlines.append(outline)
        save(outline, i)
log_msg(f'\n✓ Complete: {len(outlines)}/{len(TARGETS)} outlines generated')
