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

def call_claude(model):
    if not ANTHROPIC_API_KEY:
        return None, 'No key'
    try:
        headers = {'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'}
        payload = {'model': model, 'max_tokens': 100, 'messages': [{'role': 'user', 'content': 'Say hi'}]}
        log_msg(f'Trying {model}...')
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=10)
        return resp.status_code, resp.json().get('error', {}).get('message', 'ok')
    except Exception as e:
        return 'error', str(e)[:100]

models = ['claude-haiku-3-5-20241022', 'claude-opus-4-20250514', 'claude-sonnet-4-20250514']
for model in models:
    status, msg = call_claude(model)
    log_msg(f'{model}: {status} - {msg}')
