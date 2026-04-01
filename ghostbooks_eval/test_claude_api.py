import json, os, requests
from datetime import datetime

BASE_DIR = os.getcwd()
KEY_FILE = os.path.join(BASE_DIR, 'anthropic_key.txt')

ANTHROPIC_API_KEY = ''
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        raw = f.read()
        ANTHROPIC_API_KEY = raw.decode('utf-8-sig').strip()

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

log_msg(f'API Key loaded: {len(ANTHROPIC_API_KEY)} chars')

def call_claude(system_prompt, user_prompt, model='claude-3-5-sonnet-20241022'):
    if not ANTHROPIC_API_KEY:
        log_msg('ERROR: No API key')
        return None
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': model, 'max_tokens': 1000, 'system': system_prompt, 'messages': [{'role': 'user', 'content': user_prompt}]}
        log_msg(f'Calling Claude API with {model}...')
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        log_msg(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', [])
            if content and content[0].get('type') == 'text':
                return content[0].get('text', '')
        else:
            log_msg(f'Error: {resp.status_code} - {resp.text[:300]}')
    except Exception as e:
        log_msg(f'Exception: {type(e).__name__}: {str(e)[:200]}')
    return None

result = call_claude('You are helpful.', 'Say hello briefly.')
if result:
    log_msg('SUCCESS')
    print(result)
else:
    log_msg('FAILED')
