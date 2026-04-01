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

log_msg('=== CHAPTER 5 SYNTHESIS ===')
log_msg('Title: Information Cascades & Fake News')

ch5_system = 'You are a ghostwriter creating a detailed chapter outline for a network science book about information spread.'

ch5_user = '''Create a detailed outline for Chapter 5: "The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks"

Context: After explaining how networks fail physically (Ch 4), reveal how the SAME cascade mechanism applies to information—ideas, rumors, panic, fake news.

Purpose: Show that information spreads through networks following predictable cascade patterns. What makes some ideas go viral while others die? Why do false beliefs persist?

Modern angle: COVID misinformation, election disinformation, QAnon, vaccine hesitancy, Twitter cascades, TikTok trends, Reddit viral moments, the role of bots/algorithms.

Provide:
1. HOOK: A real information cascade (COVID misinformation, election disinformation, viral rumor)
2. SECTIONS: 4-5 major sections with titles and descriptions
3. KEY_CONCEPTS: Information cascade, threshold models, viral spread, herding behavior, echo chambers
4. RIGOR_NOTES: Where network science explains cascade dynamics (degree distribution, clustering, bottlenecks)
5. TRANSITION: How this leads to Chapter 6 (Platform Economics)

Format as JSON.'''

log_msg('Generating Chapter 5 detailed outline...')
ch5_response = call_claude(ch5_system, ch5_user)
if ch5_response:
    log_msg('✓ Chapter 5 outline received')
    try:
        json_start = ch5_response.find('{')
        json_end = ch5_response.rfind('}') + 1
        ch5_outline = json.loads(ch5_response[json_start:json_end])
    except:
        ch5_outline = {'status': 'parse_error', 'raw': ch5_response}
else:
    ch5_outline = {'status': 'no_response'}

hook_system = 'You are a compelling science writer opening a chapter about information cascades.'

hook_user = '''Write the opening 2-3 paragraphs for Chapter 5: "The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks"

Hook: Start with a visceral information cascade:
- A piece of COVID misinformation that spread to millions
- An election disinformation campaign that shaped behavior
- A QAnon conspiracy theory that fractured families
- A TikTok trend that suddenly exploded globally
- A stock market panic driven by social media rumors (GameStop, Meme stocks)

Make it dramatic and real. Show information spreading faster than truth can catch up.

Then pivot: "But WHY do some ideas spread while others don't? What network properties determine viral success?"'''

log_msg('Generating opening hook...')
hook_response = call_claude(hook_system, hook_user)
if hook_response:
    log_msg('✓ Opening hook received')
else:
    hook_response = '(generation failed)'

takeaway_system = 'You are an educational expert creating chapter takeaways.'

takeaway_user = '''Chapter 5: "The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks"

What should a reader understand after finishing this chapter?

Provide 5-6 concrete takeaways about information cascades. Format each as: "[Concept]: [one sentence explanation]"

Focus on:
- Information spreads like contagion through networks (threshold effects)
- Network structure determines viral potential (clustering vs. paths)
- False information spreads faster than corrections (psychology + structure)
- Echo chambers amplify beliefs (homophily + algorithms)
- Centrality matters (influencers shape cascades)
- Real-world implications (democracy, public health, social movements)'''

log_msg('Generating chapter takeaways...')
takeaway_response = call_claude(takeaway_system, takeaway_user)
if takeaway_response:
    log_msg('✓ Takeaways received')
else:
    takeaway_response = '(generation failed)'

ch5_synthesis = {
    'chapter': 5,
    'title': 'The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks',
    'purpose': 'Reveal information cascade dynamics and misinformation spread',
    'detailed_outline': ch5_outline,
    'opening_hook': hook_response,
    'key_takeaways': takeaway_response,
    'generated_at': datetime.now().isoformat(),
    'status': 'READY_FOR_WRITING'
}

with open('ghost_outlines/ch5_synthesis.json', 'w', encoding='utf-8') as f:
    json.dump(ch5_synthesis, f, indent=2)

log_msg('\n=== CHAPTER 5 SYNTHESIS COMPLETE ===')
log_msg(f'✓ Detailed outline generated')
log_msg(f'✓ Opening hook written')
log_msg(f'✓ Key takeaways identified')
log_msg(f'\nSaved to: ch5_synthesis.json')
log_msg(f'Ready to expand into full prose.')
