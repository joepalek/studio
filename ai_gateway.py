"""
ai_gateway.py — Studio Universal AI Gateway
============================================
Single entry point for ALL LLM calls in the studio.
Supervisor assigns task_type; gateway picks best available provider.

Usage:
    from ai_gateway import call

    response = call(
        prompt="Score this product idea: ...",
        task_type="scoring",       # see TASK_ROUTING below
        max_tokens=200,
        fallback=True              # try next provider on failure
    )
    print(response.text)
    print(response.provider)      # which provider was used
    print(response.cost_tier)     # free / paid

Task types and their routing:
    scoring        → Gemini 2.5 Flash (free) → Groq → Ollama
    classification → Gemini Flash Lite (free) → Groq 8B → Ollama
    batch          → Groq Llama 3.3 70B (free) → Cerebras → Gemini
    reasoning      → Mistral Large (free) → GitHub GPT-4o → Claude Sonnet
    coding         → Mistral Codestral (free) → GitHub DeepSeek → Claude
    speed          → Groq Llama 3.3 70B (free) → Cerebras → Gemini Flash
    quality        → Claude Sonnet 4.6 (paid) — no free fallback
    local          → Ollama gemma3:4b — no external calls
    image          → Cloudflare FLUX → Ideogram (manual) → paid

Author: Studio AI Gateway — built 2026-04-01
"""

import json, urllib.request, urllib.error, time, os, sys
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
sys.path.insert(0, "G:/My Drive/Projects/_studio")
import provider_health as ph

STUDIO = "G:/My Drive/Projects/_studio"
CONFIG_PATH  = STUDIO + "/studio-config.json"
VAULT_PATH   = STUDIO + "/.studio-vault.json"
REGISTRY_PATH = STUDIO + "/model-registry.json"
GATEWAY_LOG  = STUDIO + "/gateway-log.txt"

# Browser UA — required for Cloudflare-protected APIs (Groq, Cerebras)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")


def _load_cfg():
    # utf-8-sig handles BOM that Windows tools (Notepad, etc.) may add
    return json.load(open(CONFIG_PATH, encoding="utf-8-sig", errors="replace"))


def _load_vault():
    """
    Load API keys from .studio-vault.json.
    os.environ takes priority — Task Scheduler can inject keys without any file.
    Vault file is gitignored and only readable by the studio user account.
    Never called directly by agents — only ai_gateway internals use this.
    """
    vault = json.load(open(VAULT_PATH, encoding="utf-8-sig", errors="replace"))
    # Strip metadata keys (prefixed with _)
    vault = {k: v for k, v in vault.items() if not k.startswith("_")}
    # os.environ overrides file — normalize key names to match vault schema
    env_map = {
        "ANTHROPIC_API_KEY":  "anthropic_api_key",
        "GEMINI_API_KEY":     "gemini_api_key",
        "OPENROUTER_API_KEY": "openrouter_api_key",
        "GROQ_API_KEY":       "Groq API Key",
        "CEREBRAS_API_KEY":   "Cerebras API Key",
        "MISTRAL_API_KEY":    "Mistral API Key",
        "GITHUB_TOKEN":       "Github Token",
        "YOUTUBE_API_KEY":    "youtube_api_key",
    }
    for env_key, vault_key in env_map.items():
        if env_key in os.environ:
            vault[vault_key] = os.environ[env_key]
    return vault


def _load_keys():
    """Merge config + vault into one dict for provider callers."""
    cfg   = _load_cfg()
    vault = _load_vault()
    return {**cfg, **vault}  # vault wins on any overlap


@dataclass
class GatewayResponse:
    text: str
    provider: str
    model: str
    cost_tier: str          # free / paid
    latency_ms: int
    error: Optional[str] = None
    success: bool = True


# ── Task → Provider routing table ────────────────────────────────────────────
# Each entry is an ordered list of (provider_key, model_id) tuples.
# Gateway tries them in order, skipping on failure if fallback=True.

TASK_ROUTING = {
    "scoring": [
        ("gemini",     "gemini-2.5-flash"),
        ("groq",       "llama-3.3-70b-versatile"),
        ("cerebras",   "llama3.1-8b"),
        ("ollama",     "gemma3:4b"),
    ],
    "classification": [
        ("gemini",     "gemini-2.5-flash"),
        ("groq",       "llama-3.1-8b-instant"),
        ("cerebras",   "llama3.1-8b"),
        ("ollama",     "gemma3:4b"),
    ],
    "batch": [
        ("groq",       "llama-3.3-70b-versatile"),
        ("cerebras",   "llama3.1-8b"),
        ("gemini",     "gemini-2.5-flash"),
        ("ollama",     "gemma3:4b"),
    ],
    "reasoning": [
        ("mistral",    "mistral-large-latest"),
        ("groq",       "qwen/qwen3-32b"),
        ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),
        ("github",     "DeepSeek-R1"),
        ("anthropic",  "claude-sonnet-4-6"),
    ],
    "coding": [
        ("mistral",    "codestral-latest"),
        ("groq",       "qwen/qwen3-32b"),
        ("github",     "DeepSeek-R1"),
        ("anthropic",  "claude-sonnet-4-6"),
    ],
    "speed": [
        ("groq",       "llama-3.3-70b-versatile"),
        ("cerebras",   "qwen-3-235b-a22b-instruct-2507"),
        ("gemini",     "gemini-2.5-flash"),
    ],
    "quality": [
        ("anthropic",  "claude-sonnet-4-6"),
    ],
    "local": [
        ("ollama",     "gemma3:4b"),
    ],
    "general": [
        ("gemini",     "gemini-2.5-flash"),
        ("groq",       "llama-3.3-70b-versatile"),
        ("mistral",    "mistral-small-latest"),
        ("ollama",     "gemma3:4b"),
    ],
}

COST_TIERS = {
    "gemini": "free", "groq": "free", "cerebras": "free",
    "mistral": "free", "github": "free", "openrouter": "free",
    "cloudflare": "free", "cohere": "free", "ollama": "free",
    "anthropic": "paid",
}


# ── Provider call implementations ─────────────────────────────────────────────

def _post(url, headers, body, timeout=60):
    # ensure_ascii=True converts all non-ASCII to \uXXXX escapes —
    # prevents Windows Errno 22 / socket errors with Unicode prompt content
    data = json.dumps(body, ensure_ascii=True).encode("ascii")
    req = urllib.request.Request(url, data=data, headers=headers)
    r = urllib.request.urlopen(req, timeout=timeout)
    # Read full response in chunks — handles Transfer-Encoding: chunked
    chunks = []
    while True:
        chunk = r.read(65536)
        if not chunk:
            break
        chunks.append(chunk)
    return json.loads(b"".join(chunks))


def _call_gemini(cfg, model, prompt, max_tokens):
    key = cfg["gemini_api_key"]
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    gen_cfg = {"maxOutputTokens": max_tokens}
    # gemini-2.5-flash enters thinking mode and returns empty parts without this
    if "2.5" in model:
        gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
    r = _post(url, {"Content-Type": "application/json"}, {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_cfg
    })
    parts = r["candidates"][0]["content"].get("parts", [])
    if not parts:
        raise ValueError(f"Gemini {model} returned empty parts (thinking mode leak?)")
    return parts[0]["text"].strip()


def _call_groq(cfg, model, prompt, max_tokens):
    r = _post("https://api.groq.com/openai/v1/chat/completions", {
        "Authorization": f"Bearer {cfg['Groq API Key']}",
        "Content-Type": "application/json", "User-Agent": UA
    }, {"model": model, "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]})
    return r["choices"][0]["message"]["content"].strip()


def _call_cerebras(cfg, model, prompt, max_tokens):
    r = _post("https://api.cerebras.ai/v1/chat/completions", {
        "Authorization": f"Bearer {cfg['Cerebras API Key']}",
        "Content-Type": "application/json", "User-Agent": UA
    }, {"model": model, "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]})
    return r["choices"][0]["message"]["content"].strip()


def _call_mistral(cfg, model, prompt, max_tokens):
    r = _post("https://api.mistral.ai/v1/chat/completions", {
        "Authorization": f"Bearer {cfg['Mistral API Key']}",
        "Content-Type": "application/json"
    }, {"model": model, "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]})
    return r["choices"][0]["message"]["content"].strip()


def _call_openrouter(cfg, model, prompt, max_tokens):
    r = _post("https://openrouter.ai/api/v1/chat/completions", {
        "Authorization": f"Bearer {cfg['openrouter_api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://joepalek.github.io/studio/"
    }, {"model": model, "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]})
    return r["choices"][0]["message"]["content"].strip()


def _call_github(cfg, model, prompt, max_tokens):
    r = _post("https://models.inference.ai.azure.com/chat/completions", {
        "Authorization": f"Bearer {cfg['Github Token']}",
        "Content-Type": "application/json"
    }, {"model": model, "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]})
    return r["choices"][0]["message"]["content"].strip()


def _call_anthropic(cfg, model, prompt, max_tokens):
    import urllib.error as _ue
    try:
        r = _post("https://api.anthropic.com/v1/messages", {
            "x-api-key": cfg["anthropic_api_key"],
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }, {"model": model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]})
        return r["content"][0]["text"].strip()
    except _ue.HTTPError as e:
        # Read the response body so billing errors surface with real message
        try:
            body = json.loads(e.read().decode("utf-8", errors="replace"))
            msg  = body.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        raise Exception(msg)


def _call_ollama(cfg, model, prompt, max_tokens):
    url = cfg.get("ollama_url", "http://localhost:11434")
    r = _post(url + "/api/generate", {"Content-Type": "application/json"}, {
        "model": model, "prompt": prompt, "stream": False,
        "options": {"num_predict": max_tokens}
    }, timeout=60)
    return r["response"].strip()


PROVIDER_CALLERS = {
    "gemini":     _call_gemini,
    "groq":       _call_groq,
    "cerebras":   _call_cerebras,
    "mistral":    _call_mistral,
    "openrouter": _call_openrouter,
    "github":     _call_github,
    "anthropic":  _call_anthropic,
    "ollama":     _call_ollama,
}


# ── Gateway log ───────────────────────────────────────────────────────────────

def _log(provider, model, task_type, success, latency_ms, error=None):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    status = "OK" if success else "FAIL"
    err = f" ERROR={error[:60]}" if error else ""
    line = f"{ts} {status} provider={provider} model={model} task={task_type} ms={latency_ms}{err}\n"
    try:
        with open(GATEWAY_LOG, "a", encoding="utf-8", errors="replace") as f:
            f.write(line)
    except Exception:
        pass


# ── Main public API ────────────────────────────────────────────────────────────

def call(prompt: str,
         task_type: str = "general",
         max_tokens: int = 500,
         fallback: bool = True,
         force_provider: str = None,
         force_model: str = None) -> GatewayResponse:
    """
    Route a prompt to the best available provider for the given task type.

    Args:
        prompt:         The text prompt to send
        task_type:      One of: scoring, classification, batch, reasoning,
                        coding, speed, quality, local, general
        max_tokens:     Max tokens in response
        fallback:       If True, try next provider on failure
        force_provider: Override routing — use this specific provider
        force_model:    Override routing — use this specific model

    Returns:
        GatewayResponse with .text, .provider, .model, .cost_tier, .latency_ms
    """
    cfg = _load_keys()

    # Build route list
    if force_provider and force_model:
        route = [(force_provider, force_model)]
    else:
        route = TASK_ROUTING.get(task_type, TASK_ROUTING["general"])

    last_error = None

    for provider, model in route:
        caller = PROVIDER_CALLERS.get(provider)
        if not caller:
            continue

        # Skip models known to be defunct — don't waste a call
        if not ph.is_usable(provider, model):
            _log(provider, model, task_type, False, 0, "SKIPPED — marked defunct in provider-health.json")
            continue

        t0 = time.time()
        try:
            text = caller(cfg, model, prompt, max_tokens)
            latency_ms = int((time.time() - t0) * 1000)
            _log(provider, model, task_type, True, latency_ms)
            ph.record_success(provider, model)
            return GatewayResponse(
                text=text,
                provider=provider,
                model=model,
                cost_tier=COST_TIERS.get(provider, "unknown"),
                latency_ms=latency_ms,
                success=True
            )
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            last_error = str(e)[:120]
            # Billing gate — credit depleted: skip remaining providers, don't mark defunct
            if "credit balance is too low" in last_error or "credit balance" in last_error:
                _log(provider, model, task_type, False, latency_ms,
                     "BILLING: credits depleted — skipping provider")
                last_error = f"BILLING:{provider} credits depleted"
                if not fallback:
                    break
                continue  # try next provider without recording a health failure
            _log(provider, model, task_type, False, latency_ms, last_error)
            new_status = ph.record_failure(provider, model, last_error)
            if new_status == "defunct":
                ph.push_defunct_to_inbox()
            if not fallback:
                break
            # Consecutive failure guard — don't hammer if rate limited
            if "429" in last_error or "rate" in last_error.lower():
                time.sleep(2)

    # All providers failed
    return GatewayResponse(
        text="",
        provider="none",
        model="none",
        cost_tier="none",
        latency_ms=0,
        error=last_error,
        success=False
    )


# ── Convenience wrappers ───────────────────────────────────────────────────────

def score(prompt, max_tokens=300):
    """Score or evaluate something. Routes to best free scoring model."""
    return call(prompt, task_type="scoring", max_tokens=max_tokens)

def classify(prompt, max_tokens=100):
    """Quick classification. Routes to fastest free model."""
    return call(prompt, task_type="classification", max_tokens=max_tokens)

def batch(prompt, max_tokens=500):
    """Batch processing. Routes to highest-throughput free model."""
    return call(prompt, task_type="batch", max_tokens=max_tokens)

def reason(prompt, max_tokens=1000):
    """Complex reasoning. Routes to best free reasoning model."""
    return call(prompt, task_type="reasoning", max_tokens=max_tokens)

def fast(prompt, max_tokens=200):
    """Speed-critical task. Routes to Groq first."""
    return call(prompt, task_type="speed", max_tokens=max_tokens)

def local(prompt, max_tokens=500):
    """Privacy-sensitive or offline task. Ollama only."""
    return call(prompt, task_type="local", max_tokens=max_tokens)

def premium(prompt, max_tokens=2000):
    """High-quality task. Claude Sonnet only — costs quota."""
    return call(prompt, task_type="quality", max_tokens=max_tokens)


# ── CLI test ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("\n=== AI GATEWAY — ROUTING TEST ===\n")

    tests = [
        ("scoring",        "Rate this idea 1-10: A horror game review aggregator. Return only JSON: {score: N, reason: '...'}"),
        ("classification", "Classify as BUILD/RESEARCH/PUBLISH/KILL: 'SoBe Elixir drink revival'. One word only."),
        ("batch",          "Summarize in 10 words: overnight batch processing agent for eBay listing optimization"),
        ("reasoning",      "What are the top 3 risks of building an AI services business in 2026? Be concise."),
        ("coding",         "Write a 3-line Python function that safely loads a JSON file with utf-8 encoding."),
        ("speed",          "Say OK."),
        ("local",          "Say OK."),
    ]

    for task_type, prompt in tests:
        print(f"[{task_type.upper()}]")
        r = call(prompt, task_type=task_type, max_tokens=150)
        if r.success:
            print(f"  Provider: {r.provider} ({r.model}) [{r.cost_tier}] {r.latency_ms}ms")
            print(f"  Response: {r.text[:100]}")
        else:
            print(f"  FAILED: {r.error}")
        print()
