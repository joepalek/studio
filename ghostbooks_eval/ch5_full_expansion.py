import json, os, requests
from datetime import datetime

with open('ghost_outlines/ch5_synthesis.json', 'rb') as f:
    ch5_scaffold = json.loads(f.read().decode('utf-8-sig'))

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
        payload = {'model': MODEL, 'max_tokens': 3000, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content: return content[0].get('text', '')
    except: pass
    return None

log_msg('=== CHAPTER 5 FULL PROSE EXPANSION ===')

sections = ch5_scaffold['detailed_outline'].get('sections', [])
expanded_sections = []

for sec in sections:
    section_num = sec.get('number', len(expanded_sections) + 1)
    section_title = sec.get('title', 'Untitled')
    section_desc = sec.get('description', '')
    
    log_msg(f'[Section {section_num}] {section_title}...')
    
    system_prompt = 'You are a compelling science writer. Write with clarity, vivid examples, and engagement. Target: 800-1200 words per section. Include real misinformation examples, keep narrative strong.'
    
    user_prompt = f'''Write a complete, publication-ready section for a network science book about information cascades.

Section Title: {section_title}
Section Purpose: {section_desc}

Requirements:
1. Open with a compelling hook or question
2. Use 2-3 vivid, concrete examples (prefer real misinformation cascades: COVID, elections, conspiracy theories)
3. Explain cascade/information spread concepts in accessible language
4. End with transition to next section
5. Target length: 800-1200 words
6. Tone: Engaging, accessible, intellectually rigorous

Write the full section now:'''
    
    response = call_claude(system_prompt, user_prompt)
    if response:
        log_msg(f'  ✓ Section {section_num} complete ({len(response)} chars)')
        expanded_sections.append({
            'number': section_num,
            'title': section_title,
            'content': response
        })
    else:
        log_msg(f'  ✗ Section {section_num} failed')

log_msg('\n[Introduction] Opening hook expansion...')
intro_system = 'You are writing a chapter introduction. Make it 300-400 words, vivid, and hook the reader.'
intro_user = f'''Write the introduction to Chapter 5: "The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks"

Opening Hook (reference):
{ch5_scaffold.get('opening_hook', '')[:400]}...

Create a 300-400 word introduction that:
1. Opens with an information cascade (misinformation, viral panic, conspiracy theory)
2. Poses the central question: Why do false beliefs spread faster than truth?
3. Promises readers will understand cascade dynamics
4. Transitions to Section 1

Write now:'''

intro_response = call_claude(intro_system, intro_user)
if intro_response:
    log_msg('  ✓ Introduction complete')
else:
    log_msg('  ✗ Introduction failed')

log_msg('\n[Conclusion] Chapter wrap-up...')
conclusion_system = 'You are writing a chapter conclusion. Synthesize and preview platform economics.'
conclusion_user = '''Write the conclusion to Chapter 5: "The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks"

Key concepts to synthesize:
- Information cascades follow network structure (like physical cascades)
- False information spreads faster than corrections (structural + psychological reasons)
- Network centrality determines cascade reach (influencers, bots, algorithms)
- Echo chambers amplify and insulate beliefs
- Platform design choices shape information spread
- This has real consequences (democracy, public health, social cohesion)

Transition preview: Next chapter explores how platforms profit from cascades—and why they design networks to maximize engagement (even if it spreads misinformation).

Write 250-350 words:'''

conclusion_response = call_claude(conclusion_system, conclusion_user)
if conclusion_response:
    log_msg('  ✓ Conclusion complete')
else:
    log_msg('  ✗ Conclusion failed')

ch5_full = {
    'chapter': 5,
    'title': 'The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks',
    'introduction': intro_response or '(failed)',
    'sections': expanded_sections,
    'conclusion': conclusion_response or '(failed)',
    'status': 'EXPANSION_COMPLETE',
    'generated_at': datetime.now().isoformat(),
    'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in expanded_sections]) + (len(intro_response.split()) if intro_response else 0) + (len(conclusion_response.split()) if conclusion_response else 0)
}

with open('ghost_outlines/ch5_FULL_PROSE.json', 'w', encoding='utf-8') as f:
    json.dump(ch5_full, f, indent=2)

log_msg(f'\n=== CHAPTER 5 EXPANSION COMPLETE ===')
log_msg(f'Est. word count: {ch5_full["word_count_estimate"]:,} words')
log_msg(f'Sections: {len(expanded_sections)} complete')
log_msg(f'Saved to: ch5_FULL_PROSE.json')
log_msg(f'\nTotal manuscript so far:')
log_msg(f'  Ch 1: ~5,400 words')
log_msg(f'  Ch 2: ~5,300 words')
log_msg(f'  Ch 3: ~5,521 words')
log_msg(f'  Ch 4: ~4,091 words')
log_msg(f'  Ch 5: ~{ch5_full["word_count_estimate"]:,} words')
log_msg(f'  TOTAL: ~{5400 + 5300 + 5521 + 4091 + ch5_full["word_count_estimate"]:,} words')
log_msg(f'\nRemaining: Ch 6, 7, 8')
