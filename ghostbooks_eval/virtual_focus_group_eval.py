import json, os, requests
from datetime import datetime

with open('ghost_outlines/ch1_FULL_PROSE.json', 'rb') as f:
    ch1 = json.loads(f.read().decode('utf-8-sig'))

with open('ghost_outlines/ch2_FULL_PROSE.json', 'rb') as f:
    ch2 = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'technical-peer-guides.json'), 'rb') as f:
    guides_config = json.loads(f.read().decode('utf-8-sig'))

with open(os.path.join('..', 'focus_group_contacts_research.json'), 'rb') as f:
    contacts = json.loads(f.read().decode('utf-8-sig'))

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
        payload = {'model': MODEL, 'max_tokens': 2000, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
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

log_msg('=== VIRTUAL FOCUS GROUP EVALUATION ===')
log_msg('Simulating expert review personas')
log_msg(f'Ch 1: {len(ch1_text)} chars')
log_msg(f'Ch 2: {len(ch2_text)} chars')

# Define virtual focus group personas
personas = {
    'PUBLISHER': {
        'name': 'Publisher (Network Science / Trade)',
        'role': 'Market positioning, audience fit, comp titles, sales viability',
        'prompt': '''You are an acquisitions editor at a major science publisher (Princeton/Penguin/Basic Books). 
        
Evaluate these 2 chapters of "Linked: The New Science of Networks" for publication viability.

Key questions:
1. Who is the reader for this book?
2. Is this marketable? (Compare to Barabási's "Linked", Gladwell's "Tipping Point", Pinker's work)
3. What's the unique angle vs. existing network science books?
4. Would you acquire this? Why or why not?
5. What direction should the author take Chapters 3-8?

Respond with VERDICT (ACQUIRE / CONDITIONAL / PASS) and brief reasoning.'''
    },
    
    'COPYEDITOR_NARRATIVE': {
        'name': 'Copyeditor (Trade/Narrative)',
        'role': 'Prose clarity, pacing, accessibility for general readers',
        'prompt': '''You are a copyeditor specializing in popular science and narrative nonfiction.

Evaluate these 2 chapters for prose quality, readability, and accessibility.

Key questions:
1. Is the writing clear for a general educated reader?
2. Are technical concepts explained accessibly?
3. Does the narrative flow work? Any choppy transitions?
4. What's the reading level? (high school / college / graduate)
5. What needs tightening or expansion?

Respond with PROSE_SCORE (1-10) and 2-3 specific suggestions.'''
    },
    
    'COMPARABLE_AUTHOR': {
        'name': 'Comparable Author (Network Science)',
        'role': 'How this compares to existing network science books',
        'prompt': '''You are the author of network science books (like Barabási, Watts, Newman).

Evaluate how "Linked" compares to existing network science literature.

Key questions:
1. How does this differ from my books ("Linked", "Six Degrees", etc)?
2. Is there a unique angle or gap this fills?
3. What's missing that readers would expect?
4. Is the depth right for the intended audience?
5. Would I recommend this to students/professionals?

Respond with COMP_VERDICT (UNIQUE / DERIVATIVE / FILLS_GAP / NEEDS_WORK) and why.'''
    },
    
    'SOURCE_VALIDATOR': {
        'name': 'Source Validator (Network Scientist)',
        'role': 'Factual accuracy, mathematical rigor, validation gaps',
        'prompt': '''You are a network science researcher/academic (physics, computer science, complexity).

Evaluate factual accuracy, rigor, and mathematical foundation.

Key questions:
1. Are the network concepts presented accurately?
2. What rigor is missing? (definitions, proofs, equations)
3. Are there factual errors or oversimplifications?
4. Would this satisfy a student or professional seeking rigor?
5. What's needed to make this academically credible?

Respond with RIGOR_SCORE (1-10), ACCURACY_SCORE (1-10), and gap analysis.'''
    }
}

reviews = []

for role_key, persona in personas.items():
    log_msg(f'\n[{persona["name"]}]...')
    
    system_prompt = f'You are a {persona["name"]}. {persona["role"]}'
    
    user_prompt = f'''{persona['prompt']}

CHAPTERS (Ch 1 & 2 excerpts):
{ch1_text[:3000]}...
---
{ch2_text[:3000]}...'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Response received')
        reviews.append({
            'persona': persona['name'],
            'role_key': role_key,
            'response': response
        })
    else:
        log_msg(f'  ✗ No response')

# Compile results
with open('virtual_focus_group_results.json', 'w', encoding='utf-8') as f:
    json.dump({
        'evaluation_type': 'VIRTUAL_FOCUS_GROUP',
        'date': datetime.now().isoformat(),
        'chapters_evaluated': 2,
        'word_count': len(ch1_text) + len(ch2_text),
        'personas_count': len(reviews),
        'reviews': reviews
    }, f, indent=2)

log_msg(f'\n=== VIRTUAL FOCUS GROUP COMPLETE ===')
log_msg(f'Personas evaluated: {len(reviews)}/4')
log_msg(f'Results saved: virtual_focus_group_results.json')
log_msg(f'\nFocus group verdict forthcoming...')
