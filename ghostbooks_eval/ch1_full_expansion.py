import json, os, requests
from datetime import datetime

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

log_msg('=== CHAPTER 1 FULL PROSE EXPANSION ===')
log_msg('Expanding 5 sections into complete, publication-ready prose')

sections = ch1_scaffold['detailed_outline']['sections']
expanded_sections = []

for sec in sections:
    section_num = sec['number']
    section_title = sec['title']
    section_desc = sec['description']
    
    log_msg(f'\n[Section {section_num}] {section_title}...')
    
    system_prompt = 'You are a compelling science writer creating a section for a network science book. Write with clarity, vivid examples, and engagement. Avoid jargon without explanation. Target: 800-1200 words per section.'
    
    user_prompt = f'''Write a complete, publication-ready section for a network science book.

Section Title: {section_title}
Section Purpose: {section_desc}

Requirements:
1. Open with a compelling hook or question
2. Use 2-3 vivid, concrete examples throughout
3. Explain complex concepts in accessible language
4. End with a transition sentence to next section
5. Target length: 800-1200 words
6. Tone: Engaging, accessible to general readers, but intellectually rigorous

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

# Generate introduction (before Section 1)
log_msg('\n[Introduction] Opening hook expansion...')
intro_system = 'You are writing an introduction to a chapter. Make it 300-400 words, vivid, and hook the reader immediately.'
intro_user = f'''Write the introduction to Chapter 1 of a network science book.

Opening Hook (use this as reference):
{ch1_scaffold['opening_hook'][:500]}...

Create a 300-400 word introduction that:
1. Opens with the ski chalet/virus story or similar vivid example
2. Poses the central question of the chapter
3. Promises what readers will understand by chapter end
4. Transitions smoothly to Section 1

Write now:'''

intro_response = call_claude(intro_system, intro_user)
if intro_response:
    log_msg('  ✓ Introduction complete')
else:
    log_msg('  ✗ Introduction failed')

# Generate conclusion (after Section 5)
log_msg('\n[Conclusion] Chapter wrap-up...')
conclusion_system = 'You are writing a chapter conclusion. Make it 250-350 words, synthesize key ideas, and preview the next chapter.'
conclusion_user = f'''Write the conclusion to Chapter 1: "The Hidden Architecture of Everything"

Key takeaways to reference:
- Networks are hidden yet everywhere
- Universal patterns repeat across domains
- Position matters more than attributes
- Networks create both efficiency and vulnerability
- Readers now have a \"network lens\"

Transition preview: Next chapter explores how scientists discovered these principles

Write 250-350 words:'''

conclusion_response = call_claude(conclusion_system, conclusion_user)
if conclusion_response:
    log_msg('  ✓ Conclusion complete')
else:
    log_msg('  ✗ Conclusion failed')

# Compile full Chapter 1
ch1_full = {{
    'chapter': 1,
    'title': 'The Hidden Architecture of Everything',
    'introduction': intro_response or '(failed)',
    'sections': expanded_sections,
    'conclusion': conclusion_response or '(failed)',
    'status': 'EXPANSION_COMPLETE',
    'generated_at': datetime.now().isoformat(),
    'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in expanded_sections]) + (len(intro_response.split()) if intro_response else 0) + (len(conclusion_response.split()) if conclusion_response else 0)
}}

# Save
with open('ghost_outlines/ch1_FULL_PROSE.json', 'w', encoding='utf-8') as f:
    json.dump(ch1_full, f, indent=2)

log_msg(f'\n=== CHAPTER 1 EXPANSION COMPLETE ===')
log_msg(f'Status: {ch1_full["status"]}')
log_msg(f'Est. word count: {ch1_full["word_count_estimate"]:,} words')
log_msg(f'Sections: {len(expanded_sections)}/5 complete')
log_msg(f'Saved to: ch1_FULL_PROSE.json')
log_msg(f'\nChapter 1 is ready for final review and publication.')
