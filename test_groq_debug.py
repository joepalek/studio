"""
test_groq_cerebras_fix.py - Fix Cloudflare 1010 with proper headers
"""
import json, urllib.request, urllib.error
sys = __import__('sys')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cfg = json.load(open("G:/My Drive/Projects/_studio/studio-config.json", encoding="utf-8"))

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

def post_json(url, auth_key, body):
    headers = {**BROWSER_HEADERS,
               "Authorization": f"Bearer {auth_key}",
               "Content-Type": "application/json"}
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    r = urllib.request.urlopen(req, timeout=20)
    return json.loads(r.read())

def get_json(url, auth_key):
    headers = {**BROWSER_HEADERS, "Authorization": f"Bearer {auth_key}"}
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=20)
    return json.loads(r.read())

# ── Groq ──────────────────────────────────────────────────
print("=== GROQ ===")
try:
    data = get_json("https://api.groq.com/openai/v1/models", cfg["Groq API Key"])
    models = [m["id"] for m in data.get("data", [])]
    print(f"List models: OK - {len(models)} models")
    for m in sorted(models)[:10]:
        print(f"  {m}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"List models FAILED: HTTP {e.code} - {body[:200]}")

print()
try:
    r = post_json("https://api.groq.com/openai/v1/chat/completions",
        cfg["Groq API Key"],
        {"model": "llama-3.3-70b-versatile", "max_tokens": 10,
         "messages": [{"role": "user", "content": "Say OK"}]})
    print(f"Chat: OK - {r['choices'][0]['message']['content']}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"Chat FAILED: HTTP {e.code} - {body[:200]}")

# ── Cerebras ───────────────────────────────────────────────
print("\n=== CEREBRAS ===")
try:
    data = get_json("https://api.cerebras.ai/v1/models", cfg["Cerebras API Key"])
    models = [m["id"] for m in data.get("data", [])]
    print(f"List models: OK - {len(models)} models")
    for m in models:
        print(f"  {m}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"List models FAILED: HTTP {e.code} - {body[:200]}")

print()
try:
    r = post_json("https://api.cerebras.ai/v1/chat/completions",
        cfg["Cerebras API Key"],
        {"model": "llama-3.3-70b", "max_tokens": 10,
         "messages": [{"role": "user", "content": "Say OK"}]})
    print(f"Chat: OK - {r['choices'][0]['message']['content']}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"Chat FAILED: HTTP {e.code} - {body[:200]}")
