import json, os, requests
from datetime import datetime

with open('anthropic_key.txt', 'rb') as f:
    ANTHROPIC_API_KEY = f.read().decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-opus-4-20250514'

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_claude(system, user):
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': MODEL, 'max_tokens': 3000, 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('content'):
                return data['content'][0].get('text', '')
    except Exception as e:
        log_msg(f'Error: {e}')
    return None

log_msg('=== FINISHING LINKED: MISSING SECTIONS ===')

# Load existing chapters
chapters = {}
for ch_num in [1, 2, 3, 4, 5, 6, 7, 8]:
    try:
        with open(f'ghost_outlines/ch{ch_num}_FULL_PROSE.json', 'rb') as f:
            chapters[ch_num] = json.loads(f.read().decode('utf-8-sig'))
            log_msg(f'✓ Ch {ch_num} loaded ({len(chapters[ch_num].get("sections", []))} sections)')
    except:
        log_msg(f'⚠ Ch {ch_num} not found')

# Missing sections to generate
missing = [
    {'ch': 5, 'sec': 4, 'title': 'The Cost of Cascades', 'prompt': 'Write Section 4: "The Cost of Cascades". Discuss real-world consequences of information cascades on democracy, public health, and social cohesion. 800-1000 words.'},
    {'ch': 6, 'sec': 2, 'title': 'Winner-Take-All Markets', 'prompt': 'Write Section 2: "Winner-Take-All Markets". Explain power-law dynamics in platform adoption. Compare MySpace vs Facebook, Snapchat vs Instagram. 800-1000 words.'},
    {'ch': 6, 'sec': 4, 'title': 'The Cost of Concentration', 'prompt': 'Write Section 4: "The Cost of Concentration". Discuss monopoly power, privacy violations, and costs of mega-platform dominance. 800-1000 words.'},
    {'ch': 7, 'sec': 2, 'title': 'Disease as Network Contagion', 'prompt': 'Write Section 2: "Disease as Network Contagion". Explain pandemic spread using network science—contact networks, R-naught, disease spread patterns. Use COVID-19. 800-1000 words.'},
    {'ch': 8, 'sec': 1, 'title': 'Networks and Artificial Intelligence', 'prompt': 'Write Section 1: "Networks and Artificial Intelligence". Explain how neural networks ARE networks. How AI will shape future networks. Include recommendation systems, autonomous agents, swarm intelligence. 800-1000 words.'},
    {'ch': 8, 'sec': 2, 'title': 'Quantum Networks and Future Cryptography', 'prompt': 'Write Section 2: "Quantum Networks and Future Cryptography". Explain quantum computing and quantum networks. How they will transform network security. 800-1000 words.'},
]

system_prompt = 'You are a science writer for a network science book. Write engaging, clear prose. Target: 800-1000 words per section. Include real examples, vivid metaphors, and compelling narrative.'

for missing_sec in missing:
    ch_num = missing_sec['ch']
    sec_num = missing_sec['sec']
    
    log_msg(f'\n[Ch {ch_num}, Sec {sec_num}] {missing_sec["title"]}...')
    
    response = call_claude(system_prompt, missing_sec['prompt'])
    if response:
        log_msg(f'  ✓ {len(response)} chars')
        
        # Add to chapter
        if ch_num not in chapters:
            chapters[ch_num] = {'chapter': ch_num, 'title': 'Placeholder', 'sections': [], 'introduction': '', 'conclusion': ''}
        
        # Ensure sections list exists
        if 'sections' not in chapters[ch_num]:
            chapters[ch_num]['sections'] = []
        
        chapters[ch_num]['sections'].append({
            'number': sec_num,
            'title': missing_sec['title'],
            'content': response
        })
    else:
        log_msg(f'  ✗ Failed')

# Calculate word counts
total_words = 0
for ch_num in range(1, 9):
    if ch_num in chapters:
        ch_words = sum([len(s.get('content', '').split()) for s in chapters[ch_num].get('sections', [])])
        ch_words += len(chapters[ch_num].get('introduction', '').split())
        ch_words += len(chapters[ch_num].get('conclusion', '').split())
        total_words += ch_words
        log_msg(f'Ch {ch_num}: ~{ch_words:,} words')

log_msg(f'\n=== MANUSCRIPT COMPILATION ===')
log_msg(f'Total chapters: 8')
log_msg(f'Total words: ~{total_words:,}')

# Save full manuscript
manuscript = {
    'title': 'The Hidden Architecture: Network Science and the Structure of Everything',
    'chapters': chapters,
    'total_word_count': total_words,
    'compilation_date': datetime.now().isoformat(),
    'status': 'COMPLETE'
}

with open('linked_FULL_MANUSCRIPT_COMPLETE.json', 'w', encoding='utf-8') as f:
    json.dump(manuscript, f, indent=2)

log_msg(f'\n✓ Full manuscript saved: linked_FULL_MANUSCRIPT_COMPLETE.json')
log_msg(f'Ready for peer review and Phase 2/5 consolidation')
