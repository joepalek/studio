import json, os, requests
from datetime import datetime

with open('..\\studio-config.json', 'rb') as f:
    config = json.loads(f.read().decode('utf-8-sig'))

GROQ_API_KEY = config.get('Groq API Key', '')
GROQ_MODEL = 'llama-3.3-70b-versatile'

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

log_msg('=== SUPERVISOR QUERY VIA GROQ ===')
log_msg('Claude: OUT OF CREDITS')
log_msg('Routing to Groq for supervisor recommendation...')

system_prompt = '''You are the Studio Supervisor. Claude API is out of credits. 

Context:
- Task: Finish 6 missing book sections (4K-5K words)
- Claude: OUT OF CREDITS
- Groq: Recently rate-limited (may have reset by now)
- Available: Gemini, Mistral, Cerebras, OpenRouter

Recommendation:
1. Best API to use now?
2. Should we wait for Groq to reset or switch to Gemini/Mistral?
3. Should we mark task for CX Agent to handle with fallback chain?

Be direct.'''

user_prompt = 'Claude out of credits. What is the best path to finish 6 book sections right now?'

try:
    headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
    payload = {
        'model': GROQ_MODEL,
        'max_tokens': 1000,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
    }
    resp = requests.post('https://api.groq.com/openai/v1/chat/completions', json=payload, headers=headers, timeout=30)
    
    if resp.status_code == 200:
        data = resp.json()
        if data.get('choices'):
            supervisor_response = data['choices'][0]['message']['content']
            log_msg('✓ Supervisor (via Groq) response:\n')
            print(supervisor_response)
    elif resp.status_code == 429:
        log_msg('Groq: RATE LIMITED (429)')
        log_msg('Supervisor recommends: Switch to Gemini or wait 1 hour')
    else:
        log_msg(f'Groq error {resp.status_code}')
        
except Exception as e:
    log_msg(f'Error: {e}')
