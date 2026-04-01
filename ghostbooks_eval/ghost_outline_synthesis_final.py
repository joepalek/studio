import json, os, requests
from datetime import datetime

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, 'ghost_outlines')
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEY_FILE = os.path.join(BASE_DIR, 'anthropic_key.txt')
ANTHROPIC_API_KEY = ''
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        ANTHROPIC_API_KEY = f.read().decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-opus-4-20250514'

TARGETS = [
    {'title': 'Linked: the new science of networks', 'domain': 'networks_emergence', 'score': 8.7},
    {'title': 'Nonlinear Waves 1: Dynamics and Evolution', 'domain': 'systems_complexity', 'score': 8.4},
    {'title': 'Automata, Computability and Complexity: Theory and Applications', 'domain': 'information_computation', 'score': 8.1}
]

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_claude(system, user):
    if not ANTHROPIC_API_KEY: return None
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': MODEL, 'max_tokens': 2000, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content: return content[0].get('text', '')
    except: pass
    return None

log_msg('=== GHOST BOOK OUTLINE SYNTHESIS ===')
outlines = []
for i, book in enumerate(TARGETS, 1):
    log_msg(f"Synthesizing {i}/3: {book['title'][:40]}")
    thesis = call_claude('Create a 2-3 sentence thesis statement.', f"Book: {book['title']}")
    if thesis:
        log_msg(f"✓ Thesis OK")
        outline = {'book': book['title'], 'domain': book['domain'], 'score': book['score'], 'thesis': thesis}
        outlines.append(outline)
        slug = book['title'].lower().replace(' ', '_').replace(':', '').replace(',', '')[:30]
        out_path = os.path.join(OUTPUT_DIR, f'{i}_{slug}_outline.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, indent=2)
        log_msg(f"  Saved: {out_path}")

log_msg(f'✓ Complete: {len(outlines)}/{len(TARGETS)} outlines saved')
