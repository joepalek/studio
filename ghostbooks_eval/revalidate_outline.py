import json, os, requests
from datetime import datetime

# Load revised outline
with open('ghost_outlines/linked_deep_outline_REVISED.json', 'rb') as f:
    outline = json.loads(f.read().decode('utf-8-sig'))

# Load configs
with open(os.path.join('..', 'technical-peer-guides.json'), 'rb') as f:
    guides_config = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'adversary-test-packages.json'), 'rb') as f:
    packages_config = json.loads(f.read().decode('utf-8-sig'))

# Load API key
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
        payload = {'model': MODEL, 'max_tokens': 1500, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content: return content[0].get('text', '')
    except: pass
    return None

log_msg('=== PEER REVIEW RE-VALIDATION: REVISED LINKED OUTLINE ===')
log_msg(f'Chapters: {len(outline.get("chapters", []))} (was 6, now 8)')
log_msg(f'Thesis now addresses: limitations, domain variations, robustness, failure')

guides_to_run = packages_config['packages']['complete_technical_stress_test']['guides']
log_msg(f'\nRunning {len(guides_to_run)} technical guides...')

reviews = []
scores = []
for i, guide_name in enumerate(guides_to_run, 1):
    guide = guides_config['guides'][guide_name]
    log_msg(f'[{i}/{len(guides_to_run)}] {guide["name"]}...')
    
    system_prompt = f'You are a {guide["name"]} evaluating a REVISED ghostwritten book outline. This version addresses previous weaknesses. Score 1-10 based on {", ".join(guide["evaluates_for"])}.'
    
    user_prompt = f'''Evaluate this REVISED outline (now 8 chapters):

Title: {outline.get("book")}
Thesis: {outline.get("thesis")}

NEW Chapters (addressing peer feedback):
- Ch 5: Beyond Scale-Free - Small Worlds, Robustness, and Limits
- Ch 6: Network Failures and Transformations - Collapse, Phase Transitions, Domain Limits

Score 1-10. Did the revisions address previous weaknesses? Respond ONLY with:
SCORE: [1-10]
IMPROVED: [yes/no and why]
REMAINING_ISSUES: [if any]
READY: [yes/no for ghostwriting]'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Response received')
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

# Calculate aggregate
if scores:
    avg = round(sum(scores) / len(scores), 1)
    log_msg(f'\n=== RE-VALIDATION RESULT ===')
    log_msg(f'Average Score: {avg}/10')
    log_msg(f'Reviews: {len(reviews)}/{len(guides_to_run)}')
    
    if avg >= 7.5:
        log_msg(f'\n✓✓✓ RECOMMENDATION: APPROVE FOR GHOSTWRITING ✓✓✓')
        log_msg(f'Outline is ready. Proceed to Chapter 1 synthesis.')
    elif avg >= 6.5:
        log_msg(f'\n⚠ RECOMMENDATION: CONDITIONALLY APPROVE')
        log_msg(f'Review feedback below before starting.')
    else:
        log_msg(f'\n✗ RECOMMENDATION: NEEDS MORE REVISION')
        log_msg(f'Address remaining issues before writing.')
    
    log_msg(f'\n=== DETAILED FEEDBACK ===')
    for review in reviews:
        log_msg(f'\n[{review["name"]}]')
        log_msg(review['response'])
else:
    log_msg('ERROR: No scores collected')
