"""
test_connections.py — Studio API Connection Tester
Tests every provider in studio-config.json with a real API call.
Run: python test_connections.py
"""
import json, urllib.request, urllib.error, sys, time
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CONFIG_PATH = "G:/My Drive/Projects/_studio/studio-config.json"
cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))

results = []

def check(name, fn):
    try:
        msg = fn()
        print(f"  ✅ {name}: {msg}")
        results.append((name, "OK", msg))
    except Exception as e:
        err = str(e)[:120]
        print(f"  ❌ {name}: {err}")
        results.append((name, "FAIL", err))

def post(url, headers, body, timeout=15):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read())

def get(url, headers, timeout=15):
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read())

# Browser UA needed for Cloudflare-protected APIs (Groq, Cerebras)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

print(f"\n{'='*55}")
print(f"  STUDIO API CONNECTION TEST — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*55}\n")

# ── Anthropic ──────────────────────────────────────────────
print("[ Anthropic ]")
def test_anthropic():
    r = post("https://api.anthropic.com/v1/messages",
        {"x-api-key": cfg["anthropic_api_key"],
         "anthropic-version": "2023-06-01",
         "content-type": "application/json"},
        {"model": "claude-haiku-4-5-20251001", "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"claude-haiku-4-5 responded — stop_reason: {r.get('stop_reason','?')}"
check("Claude Haiku 4.5", test_anthropic)

# ── Google Gemini ──────────────────────────────────────────
print("\n[ Google Gemini ]")
def test_gemini(model):
    key = cfg["gemini_api_key"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    r = post(url, {"Content-Type": "application/json"},
        {"contents": [{"parts": [{"text": "Say OK"}]}],
         "generationConfig": {"maxOutputTokens": 5}})
    return f"responded OK"
check("Gemini 2.5 Flash", lambda: test_gemini("gemini-2.5-flash"))
check("Gemini 2.0 Flash", lambda: test_gemini("gemini-2.0-flash-001"))

# ── Groq ───────────────────────────────────────────────────
print("\n[ Groq ]")
def test_groq(model):
    r = post("https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {cfg['Groq API Key']}",
         "Content-Type": "application/json", "User-Agent": UA},
        {"model": model, "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"responded — model: {r['model']}"
check("Groq Llama 3.3 70B", lambda: test_groq("llama-3.3-70b-versatile"))
check("Groq Llama 3.1 8B",  lambda: test_groq("llama-3.1-8b-instant"))
check("Groq Llama 4 Scout",  lambda: test_groq("meta-llama/llama-4-scout-17b-16e-instruct"))
time.sleep(1)

# ── Cerebras ───────────────────────────────────────────────
print("\n[ Cerebras ]")
def test_cerebras():
    r = post("https://api.cerebras.ai/v1/chat/completions",
        {"Authorization": f"Bearer {cfg['Cerebras API Key']}",
         "Content-Type": "application/json", "User-Agent": UA},
        {"model": "llama3.1-8b", "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"responded — model: {r.get('model','?')}"
check("Cerebras Llama 3.1 8B", test_cerebras)

def test_cerebras_qwen():
    r = post("https://api.cerebras.ai/v1/chat/completions",
        {"Authorization": f"Bearer {cfg['Cerebras API Key']}",
         "Content-Type": "application/json", "User-Agent": UA},
        {"model": "qwen-3-235b-a22b-instruct-2507", "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"responded — model: {r.get('model','?')}"
check("Cerebras Qwen3 235B", test_cerebras_qwen)

# ── Mistral ────────────────────────────────────────────────
print("\n[ Mistral ]")
def test_mistral(model):
    r = post("https://api.mistral.ai/v1/chat/completions",
        {"Authorization": f"Bearer {cfg['Mistral API Key']}",
         "Content-Type": "application/json"},
        {"model": model, "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"responded — model: {r.get('model','?')}"
check("Mistral Small",  lambda: test_mistral("mistral-small-latest"))
check("Mistral Large",  lambda: test_mistral("mistral-large-latest"))
check("Codestral",      lambda: test_mistral("codestral-latest"))

# ── OpenRouter ─────────────────────────────────────────────
print("\n[ OpenRouter ]")
def test_openrouter(model):
    r = post("https://openrouter.ai/api/v1/chat/completions",
        {"Authorization": f"Bearer {cfg['openrouter_api_key']}",
         "Content-Type": "application/json",
         "HTTP-Referer": "https://joepalek.github.io/studio/"},
        {"model": model, "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"responded — model: {r.get('model','?')}"
check("OpenRouter DeepSeek R1 (free)", lambda: test_openrouter("deepseek/deepseek-r1:free"))
check("OpenRouter Mistral 7B (free)",  lambda: test_openrouter("mistralai/mistral-7b-instruct:free"))
check("OpenRouter Qwen3 (free)",       lambda: test_openrouter("qwen/qwen3.6-plus-preview:free"))

# ── Cohere ─────────────────────────────────────────────────
print("\n[ Cohere ]")
def test_cohere():
    r = post("https://api.cohere.com/v2/chat",
        {"Authorization": f"Bearer {cfg['Cohere API Key Trial']}",
         "Content-Type": "application/json"},
        {"model": "command-r-plus-08-2024",
         "messages": [{"role": "user", "content": "Hi"}],
         "max_tokens": 5})
    return f"responded OK"
check("Cohere Command R+", test_cohere)

# ── GitHub Models ──────────────────────────────────────────
print("\n[ GitHub Models ]")
def test_github(model):
    r = post("https://models.inference.ai.azure.com/chat/completions",
        {"Authorization": f"Bearer {cfg['Github Token']}",
         "Content-Type": "application/json"},
        {"model": model, "max_tokens": 10,
         "messages": [{"role": "user", "content": "Hi"}]})
    return f"responded OK"
check("GitHub GPT-4o",      lambda: test_github("gpt-4o"))
check("GitHub DeepSeek R1", lambda: test_github("DeepSeek-R1"))

# ── Cloudflare Workers AI ──────────────────────────────────
print("\n[ Cloudflare Workers AI ]")
def test_cloudflare(model):
    acct = cfg["Cloudflare account ID"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}"
    r = post(url,
        {"Authorization": f"Bearer {cfg['Cloudflare API Token']}",
         "Content-Type": "application/json"},
        {"messages": [{"role": "user", "content": "Hi"}],
         "max_tokens": 10})
    if r.get("success"):
        return f"responded OK"
    raise Exception(str(r.get("errors", "unknown error")))
def _test_cf_image():
    acct = cfg["Cloudflare account ID"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    r = post(url,
        {"Authorization": f"Bearer {cfg['Cloudflare API Token']}",
         "Content-Type": "application/json"},
        {"prompt": "a red circle", "num_steps": 1})
    if r.get("success"):
        return "image endpoint live (base64 image returned)"
    raise Exception(str(r.get("errors", "unknown")))

check("Cloudflare Llama 3.3 70B", lambda: test_cloudflare("@cf/meta/llama-3.3-70b-instruct-fp8-fast"))
check("Cloudflare FLUX.1 Schnell (image)", _test_cf_image)

# ── Ollama (local) ─────────────────────────────────────────
print("\n[ Ollama Local ]")
def test_ollama():
    r = post("http://localhost:11434/api/generate",
        {"Content-Type": "application/json"},
        {"model": cfg.get("ollama_model","gemma3:4b"),
         "prompt": "Hi", "stream": False,
         "options": {"num_predict": 5}})
    return f"responded — model: {r.get('model','?')}"
check("Ollama gemma3:4b", test_ollama)

# ── Summary ────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  SUMMARY")
print(f"{'='*55}")
ok   = [r for r in results if r[1] == "OK"]
fail = [r for r in results if r[1] == "FAIL"]
print(f"  ✅ PASSED: {len(ok)}/{len(results)}")
print(f"  ❌ FAILED: {len(fail)}/{len(results)}")
if fail:
    print(f"\n  Failed providers:")
    for name, _, err in fail:
        print(f"    • {name}: {err[:80]}")
print(f"\n{'='*55}\n")
