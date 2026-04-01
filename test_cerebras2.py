import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
cfg = json.load(open("G:/My Drive/Projects/_studio/studio-config.json", encoding="utf-8"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
headers = {"Authorization": f"Bearer {cfg['Cerebras API Key']}",
           "Content-Type": "application/json", "User-Agent": UA}
body = json.dumps({"model": "llama3.1-8b", "max_tokens": 10,
                   "messages": [{"role": "user", "content": "Say OK"}]}).encode()
req = urllib.request.Request("https://api.cerebras.ai/v1/chat/completions", data=body, headers=headers)
r = urllib.request.urlopen(req, timeout=20)
data = json.loads(r.read())
print("Cerebras llama3.1-8b OK:", data["choices"][0]["message"]["content"])

# Also test Qwen
body2 = json.dumps({"model": "qwen-3-235b-a22b-instruct-2507", "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Say OK"}]}).encode()
req2 = urllib.request.Request("https://api.cerebras.ai/v1/chat/completions", data=body2, headers=headers)
r2 = urllib.request.urlopen(req2, timeout=20)
data2 = json.loads(r2.read())
print("Cerebras Qwen3-235B OK:", data2["choices"][0]["message"]["content"])
