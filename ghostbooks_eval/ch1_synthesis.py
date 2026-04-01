import json, os, requests
from datetime import datetime

# Load outline and API key
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

log_msg('=== CHAPTER 1 SYNTHESIS ===')
log_msg('Title: The Hidden Architecture of Everything')
log_msg('Purpose: Establish the hidden patterns in complex systems')

# Generate Chapter 1 detailed outline
ch1_system = 'You are a ghostwriter creating a detailed chapter outline for a network science book. Focus on engagement, clarity, and establishing the foundational mystery.'

ch1_user = '''Create a detailed outline for Chapter 1: "The Hidden Architecture of Everything"

Purpose: Introduce readers to the idea that seemingly different systems (social networks, biological networks, internet, organizations) share hidden organizing principles.

Provide:
1. HOOK: Opening story/example that captures attention
2. SECTIONS: 4-5 major sections with titles and 2-3 sentence descriptions
3. KEY_CONCEPTS: What readers will understand by chapter end
4. TRANSITION: How this chapter leads to Chapter 2

Format as JSON.'''

log_msg('Generating Chapter 1 detailed outline...')
ch1_response = call_claude(ch1_system, ch1_user)
if ch1_response:
    log_msg('✓ Chapter 1 outline received')
    try:
        json_start = ch1_response.find('{')
        json_end = ch1_response.rfind('}') + 1
        ch1_outline = json.loads(ch1_response[json_start:json_end])
    except:
        ch1_outline = {'status': 'parse_error', 'raw': ch1_response}
else:
    ch1_outline = {'status': 'no_response'}

# Generate opening paragraph (hook)
hook_system = 'You are a compelling science writer. Write a 2-3 paragraph opening that hooks the reader with a concrete example.'

hook_user = '''Write the opening 2-3 paragraphs for Chapter 1 of a network science book.

Setting: A reader who doesn't know anything about network science yet.
Goal: Show them that the networks they encounter every day—social, biological, digital—follow hidden patterns.

Example to use: Start with something concrete (a disease outbreak, social media spread, a company's organizational structure) and hint that it shares rules with seemingly unrelated systems.

Make it vivid, concrete, and create curiosity about what those hidden rules are.'''

log_msg('Generating opening hook...')
hook_response = call_claude(hook_system, hook_user)
if hook_response:
    log_msg('✓ Opening paragraph received')
else:
    hook_response = '(hook generation failed)'

# Generate key takeaways
takeaway_system = 'You are an educational expert. Create 5-6 key takeaways that readers should have at chapter end.'

takeaway_user = '''Chapter 1: "The Hidden Architecture of Everything"

What should a reader understand after finishing this chapter?

Provide 5-6 concrete takeaways. Format each as: "[Concept]: [one sentence explanation]"'''

log_msg('Generating chapter takeaways...')
takeaway_response = call_claude(takeaway_system, takeaway_user)
if takeaway_response:
    log_msg('✓ Takeaways received')
else:
    takeaway_response = '(takeaways generation failed)'

# Compile Chapter 1 synthesis
ch1_synthesis = {
    'chapter': 1,
    'title': 'The Hidden Architecture of Everything',
    'thesis': outline.get('thesis'),
    'purpose': 'Establish the existence of hidden patterns in seemingly different systems',
    'detailed_outline': ch1_outline,
    'opening_hook': hook_response,
    'key_takeaways': takeaway_response,
    'generated_at': datetime.now().isoformat(),
    'status': 'READY_FOR_WRITING'
}

# Save Chapter 1 synthesis
with open('ghost_outlines/ch1_synthesis.json', 'w', encoding='utf-8') as f:
    json.dump(ch1_synthesis, f, indent=2)

log_msg('\n=== CHAPTER 1 SYNTHESIS COMPLETE ===')
log_msg(f'✓ Detailed outline generated')
log_msg(f'✓ Opening hook written')
log_msg(f'✓ Key takeaways identified')
log_msg(f'\nSaved to: ch1_synthesis.json')
log_msg(f'\nReady to begin full Chapter 1 content synthesis.')
log_msg(f'Next: Expand sections into full prose.')
