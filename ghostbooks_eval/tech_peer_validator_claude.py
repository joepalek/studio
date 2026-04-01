import json, os, requests
from datetime import datetime

# Load configs with BOM handling
with open(os.path.join('..', 'technical-peer-guides.json'), 'rb') as f:
    guides_config = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'adversary-test-packages.json'), 'rb') as f:
    packages_config = json.loads(f.read().decode('utf-8-sig'))

with open('ghost_outlines/linked_deep_outline.json', 'rb') as f:
    outline = json.loads(f.read().decode('utf-8-sig'))

# Load API key
KEY_FILE = os.path.join('anthropic_key.txt')
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

log_msg('=== TECHNICAL PEER REVIEW: LINKED OUTLINE ===')
log_msg(f'Item: {outline.get("book")}')
log_msg(f'Thesis: {outline.get("thesis")[:100]}...')
log_msg(f'Chapters: {len(outline.get("chapters", []))}')

guides_to_run = packages_config['packages']['complete_technical_stress_test']['guides']
log_msg(f'\nRunning {len(guides_to_run)} technical guides via Claude...')

reviews = []
for i, guide_name in enumerate(guides_to_run, 1):
    guide = guides_config['guides'][guide_name]
    log_msg(f'\n[{i}/{len(guides_to_run)}] {guide["name"]}...')
    
    system_prompt = f'You are a {guide["name"]} evaluating a ghostwritten book outline. Score 1-10 based on {", ".join(guide["evaluates_for"])}. Be specific and actionable.'
    
    user_prompt = f'''Evaluate this outline:

Title: {outline.get("book")}
Thesis: {outline.get("thesis")}

Chapters:
{chr(10).join([f'- Ch {ch.get("chapter")}: {ch.get("title")}' for ch in outline.get("chapters", [])])}

Score this 1-10 based on your expertise. Respond ONLY with:
SCORE: [1-10]
STRENGTHS: [2-3 bullets]
WEAKNESSES: [2-3 bullets]
FIX: [one specific suggestion]'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Response received')
        reviews.append({'guide': guide_name, 'name': guide['name'], 'response': response})
        # Extract score
        if 'SCORE:' in response:
            score_line = [l for l in response.split(chr(10)) if 'SCORE:' in l]
            if score_line:
                try:
                    score = int(score_line[0].split(':')[1].strip().split('/')[0])
                    log_msg(f'     Score: {score}/10')
                except: pass
    else:
        log_msg(f'  ✗ No response')

log_msg(f'\n=== PEER REVIEW COMPLETE ===')
log_msg(f'Reviews collected: {len(reviews)}/{len(guides_to_run)}')

# Save to peer-review-log.json
peer_log_path = os.path.join('..', 'peer-review-log.json')
with open(peer_log_path, 'r', encoding='utf-8') as f:
    peer_log = json.load(f)

review_entry = {
    'date': datetime.now().isoformat(),
    'item_id': 'linked_outline_ghostwriting',
    'item_type': 'thesis_outline',
    'scope': 'large',
    'package': 'complete_technical_stress_test',
    'reviews': reviews,
    'status': 'COMPLETE'
}

peer_log['entries'].append(review_entry)

with open(peer_log_path, 'w', encoding='utf-8') as f:
    json.dump(peer_log, f, indent=2)

log_msg(f'✓ Results saved to peer-review-log.json')
log_msg(f'\nNext: Review findings. Recommendation: APPROVE/REVISE/REJECT')
