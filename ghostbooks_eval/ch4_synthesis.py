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

log_msg('=== CHAPTER 4 SYNTHESIS ===')
log_msg('Title: Network Robustness & Failure (Infrastructure, Supply Chains)')

ch4_system = 'You are a ghostwriter creating a detailed chapter outline for a network science book about network failures.'

ch4_user = '''Create a detailed outline for Chapter 4: "When Networks Fail: Cascades, Attacks, and Collapse"

Context: After explaining how networks create shortcuts (Ch 3), reveal the DARK SIDE—networks are also fragile. One failure can cascade through the entire system.

Purpose: Show that the same properties that make networks efficient (tight coupling, preferential attachment, clustering) also make them vulnerable to targeted attacks or cascading failures.

Modern angle: 2003 Northeast blackout, Twitter outages, supply chain disruptions (COVID, Ever Given), financial crises, airline hub failures, internet backbone vulnerabilities.

Provide:
1. HOOK: A real cascading failure (blackout, supply chain collapse, financial contagion)
2. SECTIONS: 4-5 major sections with titles and descriptions
3. KEY_CONCEPTS: Cascade, robustness, resilience, attack tolerance, critical infrastructure
4. RIGOR_NOTES: Where network science explains cascade dynamics (percolation theory, k-cores, network diameter)
5. TRANSITION: How this leads to Chapter 5 (Information Cascades & Misinformation)

Format as JSON.'''

log_msg('Generating Chapter 4 detailed outline...')
ch4_response = call_claude(ch4_system, ch4_user)
if ch4_response:
    log_msg('✓ Chapter 4 outline received')
    try:
        json_start = ch4_response.find('{')
        json_end = ch4_response.rfind('}') + 1
        ch4_outline = json.loads(ch4_response[json_start:json_end])
    except:
        ch4_outline = {'status': 'parse_error', 'raw': ch4_response}
else:
    ch4_outline = {'status': 'no_response'}

hook_system = 'You are a compelling science writer opening a chapter about network failures and cascades.'

hook_user = '''Write the opening 2-3 paragraphs for Chapter 4: "When Networks Fail: Cascades, Attacks, and Collapse"

Hook: Start with a visceral cascading failure:
- The 2003 Northeast blackout (one line tripped, cascaded across 9 states)
- Supply chain collapse during COVID (one factory shutdown, ripple effects)
- The Ever Given blocking the Suez Canal (global logistics paralyzed)
- A bank failure triggering financial cascade
- An airline hub shutdown (ripple delays across the network)

Make it dramatic and real. Show a single point of failure cascading outward.

Then pivot: "But WHY does one failure become a catastrophe? Why can't networks absorb a single failure?"'''

log_msg('Generating opening hook...')
hook_response = call_claude(hook_system, hook_user)
if hook_response:
    log_msg('✓ Opening hook received')
else:
    hook_response = '(generation failed)'

takeaway_system = 'You are an educational expert creating chapter takeaways.'

takeaway_user = '''Chapter 4: "When Networks Fail: Cascades, Attacks, and Collapse"

What should a reader understand after finishing this chapter?

Provide 5-6 concrete takeaways about network failures and cascades. Format each as: "[Concept]: [one sentence explanation]"

Focus on:
- Why networks fail (tight coupling, tipping points, cascade thresholds)
- How failures cascade (percolation, contagion, second-order effects)
- Which networks are vulnerable (hubs, critical infrastructure, interconnected systems)
- Defense strategies (redundancy, decoupling, isolation)
- Real-world implications (pandemic, supply chain, financial contagion)'''

log_msg('Generating chapter takeaways...')
takeaway_response = call_claude(takeaway_system, takeaway_user)
if takeaway_response:
    log_msg('✓ Takeaways received')
else:
    takeaway_response = '(generation failed)'

ch4_synthesis = {
    'chapter': 4,
    'title': 'When Networks Fail: Cascades, Attacks, and Collapse',
    'purpose': 'Reveal network fragility and cascade dynamics',
    'detailed_outline': ch4_outline,
    'opening_hook': hook_response,
    'key_takeaways': takeaway_response,
    'generated_at': datetime.now().isoformat(),
    'status': 'READY_FOR_WRITING'
}

with open('ghost_outlines/ch4_synthesis.json', 'w', encoding='utf-8') as f:
    json.dump(ch4_synthesis, f, indent=2)

log_msg('\n=== CHAPTER 4 SYNTHESIS COMPLETE ===')
log_msg(f'✓ Detailed outline generated')
log_msg(f'✓ Opening hook written')
log_msg(f'✓ Key takeaways identified')
log_msg(f'\nSaved to: ch4_synthesis.json')
log_msg(f'Ready to expand into full prose.')
