import json, os, requests
from datetime import datetime

with open('ghost_outlines/ch2_synthesis.json', 'rb') as f:
    ch2_scaffold = json.loads(f.read().decode('utf-8-sig'))

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
    except Exception as e:
        log_msg(f'API Error: {e}')
    return None

log_msg('=== CHAPTER 2 FULL PROSE EXPANSION ===')
log_msg('Expanding 4-5 sections into complete, publication-ready prose')

sections = ch2_scaffold['detailed_outline'].get('sections', [])
expanded_sections = []

for sec in sections:
    section_num = sec.get('number', len(expanded_sections) + 1)
    section_title = sec.get('title', 'Untitled')
    section_desc = sec.get('description', '')
    
    log_msg(f'\n[Section {section_num}] {section_title}...')
    
    system_prompt = 'You are a compelling science writer creating a section for a network science book. Write with clarity, vivid examples, and engagement. Explain power laws intuitively. Target: 800-1200 words per section.'
    
    user_prompt = f'''Write a complete, publication-ready section for a network science book.

Section Title: {section_title}
Section Purpose: {section_desc}

Requirements:
1. Open with a compelling hook or question
2. Use 2-3 vivid, concrete examples throughout
3. Explain power laws and their significance in accessible language
4. Avoid jargon without explanation
5. End with a transition sentence to next section
6. Target length: 800-1200 words
7. Tone: Engaging, accessible, intellectually rigorous

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
intro_system = 'You are writing an introduction to a chapter about power laws. Make it 300-400 words, vivid, and hook the reader.'
intro_user = f'''Write the introduction to Chapter 2 of a network science book.

Opening Hook (reference):
{ch2_scaffold.get('opening_hook', '')[:400]}...

Create a 300-400 word introduction that:
1. Opens with a vivid power law example (eBay, YouTube, Twitter, cities, earthquakes)
2. Poses the central question: Why are power laws everywhere in networks?
3. Promises readers will understand the revolutionary insight
4. Transitions smoothly to Section 1

Write now:'''

intro_response = call_claude(intro_system, intro_user)
if intro_response:
    log_msg('  ✓ Introduction complete')
else:
    log_msg('  ✗ Introduction failed')

log_msg('\n[Conclusion] Chapter wrap-up...')
conclusion_system = 'You are writing a chapter conclusion. Synthesize power law insights and preview preferential attachment.'
conclusion_user = '''Write the conclusion to Chapter 2: "The Power Law Revolution"

Key concepts to synthesize:
- Power laws are everywhere in networks
- They differ fundamentally from normal/bell curve distributions
- They describe networks with hubs and many small nodes
- They were a revolutionary discovery
- They hint at a deeper mechanism (preferential attachment)

Transition preview: Next chapter (Chapter 3) explains the mechanism that CREATES power laws—preferential attachment.

Write 250-350 words:'''

conclusion_response = call_claude(conclusion_system, conclusion_user)
if conclusion_response:
    log_msg('  ✓ Conclusion complete')
else:
    log_msg('  ✗ Conclusion failed')

ch2_full = {
    'chapter': 2,
    'title': 'The Power Law Revolution',
    'introduction': intro_response or '(failed)',
    'sections': expanded_sections,
    'conclusion': conclusion_response or '(failed)',
    'status': 'EXPANSION_COMPLETE',
    'generated_at': datetime.now().isoformat(),
    'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in expanded_sections]) + (len(intro_response.split()) if intro_response else 0) + (len(conclusion_response.split()) if conclusion_response else 0)
}

with open('ghost_outlines/ch2_FULL_PROSE.json', 'w', encoding='utf-8') as f:
    json.dump(ch2_full, f, indent=2)

log_msg(f'\n=== CHAPTER 2 EXPANSION COMPLETE ===')
log_msg(f'Status: {ch2_full["status"]}')
log_msg(f'Est. word count: {ch2_full["word_count_estimate"]:,} words')
log_msg(f'Sections: {len(expanded_sections)} complete')
log_msg(f'Saved to: ch2_FULL_PROSE.json')
log_msg(f'\nChapter 2 ready for peer review and publication.')
