import json, os, requests
from datetime import datetime

with open('ghost_outlines/ch1_FULL_PROSE.json', 'rb') as f:
    ch1 = json.loads(f.read().decode('utf-8-sig'))

with open('ghost_outlines/ch2_FULL_PROSE.json', 'rb') as f:
    ch2 = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'technical-peer-guides.json'), 'rb') as f:
    guides_config = json.loads(f.read().decode('utf-8-sig'))

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

def extract_chapter_text(ch):
    parts = []
    if ch.get('introduction'):
        parts.append(ch['introduction'])
    for sec in ch.get('sections', []):
        if sec.get('content'):
            parts.append(f"\n{sec['title']}\n{sec['content']}")
    if ch.get('conclusion'):
        parts.append(ch['conclusion'])
    return '\n'.join(parts)

ch1_text = extract_chapter_text(ch1)
ch2_text = extract_chapter_text(ch2)

log_msg('=== PEER REVIEW: CHAPTERS 1 & 2 (FULL TEXT) ===')
log_msg(f'Ch 1 text: {len(ch1_text)} chars')
log_msg(f'Ch 2 text: {len(ch2_text)} chars')

guides_to_run = ['network_theory_expert', 'mathematical_rigor_reviewer', 'systems_thinking_validator', 'practical_application_auditor', 'clarity_and_accessibility_checker', 'copyeditor_and_style']

log_msg(f'\nRunning {len(guides_to_run)} guides...')

reviews = []
scores = []

for i, guide_name in enumerate(guides_to_run, 1):
    guide = guides_config['guides'].get(guide_name)
    if not guide:
        continue
    
    log_msg(f'\n[{i}/{len(guides_to_run)}] {guide["name"]}...')
    
    system_prompt = f'You are a {guide["name"]}. Evaluate both chapters.'
    
    user_prompt = f'''Evaluate these two chapters of a network science book.

CHAPTER 1: The Hidden Architecture of Everything
{ch1_text[:3000]}...

CHAPTER 2: The Power Law Revolution
{ch2_text[:3000]}...

Score each 1-10. Respond ONLY with:

CHAPTER 1 SCORE: [1-10]
CHAPTER 2 SCORE: [1-10]
COHERENCE: [yes/no]
VOICE: [yes/no]
READY: [yes/no]
FEEDBACK: [1-2 sentences]'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Response received')
        reviews.append({'guide': guide['name'], 'response': response})
        
        for line in response.split('\n'):
            if 'SCORE:' in line:
                try:
                    score_str = line.split(':')[1].strip().split('/')[0]
                    score = int(score_str)
                    scores.append(score)
                except:
                    pass
    else:
        log_msg(f'  ✗ No response')

if scores:
    avg = round(sum(scores) / len(scores), 1)
    log_msg(f'\n=== RESULTS ===')
    log_msg(f'Average Score: {avg}/10')
    log_msg(f'Reviews Collected: {len(scores)} scores from {len(reviews)} guides')
    
    if avg >= 7.5:
        log_msg(f'\nAPPROVAL: Chapters 1 & 2 Ready')
    elif avg >= 6.5:
        log_msg(f'\nCONDITIONAL: Review feedback')
    else:
        log_msg(f'\nNEEDS REVISION')
    
    log_msg(f'\n=== DETAILED FEEDBACK ===')
    for review in reviews:
        log_msg(f'\n[{review["guide"]}]')
        log_msg(review['response'])
else:
    log_msg('No scores parsed. Raw feedback:')
    for review in reviews:
        log_msg(f'\n[{review["guide"]}]')
        log_msg(review['response'])
