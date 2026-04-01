import json, os, requests
from datetime import datetime

with open('ghost_outlines/linked_deep_outline_REVISED.json', 'rb') as f:
    outline = json.loads(f.read().decode('utf-8-sig'))

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

log_msg('=== CHAPTER 2 SYNTHESIS ===')
log_msg('Title: The Power Law Revolution')
log_msg('Purpose: Reveal the mathematical patterns underlying network structures')

ch2_system = 'You are a ghostwriter creating a detailed chapter outline for a network science book. Focus on explaining power laws as the revolutionary insight that changed how we understand complex systems.'

ch2_user = '''Create a detailed outline for Chapter 2: "The Power Law Revolution"

Context: Chapter 1 revealed hidden networks everywhere. Chapter 2 explains THE discovery that made network science a discipline: power laws.

Purpose: Show why power laws matter, how they differ from normal distributions, and why finding power laws in networks shocked scientists.

Provide:
1. HOOK: A surprising real-world example of power law distribution
2. SECTIONS: 4-5 major sections with titles and 2-3 sentence descriptions
3. KEY_CONCEPTS: What readers will understand by chapter end
4. TRANSITION: How this chapter leads to Chapter 3 (Preferential Attachment)

Format as JSON.'''

log_msg('Generating Chapter 2 detailed outline...')
ch2_response = call_claude(ch2_system, ch2_user)
if ch2_response:
    log_msg('✓ Chapter 2 outline received')
    try:
        json_start = ch2_response.find('{')
        json_end = ch2_response.rfind('}') + 1
        ch2_outline = json.loads(ch2_response[json_start:json_end])
    except:
        ch2_outline = {'status': 'parse_error', 'raw': ch2_response}
else:
    ch2_outline = {'status': 'no_response'}

hook_system = 'You are a compelling science writer. Write a 2-3 paragraph opening that hooks readers with a power law example.'

hook_user = '''Write the opening 2-3 paragraphs for Chapter 2: "The Power Law Revolution"

Setting: Reader just learned networks are everywhere (from Ch 1). Now reveal the revolutionary pattern they all share.

Hook idea: Start with something concrete where power laws matter:
- eBay auction prices (most cheap, few extremely expensive)
- YouTube views (most videos get few views, few go viral)
- Twitter followers (most have few followers, few have millions)
- City sizes (most small, few megacities)
- Earthquake magnitudes (many small, few massive)

Pick one and make it vivid. Show how this distribution is NOT what we'd expect (not normal/bell curve). Create curiosity about WHY.'''

log_msg('Generating opening hook...')
hook_response = call_claude(hook_system, hook_user)
if hook_response:
    log_msg('✓ Opening hook received')
else:
    hook_response = '(generation failed)'

takeaway_system = 'You are an educational expert. Create key takeaways for understanding power laws and their significance.'

takeaway_user = '''Chapter 2: "The Power Law Revolution"

What should a reader understand after finishing this chapter?

Provide 5-6 concrete takeaways. Format each as: "[Concept]: [one sentence explanation]"

Focus on:
- What power laws are
- Why they're different from normal distributions
- Why they appear in networks
- Why this was revolutionary
- What this enables us to predict/understand'''

log_msg('Generating chapter takeaways...')
takeaway_response = call_claude(takeaway_system, takeaway_user)
if takeaway_response:
    log_msg('✓ Takeaways received')
else:
    takeaway_response = '(generation failed)'

ch2_synthesis = {
    'chapter': 2,
    'title': 'The Power Law Revolution',
    'thesis': outline.get('thesis'),
    'purpose': 'Reveal power laws as the mathematical pattern underlying network structures',
    'detailed_outline': ch2_outline,
    'opening_hook': hook_response,
    'key_takeaways': takeaway_response,
    'generated_at': datetime.now().isoformat(),
    'status': 'READY_FOR_WRITING'
}

with open('ghost_outlines/ch2_synthesis.json', 'w', encoding='utf-8') as f:
    json.dump(ch2_synthesis, f, indent=2)

log_msg('\n=== CHAPTER 2 SYNTHESIS COMPLETE ===')
log_msg(f'✓ Detailed outline generated')
log_msg(f'✓ Opening hook written')
log_msg(f'✓ Key takeaways identified')
log_msg(f'\nSaved to: ch2_synthesis.json')
log_msg(f'Ready to expand into full prose.')
