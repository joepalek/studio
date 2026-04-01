import json, os, requests
from datetime import datetime

with open('..\\studio-config.json', 'rb') as f:
    config = json.loads(f.read().decode('utf-8-sig'))

GROQ_API_KEY = config.get('Groq API Key', '')
GROQ_MODEL = 'llama-3.3-70b-versatile'  # HARDCODED - current working model

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

if not GROQ_API_KEY:
    log_msg('ERROR: No Groq API Key')
    exit(1)

log_msg(f'✓ Groq API Key loaded')
log_msg(f'✓ Model: {GROQ_MODEL}')

def call_groq(system, user):
    try:
        headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
        payload = {
            'model': GROQ_MODEL,
            'max_tokens': 3000,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user}
            ]
        }
        resp = requests.post('https://api.groq.com/openai/v1/chat/completions', json=payload, headers=headers, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('choices'):
                return data['choices'][0]['message']['content']
        else:
            log_msg(f'Groq {resp.status_code}: {resp.text[:100]}')
    except Exception as e:
        log_msg(f'Exception: {e}')
    return None

log_msg('\n=== CHAPTERS 5-8 EXPANSION (GROQ) ===')

chapters_data = {}

# CHAPTER 5
log_msg('\n=== CHAPTER 5: Information Cascades & Fake News ===')
ch5_sections = []
for i in range(1, 5):
    log_msg(f'[Ch 5, Sec {i}] Generating...')
    system_prompt = 'You are a science writer for a network science book. Write engaging, clear prose about information cascades and misinformation. 800-1000 words. Include real examples.'
    
    section_prompts = {
        1: 'Write Section 1: "The Viral Truth vs. The Persistent Lie". Explain why false information spreads faster than corrections using network science. Use COVID misinformation as main example. Make it vivid and compelling.',
        2: 'Write Section 2: "Threshold Effects and Tipping Points". Explain how information cascades through networks—not everyone needs to believe for it to spread. Use election misinformation or social media panics.',
        3: 'Write Section 3: "Echo Chambers and Algorithmic Amplification". Explain how networks cluster believers together and algorithms amplify divisive content. Use Twitter/TikTok/Facebook examples.',
        4: 'Write Section 4: "The Cost of Cascades". Discuss real-world consequences of information cascades on democracy, public health, and social cohesion.',
    }
    
    response = call_groq(system_prompt, section_prompts[i])
    if response:
        log_msg(f'  ✓ {len(response)} chars')
        ch5_sections.append({'number': i, 'title': ['The Viral Truth vs. The Persistent Lie', 'Threshold Effects and Tipping Points', 'Echo Chambers and Algorithmic Amplification', 'The Cost of Cascades'][i-1], 'content': response})
    else:
        log_msg(f'  ✗ Failed')

chapters_data['ch5'] = {'chapter': 5, 'title': 'The Contagion of Ideas: How Information (and Misinformation) Spreads Through Networks', 'sections': ch5_sections, 'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in ch5_sections])}

# CHAPTER 6
log_msg('\n=== CHAPTER 6: Platform Economics & Winner-Take-All ===')
ch6_sections = []
for i in range(1, 5):
    log_msg(f'[Ch 6, Sec {i}] Generating...')
    system_prompt = 'You are a science writer. Write about network effects, platform monopolies, and market concentration. 800-1000 words. Use compelling real examples.'
    
    section_prompts = {
        1: 'Write Section 1: "The Network Effect Gold Rush". Explain how platforms exploit network effects to achieve dominance. Use Facebook, Uber, TikTok, WhatsApp as examples.',
        2: 'Write Section 2: "Winner-Take-All Markets". Explain power-law dynamics in platform adoption. Compare MySpace vs Facebook, Snapchat vs Instagram.',
        3: 'Write Section 3: "The Engagement Algorithm: Designing Networks for Profit". Explain how platforms design algorithms to maximize engagement—even if it spreads misinformation.',
        4: 'Write Section 4: "The Cost of Concentration". Discuss monopoly power, privacy violations, and costs of mega-platform dominance.',
    }
    
    response = call_groq(system_prompt, section_prompts[i])
    if response:
        log_msg(f'  ✓ {len(response)} chars')
        ch6_sections.append({'number': i, 'title': ['The Network Effect Gold Rush', 'Winner-Take-All Markets', 'The Engagement Algorithm: Designing Networks for Profit', 'The Cost of Concentration'][i-1], 'content': response})
    else:
        log_msg(f'  ✗ Failed')

chapters_data['ch6'] = {'chapter': 6, 'title': 'Platform Economics & Winner-Take-All Markets', 'sections': ch6_sections, 'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in ch6_sections])}

# CHAPTER 7
log_msg('\n=== CHAPTER 7: Biological Networks & Pandemic Prediction ===')
ch7_sections = []
for i in range(1, 4):
    log_msg(f'[Ch 7, Sec {i}] Generating...')
    system_prompt = 'You are a science writer. Write about biological networks, disease spread, and epidemic prediction. 800-1000 words. Use real pandemic examples.'
    
    section_prompts = {
        1: 'Write Section 1: "The Hidden Networks Inside Us". Explain protein interaction networks, neural networks in the brain, metabolic networks. Show how network science applies to biology.',
        2: 'Write Section 2: "Disease as Network Contagion". Explain pandemic spread using network science—contact networks, R-naught, disease spread patterns. Use COVID-19.',
        3: 'Write Section 3: "Predicting and Preventing Epidemics". Explain how network science enables epidemic prediction and intervention design.',
    }
    
    response = call_groq(system_prompt, section_prompts[i])
    if response:
        log_msg(f'  ✓ {len(response)} chars')
        ch7_sections.append({'number': i, 'title': ['The Hidden Networks Inside Us', 'Disease as Network Contagion', 'Predicting and Preventing Epidemics'][i-1], 'content': response})
    else:
        log_msg(f'  ✗ Failed')

chapters_data['ch7'] = {'chapter': 7, 'title': 'Biological Networks & Pandemic Prediction', 'sections': ch7_sections, 'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in ch7_sections])}

# CHAPTER 8
log_msg('\n=== CHAPTER 8: The Future of Networks ===')
ch8_sections = []
for i in range(1, 4):
    log_msg(f'[Ch 8, Sec {i}] Generating...')
    system_prompt = 'You are a science writer. Write about the future of networks, AI, and intentional design. 800-1000 words.'
    
    section_prompts = {
        1: 'Write Section 1: "Networks and Artificial Intelligence". Explain how neural networks ARE networks. How AI will shape future networks.',
        2: 'Write Section 2: "Quantum Networks and Future Cryptography". Explain quantum computing and quantum networks.',
        3: 'Write Section 3: "Designing Better Networks". Discuss how we can design networks for resilience, fairness, and human flourishing.',
    }
    
    response = call_groq(system_prompt, section_prompts[i])
    if response:
        log_msg(f'  ✓ {len(response)} chars')
        ch8_sections.append({'number': i, 'title': ['Networks and Artificial Intelligence', 'Quantum Networks and Future Cryptography', 'Designing Better Networks'][i-1], 'content': response})
    else:
        log_msg(f'  ✗ Failed')

chapters_data['ch8'] = {'chapter': 8, 'title': 'The Future of Networks: AI, Quantum, and Intentional Design', 'sections': ch8_sections, 'word_count_estimate': sum([len(s['content'].split()) if s['content'] else 0 for s in ch8_sections])}

# Save all
for ch_key, ch_data in chapters_data.items():
    with open(f'ghost_outlines/{ch_key}_FULL_PROSE.json', 'w', encoding='utf-8') as f:
        json.dump(ch_data, f, indent=2)
    log_msg(f'✓ {ch_key.upper()} saved')

total_words = sum([ch['word_count_estimate'] for ch in chapters_data.values()])
log_msg(f'\n=== GROQ BUILD COMPLETE ===')
log_msg(f'Chapters 5-8 generated')
log_msg(f'Total new words: ~{total_words:,}')
log_msg(f'Full manuscript (Ch 1-8): ~{20312 + total_words:,} words')
