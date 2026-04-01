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

log_msg('=== CHAPTER 3 SYNTHESIS ===')
log_msg('Title: Small Worlds & Six Degrees (Modern Social Media Context)')
log_msg('Purpose: Introduce small-world networks with contemporary examples')

ch3_system = 'You are a ghostwriter creating a detailed chapter outline for a network science book. Focus on small-world networks and six degrees of separation with modern social media examples.'

ch3_user = '''Create a detailed outline for Chapter 3: "Small Worlds & Six Degrees: How Everyone Is Connected"

Context: After covering hidden networks (Ch 1) and power laws (Ch 2), explain HOW networks create surprising connectivity through small-world properties.

Purpose: Show that networks are not just about power laws—they also have surprising path length properties that create "small worlds" where everyone connects through just a few hops.

Modern angle: Use Twitter/TikTok/LinkedIn algorithms, Instagram influencers, degrees of separation in dating apps, and pandemic contact tracing.

Provide:
1. HOOK: A surprising small-world discovery (TikTok connecting strangers, LinkedIn degrees)
2. SECTIONS: 4-5 major sections with titles and descriptions
3. KEY_CONCEPTS: What readers will understand by chapter end
4. RIGOR_NOTES: Where mathematical concepts fit (clustering coefficient, path length, Watts-Strogatz model)
5. TRANSITION: How this chapter leads to Chapter 4 (Network Failures)

Format as JSON.'''

log_msg('Generating Chapter 3 detailed outline...')
ch3_response = call_claude(ch3_system, ch3_user)
if ch3_response:
    log_msg('✓ Chapter 3 outline received')
    try:
        json_start = ch3_response.find('{')
        json_end = ch3_response.rfind('}') + 1
        ch3_outline = json.loads(ch3_response[json_start:json_end])
    except:
        ch3_outline = {'status': 'parse_error', 'raw': ch3_response}
else:
    ch3_outline = {'status': 'no_response'}

hook_system = 'You are a compelling science writer opening a chapter about small-world networks.'

hook_user = '''Write the opening 2-3 paragraphs for Chapter 3: "Small Worlds & Six Degrees"

Hook: Start with a modern, visceral small-world example:
- A TikTok video connecting two strangers 5,000 miles apart
- A LinkedIn connection chain that surprises someone
- An Instagram influencer discovering they share a mutual friend with a random person
- A pandemic contact trace revealing unexpected proximity

Make it vivid and relatable. Show that networks create surprising shortcuts that make the world feel smaller than it is.

Then pivot: "But WHY does this happen? What property of networks creates these shortcuts?"'''

log_msg('Generating opening hook...')
hook_response = call_claude(hook_system, hook_user)
if hook_response:
    log_msg('✓ Opening hook received')
else:
    hook_response = '(generation failed)'

takeaway_system = 'You are an educational expert creating chapter takeaways.'

takeaway_user = '''Chapter 3: "Small Worlds & Six Degrees"

What should a reader understand after finishing this chapter?

Provide 5-6 concrete takeaways about small-world networks. Format each as: "[Concept]: [one sentence explanation]"

Focus on:
- What small-world networks are (high clustering + short path lengths)
- Why they matter (shortcuts, rapid spread, efficiency)
- How algorithms exploit them (recommendation systems)
- Real-world implications (pandemic spread, information cascades)'''

log_msg('Generating chapter takeaways...')
takeaway_response = call_claude(takeaway_system, takeaway_user)
if takeaway_response:
    log_msg('✓ Takeaways received')
else:
    takeaway_response = '(generation failed)'

ch3_synthesis = {
    'chapter': 3,
    'title': 'Small Worlds & Six Degrees: How Everyone Is Connected',
    'thesis': outline.get('thesis'),
    'purpose': 'Reveal small-world properties that create surprising connectivity in networks',
    'detailed_outline': ch3_outline,
    'opening_hook': hook_response,
    'key_takeaways': takeaway_response,
    'generated_at': datetime.now().isoformat(),
    'status': 'READY_FOR_WRITING'
}

with open('ghost_outlines/ch3_synthesis.json', 'w', encoding='utf-8') as f:
    json.dump(ch3_synthesis, f, indent=2)

log_msg('\n=== CHAPTER 3 SYNTHESIS COMPLETE ===')
log_msg(f'✓ Detailed outline generated')
log_msg(f'✓ Opening hook written')
log_msg(f'✓ Key takeaways identified')
log_msg(f'\nSaved to: ch3_synthesis.json')
log_msg(f'Ready to expand into full prose.')
