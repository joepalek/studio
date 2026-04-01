import json, os, requests
from datetime import datetime

with open('..\\studio-config.json', 'rb') as f:
    config = json.loads(f.read().decode('utf-8-sig'))

GEMINI_API_KEY = config.get('gemini_api_key', '')
MISTRAL_API_KEY = config.get('Mistral API Key', '')
OPENROUTER_API_KEY = config.get('openrouter_api_key', '')

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

def call_gemini(system, user):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f'{system}\n\n{user}')
        return response.text if response else None
    except Exception as e:
        log_msg(f'Gemini error: {e}')
        return None

def call_mistral(system, user):
    try:
        headers = {'Authorization': f'Bearer {MISTRAL_API_KEY}', 'Content-Type': 'application/json'}
        payload = {
            'model': 'mistral-large-latest',
            'max_tokens': 3000,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user}
            ]
        }
        resp = requests.post('https://api.mistral.ai/v1/chat/completions', json=payload, headers=headers, timeout=60)
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        log_msg(f'Mistral error: {e}')
    return None

log_msg('=== CX AGENT: FINISH LINKED MISSING SECTIONS ===')
log_msg('Supervisor recommendation: Gemini → Mistral → OpenRouter fallback chain')

# Load existing chapters
chapters = {}
for ch_num in [1, 2, 3, 4, 5, 6, 7, 8]:
    try:
        with open(f'ghost_outlines/ch{ch_num}_FULL_PROSE.json', 'rb') as f:
            chapters[ch_num] = json.loads(f.read().decode('utf-8-sig'))
    except:
        pass

missing = [
    {'ch': 5, 'sec': 4, 'title': 'The Cost of Cascades', 'prompt': 'Write Section 4: "The Cost of Cascades". Discuss real-world consequences of information cascades on democracy, public health, and social cohesion. 800-1000 words.'},
    {'ch': 6, 'sec': 2, 'title': 'Winner-Take-All Markets', 'prompt': 'Write Section 2: "Winner-Take-All Markets". Explain power-law dynamics in platform adoption. Compare MySpace vs Facebook, Snapchat vs Instagram. 800-1000 words.'},
    {'ch': 6, 'sec': 4, 'title': 'The Cost of Concentration', 'prompt': 'Write Section 4: "The Cost of Concentration". Discuss monopoly power, privacy violations, and costs of mega-platform dominance. 800-1000 words.'},
    {'ch': 7, 'sec': 2, 'title': 'Disease as Network Contagion', 'prompt': 'Write Section 2: "Disease as Network Contagion". Explain pandemic spread using network science. Use COVID-19. 800-1000 words.'},
    {'ch': 8, 'sec': 1, 'title': 'Networks and Artificial Intelligence', 'prompt': 'Write Section 1: "Networks and Artificial Intelligence". Explain how neural networks ARE networks. How AI will shape future networks. 800-1000 words.'},
    {'ch': 8, 'sec': 2, 'title': 'Quantum Networks', 'prompt': 'Write Section 2: "Quantum Networks and Future Cryptography". Explain quantum computing and quantum networks. 800-1000 words.'},
]

system_prompt = 'You are a science writer for a network science book. Write engaging, clear prose. 800-1000 words per section. Include real examples.'

for missing_sec in missing:
    ch_num = missing_sec['ch']
    sec_num = missing_sec['sec']
    
    log_msg(f'\n[Ch {ch_num}, Sec {sec_num}] {missing_sec["title"]}')
    log_msg('  Trying: Gemini...')
    
    response = call_gemini(system_prompt, missing_sec['prompt'])
    
    if not response:
        log_msg('  Gemini failed. Trying: Mistral...')
        response = call_mistral(system_prompt, missing_sec['prompt'])
    
    if response:
        log_msg(f'  ✓ Success ({len(response)} chars)')
        
        if ch_num not in chapters:
            chapters[ch_num] = {'chapter': ch_num, 'title': 'Placeholder', 'sections': [], 'introduction': '', 'conclusion': ''}
        if 'sections' not in chapters[ch_num]:
            chapters[ch_num]['sections'] = []
        
        chapters[ch_num]['sections'].append({
            'number': sec_num,
            'title': missing_sec['title'],
            'content': response
        })
    else:
        log_msg(f'  ✗ Both Gemini & Mistral failed')

# Compile
total_words = 0
for ch_num in range(1, 9):
    if ch_num in chapters:
        ch_words = sum([len(s.get('content', '').split()) for s in chapters[ch_num].get('sections', [])])
        ch_words += len(chapters[ch_num].get('introduction', '').split())
        ch_words += len(chapters[ch_num].get('conclusion', '').split())
        total_words += ch_words

manuscript = {
    'title': 'The Hidden Architecture: Network Science and the Structure of Everything',
    'chapters': chapters,
    'total_word_count': total_words,
    'compilation_date': datetime.now().isoformat(),
    'status': 'COMPLETE' if total_words > 30000 else 'PARTIAL',
    'cx_agent_note': 'Executed via CX Agent fallback chain (Claude credits depleted)'
}

with open('linked_FULL_MANUSCRIPT_COMPLETE.json', 'w', encoding='utf-8') as f:
    json.dump(manuscript, f, indent=2)

log_msg(f'\n=== CX AGENT COMPLETE ===')
log_msg(f'Total words: ~{total_words:,}')
log_msg(f'Status: {manuscript["status"]}')
log_msg(f'Saved: linked_FULL_MANUSCRIPT_COMPLETE.json')
