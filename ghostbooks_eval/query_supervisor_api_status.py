import json, os, requests
from datetime import datetime

with open('..\\studio-config.json', 'rb') as f:
    config = json.loads(f.read().decode('utf-8-sig'))

ANTHROPIC_API_KEY = config.get('anthropic_api_key', '')

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

log_msg('=== SUPERVISOR QUERY: API THROTTLE STATUS & ALTERNATIVES ===')

system_prompt = '''You are the Studio Supervisor. Analyze current API usage and recommend best path forward.

Context:
- Claude API: Rate-limited on last 6 requests (instant 429 errors)
- Groq API: Rate-limited after 3 successful requests (429 on subsequent requests)
- Task: Write 6 missing book sections (~4,000-5,000 words total)

Available APIs:
- Claude (anthropic_api_key)
- Groq (Groq API Key)
- Gemini (gemini_api_key)
- Mistral (Mistral API Key)
- Cerebras (Cerebras API Key)
- OpenRouter (openrouter_api_key)

Questions:
1. Which APIs are throttled and for how long?
2. Which alternative API would you recommend for this task?
3. Should we: A) Wait for reset, B) Switch to alternative now, C) Distribute across multiple?
4. Best practice: How should Studio handle simultaneous API throttling?

Provide recommendation with rationale.'''

user_prompt = 'Analyze API status and recommend next action for finishing 6 missing book sections.'

try:
    headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
    payload = {
        'model': 'claude-opus-4-20250514',
        'max_tokens': 1500,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_prompt}]
    }
    resp = requests.post('https://api.anthropic.com/v1/messages', json=payload, headers=headers, timeout=30)
    
    if resp.status_code == 200:
        data = resp.json()
        if data.get('content'):
            supervisor_response = data['content'][0].get('text', '')
            log_msg('✓ Supervisor analysis received:\n')
            print(supervisor_response)
    elif resp.status_code == 429:
        log_msg('Claude API: RATE LIMITED (429)')
        log_msg('Checking alternatives...')
    else:
        log_msg(f'Error {resp.status_code}: {resp.text[:200]}')
        
except Exception as e:
    log_msg(f'Error: {e}')

log_msg('\n=== AWAITING SUPERVISOR RECOMMENDATION ===')
