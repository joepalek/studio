import json, os, requests
from datetime import datetime

# Load Ch 1 scaffold (has outline, hook, takeaways)
with open('ghost_outlines/ch1_synthesis.json', 'rb') as f:
    ch1_scaffold = json.loads(f.read().decode('utf-8-sig'))

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

log_msg('=== REGENERATING CHAPTER 1 FULL PROSE ===')
log_msg('Rebuilding 5 sections from scaffold')

sections = ch1_scaffold['detailed_outline']['sections']
expanded_sections = []

for sec in sections:
    section_num = sec['number']
    section_title = sec['title']
    section_desc = sec['description']
    
    log_msg(f'\n[Section {section_num}] {section_title}...')
    
    system_prompt = 'You are a compelling science writer creating a section for a network science book. Write with clarity, vivid examples, and engagement. Target: 800-1200 words per section.'
    
    user_prompt = f'''Write a complete, publication-ready section for a network science book.

Section Title: {section_title}
Section Purpose: {section_desc}

Requirements:
1. Open with a compelling hook or question
2. Use 2-3 vivid, concrete examples throughout
3. Explain concepts in accessible language
4. End with transition sentence to next section
5. Target length: 800-1200 words
6. Tone: Engaging, accessible, rigorous

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
intro_user = f'''Write the introduction to Chapter 1: "The Hidden Architecture of Everything"

Opening Hook (reference):
{ch1_scaffold.get('opening_hook', '')[:500]}...

Create a 300-400 word introduction that:
1. Opens with a vivid example (ski chalet/virus, power outage, or social spread)
2. Poses the central question
3. Promises what readers will understand
4. Transitions to Section 1

Write now:'''

intro_response = call_claude(intro_system, intro_user)
if intro_response:
    log_msg('  ✓ Introduction complete')
else:
    log_msg('  ✗ Introduction failed')

log_msg('\n[Conclusion] Chapter wrap-up...')
conclusion_system = 'You are writing a chapter conclusion. Make it 250-350 words, synthesize key ideas.'
conclusion_user = '''Write the conclusion to Chapter 1: "The Hidden Architecture of Everything"

Key concepts to synthesize:
- Networks are hidden yet everywhere
- Universal patterns repeat across domains
- Position matters more than attributes
- Networks create both efficiency and vulnerability
- Readers now have a "network lens"

Transition: Next chapter explores how scientists discovered these principles

Write 250-350 words:'''

conclusion_response = call_claude(conclusion_system, conclusion_user)
if conclusion_response:
    log_msg('  ✓ Conclusion complete')
else:
    log_msg('  ✗ Conclusion failed')

ch1_full = {
    'chapter': 1,
    'title': 'The Hidden Architecture of Everything',
    'introduction': intro_response or '(failed)',
    'sections': expanded_sections,
    'conclusion': conclusion_response or '(failed)',
    'status': 'FULL_PROSE_REGENERATED',
    'generated_at': datetime.now().isoformat(),
    'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in expanded_sections]) + (len(intro_response.split()) if intro_response else 0) + (len(conclusion_response.split()) if conclusion_response else 0)
}

with open('ghost_outlines/ch1_FULL_PROSE.json', 'w', encoding='utf-8') as f:
    json.dump(ch1_full, f, indent=2)

log_msg(f'\n=== CHAPTER 1 REGENERATION COMPLETE ===')
log_msg(f'Status: {ch1_full["status"]}')
log_msg(f'Est. word count: {ch1_full["word_count_estimate"]:,} words')
log_msg(f'Sections: {len(expanded_sections)}/5 complete')
log_msg(f'Saved to: ch1_FULL_PROSE.json (overwritten)')
