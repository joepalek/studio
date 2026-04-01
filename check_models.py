import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
cfg = json.load(open('G:/My Drive/Projects/_studio/studio-config.json', encoding='utf-8'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Groq - list all available models
req = urllib.request.Request('https://api.groq.com/openai/v1/models',
    headers={'Authorization': f'Bearer {cfg["Groq API Key"]}', 'User-Agent': UA})
data = json.loads(urllib.request.urlopen(req, timeout=15).read())
groq_models = sorted([m['id'] for m in data.get('data', [])])
print('=== GROQ MODELS ===')
for m in groq_models:
    print(f'  {m}')

# OpenRouter - list free models
req2 = urllib.request.Request('https://openrouter.ai/api/v1/models',
    headers={'Authorization': f'Bearer {cfg["openrouter_api_key"]}'})
data2 = json.loads(urllib.request.urlopen(req2, timeout=15).read())
free = sorted([m['id'] for m in data2.get('data', [])
               if str(m.get('pricing',{}).get('prompt','1')) == '0'])
print(f'\n=== OPENROUTER FREE MODELS ({len(free)}) ===')
for m in free[:20]:
    print(f'  {m}')
