import json, os, requests
from datetime import datetime

with open('..\\studio-config.json', 'rb') as f:
    config = json.loads(f.read().decode('utf-8-sig'))

GROQ_API_KEY = config.get('Groq API Key', '')
GROQ_MODEL = config.get('groq_model', 'llama-3.1-70b-versatile')

def log_msg(msg):
    ts = datetime.now().isoformat()
    print(f'[{ts}] {msg}')

log_msg('Testing Groq connection...')
log_msg(f'API Key length: {len(GROQ_API_KEY)}')
log_msg(f'Model: {GROQ_MODEL}')

headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
payload = {
    'model': GROQ_MODEL,
    'max_tokens': 100,
    'messages': [{'role': 'user', 'content': 'Hello'}]
}

try:
    resp = requests.post('https://api.groq.com/openai/v1/chat/completions', json=payload, headers=headers, timeout=10)
    log_msg(f'Status: {resp.status_code}')
    log_msg(f'Response: {resp.text[:500]}')
except Exception as e:
    log_msg(f'Error: {e}')
