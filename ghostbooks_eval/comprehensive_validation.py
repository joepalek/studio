import json, os, requests
from datetime import datetime

with open('ghost_outlines/linked_deep_outline_REVISED.json', 'rb') as f:
    outline = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'technical-peer-guides.json'), 'rb') as f:
    guides_config = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'adversary-test-packages.json'), 'rb') as f:
    packages_config = json.loads(f.read().decode('utf-8-sig'))

KEY_FILE = 'anthropic_key.txt'
ANTHROPIC_API_KEY = ''
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        ANTHROPIC_API_KEY = f.read().decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-opus-4-20250514'

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_claude(system, user):
    if not ANTHROPIC_API_KEY: return None
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': MODEL, 'max_tokens': 1800, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content: return content[0].get('text', '')
    except: pass
    return None

log_msg('=== COMPREHENSIVE PEER REVIEW: REVISED OUTLINE WITH COPYEDITOR ===')
log_msg(f'Item: {outline.get("book")} (8 chapters)')
log_msg(f'Chapters: {len(outline.get("chapters", []))}')
log_msg(f'Thesis: {outline.get("thesis")[:100]}...')

guides_to_run = packages_config['packages']['complete_technical_stress_test']['guides']
log_msg(f'\nRunning {len(guides_to_run)} technical guides with full evaluation...')

reviews = []
scores = []
for i, guide_name in enumerate(guides_to_run, 1):
    guide = guides_config['guides'].get(guide_name)
    if not guide:
        log_msg(f'[{i}/{len(guides_to_run)}] {guide_name} - SKIPPED')
        continue
    
    log_msg(f'\n[{i}/{len(guides_to_run)}] {guide["name"]}...')
    
    system_prompt = f'You are a {guide["name"]} evaluating a ghostwritten book outline. Score 1-10 based on {", ".join(guide.get("evaluates_for", []))}. Be specific and constructive.'
    
    chapters_list = '\n'.join([f'- Ch {ch.get("chapter")}: {ch.get("title")}' for ch in outline.get("chapters", [])])
    
    user_prompt = f'''Evaluate this REVISED outline (8 chapters, addressing peer feedback):

Title: {outline.get("book")}

Chapters:
{chapters_list}

Thesis: {outline.get("thesis")}

Score 1-10. Respond ONLY with:
SCORE: [1-10]
STRENGTHS: [2-3 bullets]
WEAKNESSES: [2-3 bullets, if any]
FIX: [one specific suggestion if needed]
READY: [yes/no for ghostwriting]'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Full response received')
        reviews.append({'guide': guide_name, 'name': guide['name'], 'response': response})
        if 'SCORE:' in response:
            score_line = [l for l in response.split('\n') if 'SCORE:' in l]
            if score_line:
                try:
                    score = int(score_line[0].split(':')[1].strip().split('/')[0])
                    scores.append(score)
                    log_msg(f'     Score: {score}/10')
                except: pass
    else:
        log_msg(f'  ✗ No response')

if scores:
    avg = round(sum(scores) / len(scores), 1)
    log_msg(f'\n=== FINAL COMPREHENSIVE RESULT ===')
    log_msg(f'Average Score: {avg}/10')
    log_msg(f'Reviews: {len(reviews)}/{len(guides_to_run)} guides')
    
    if avg >= 7.5:
        log_msg(f'\n✓✓✓ FINAL APPROVAL FOR GHOSTWRITING ✓✓✓')
        log_msg(f'Outline validated across all dimensions.')
        log_msg(f'Ready to begin Chapter 1 synthesis.')
    elif avg >= 6.5:
        log_msg(f'\n⚠ CONDITIONAL APPROVAL - Review feedback below')
    else:
        log_msg(f'\n✗ NEEDS REVISION - Address issues below')
    
    log_msg(f'\n=== DETAILED FEEDBACK ===')
    for review in reviews:
        log_msg(f'\n[{review["name"]}]')
        log_msg(review['response'])
else:
    log_msg('ERROR: No scores collected')
