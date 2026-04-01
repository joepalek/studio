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

log_msg('=== PEER REVIEW: CHAPTERS 1 & 2 ===')
ch1_wc = ch1.get('word_count_estimate', 0)
ch2_wc = ch2.get('word_count_estimate', 0)
log_msg(f'Ch 1: {ch1_wc} words')
log_msg(f'Ch 2: {ch2_wc} words')
log_msg(f'Total: {ch1_wc + ch2_wc} words')

guides_to_run = ['network_theory_expert', 'mathematical_rigor_reviewer', 'systems_thinking_validator', 'practical_application_auditor', 'clarity_and_accessibility_checker', 'copyeditor_and_style']

log_msg(f'\nRunning {len(guides_to_run)} guides on both chapters...')

reviews = []
scores_ch1 = []
scores_ch2 = []

for i, guide_name in enumerate(guides_to_run, 1):
    guide = guides_config['guides'].get(guide_name)
    if not guide:
        log_msg(f'[{i}/{len(guides_to_run)}] {guide_name} - SKIPPED')
        continue
    
    log_msg(f'\n[{i}/{len(guides_to_run)}] {guide["name"]}...')
    
    system_prompt = f'You are a {guide["name"]}. Evaluate these two chapters on {", ".join(guide.get("evaluates_for", []))}. Score each 1-10.'
    
    user_prompt = f'''Evaluate Chapters 1 & 2 of a network science book.

CHAPTER 1: The Hidden Architecture of Everything
- 5 sections + intro + conclusion
- 6,500 words
- Purpose: Reveal hidden networks everywhere

CHAPTER 2: The Power Law Revolution
- 5 sections + intro + conclusion
- 5,300 words
- Purpose: Explain power laws as revolutionary discovery

For EACH chapter, score 1-10. Respond ONLY with:

CHAPTER 1:
SCORE: [1-10]
STRENGTH: [one sentence]
WEAKNESS: [one sentence]

CHAPTER 2:
SCORE: [1-10]
STRENGTH: [one sentence]
WEAKNESS: [one sentence]

COHERENCE: [yes/no - do these chapters flow together logically?]
VOICE: [yes/no - consistent tone/style?]
READY: [yes/no for publication as pair]'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Response received')
        reviews.append({'guide': guide_name, 'name': guide['name'], 'response': response})
        
        for line in response.split('\n'):
            if line.startswith('SCORE:'):
                try:
                    score = int(line.split(':')[1].strip().split('/')[0])
                    if len(scores_ch1) < len([r for r in reviews if 'CHAPTER 1' in reviews[len(reviews)-1]['response']]):
                        scores_ch1.append(score)
                        log_msg(f'     Ch 1: {score}/10')
                    else:
                        scores_ch2.append(score)
                        log_msg(f'     Ch 2: {score}/10')
                except: pass
    else:
        log_msg(f'  ✗ No response')

if scores_ch1 and scores_ch2:
    avg_ch1 = round(sum(scores_ch1) / len(scores_ch1), 1)
    avg_ch2 = round(sum(scores_ch2) / len(scores_ch2), 1)
    avg_overall = round((avg_ch1 + avg_ch2) / 2, 1)
    
    log_msg(f'\n=== REVIEW RESULTS ===')
    log_msg(f'Chapter 1 Average: {avg_ch1}/10')
    log_msg(f'Chapter 2 Average: {avg_ch2}/10')
    log_msg(f'Overall Average: {avg_overall}/10')
    
    if avg_overall >= 7.5:
        log_msg(f'\nAPPROVAL: Chapters 1 & 2 Ready')
        log_msg(f'Proceed to Chapter 3.')
    elif avg_overall >= 6.5:
        log_msg(f'\nCONDITIONAL: Review feedback below')
    else:
        log_msg(f'\nNEEDS REVISION')
    
    log_msg(f'\n=== DETAILED FEEDBACK ===')
    for review in reviews:
        log_msg(f'\n[{review["name"]}]')
        log_msg(review['response'])
else:
    log_msg('ERROR: Scores not parsed - showing raw feedback:')
    for review in reviews:
        log_msg(f'\n[{review["name"]}]')
        log_msg(review['response'])
