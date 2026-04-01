import os, requests
api_key = os.environ.get('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
resp = requests.get(url)
if resp.status_code == 200:
    data = resp.json()
    models = data.get('models', [])
    print(f'Available models: {len(models)}')
    for m in models[:5]:
        name = m.get('name', 'unknown')
        print(f'  {name}')
else:
    print(f'Error: {resp.status_code}')
    print(resp.text[:300])
