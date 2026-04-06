"""
ai_services_rankings.py
Generates ai-services-rankings.json from model-registry.json (source of truth).
Includes comprehensive engine/model data for supervisor routing decisions.
Output: ai-services-rankings.json in _studio
Schedule: daily 05:30 AM via Task Scheduler
"""

# EXPECTED_RUNTIME_SECONDS: 120

MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule

import urllib.request, json, re, html, time
from datetime import datetime, timezone

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

STUDIO = "G:/My Drive/Projects/_studio"
OUT_FILE = STUDIO + "/ai-services-rankings.json"
REGISTRY_FILE = STUDIO + "/model-registry.json"
now = datetime.now(timezone.utc)
now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
today = now.strftime("%Y-%m-%d")

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")

# ── Build categories from current model-registry.json schema ──────────────────
def build_from_registry():
    """Parse the current model-registry.json schema (engines + models + task_routing_table)."""
    registry = json.load(open(REGISTRY_FILE, encoding="utf-8", errors="replace"))
    
    engines = registry.get("engines", {})
    models = registry.get("models", {})
    routing = registry.get("task_routing_table", {})
    cost_gates = registry.get("cost_gates", {})
    clawcode = registry.get("clawcode_install", {})
    
    # Build engine lookup
    engine_info = {}
    for eng_name, eng_data in engines.items():
        if eng_name.startswith("_"):
            continue
        engine_info[eng_name] = {
            "type": eng_data.get("type", "unknown"),
            "provider": eng_data.get("provider", eng_name),
            "base_url": eng_data.get("base_url", ""),
            "api_cost_per_1k": eng_data.get("api_cost_per_1k_tokens", "varies"),
            "status": eng_data.get("status", "unknown"),
            "note": eng_data.get("note", "")
        }
    
    # Categorize models
    chat = []
    code = []
    local = []
    
    for model_id, model_data in models.items():
        if model_id.startswith("_"):
            continue
        
        engine_name = model_data.get("engine", "")
        eng = engine_info.get(engine_name, {})
        tier = model_data.get("tier", "paid")
        task_types = model_data.get("task_types", [])
        
        entry = {
            "name": model_id,
            "display": model_id,
            "provider": eng.get("provider", engine_name),
            "engine": engine_name,
            "tier": tier,
            "cost_input": model_data.get("cost_per_1k_input", 0),
            "cost_output": model_data.get("cost_per_1k_output", 0),
            "context_window": model_data.get("context_window", 0),
            "task_types": task_types,
            "supervisor_rule": model_data.get("supervisor_rule", ""),
            "tool_calling": model_data.get("tool_calling", "unknown"),
            "studio_connected": True,
            "notes": model_data.get("supervisor_rule", "")[:100]
        }
        
        # Route to correct category
        if "free_local" in tier or "local" in engine_name:
            local.append(entry)
        elif any(t in task_types for t in ["scraper", "boilerplate", "formatter", "one_shot_script", "test_writer"]):
            code.append(entry)
        else:
            chat.append(entry)
    
    # Build task routing summary
    routing_summary = []
    for task_type, route in routing.items():
        if task_type.startswith("_"):
            continue
        routing_summary.append({
            "task_type": task_type,
            "primary": route.get("primary", ""),
            "engine": route.get("engine", ""),
            "fallback": route.get("fallback", "none")
        })
    
    return {
        "chat": chat,
        "code": code, 
        "local": local,
        "engines": list(engine_info.values()),
        "routing": routing_summary,
        "cost_gates": cost_gates,
        "clawcode_status": clawcode.get("status", "unknown")
    }

# ── Static fallback services (image gen, video, search, voice) ────────────────
STATIC_SERVICES = {
    "image_gen": [
        {"name": "DALL-E 3", "provider": "OpenAI", "tier": "paid", "notes": "Best prompt adherence", "studio_connected": False},
        {"name": "Midjourney v6", "provider": "Midjourney", "tier": "paid", "notes": "Best aesthetics", "studio_connected": False},
        {"name": "FLUX.1", "provider": "Black Forest Labs", "tier": "free", "notes": "Open source, local option", "studio_connected": False},
        {"name": "Stable Diffusion XL", "provider": "Stability AI", "tier": "free", "notes": "Local, controlnet support", "studio_connected": False},
        {"name": "Ideogram 2.0", "provider": "Ideogram", "tier": "free", "notes": "Best for text in images", "studio_connected": False},
        {"name": "Leonardo.ai", "provider": "Leonardo", "tier": "free", "notes": "150 free credits/day", "studio_connected": False},
    ],
    "video_gen": [
        {"name": "Sora", "provider": "OpenAI", "tier": "paid", "notes": "Best quality, limited access", "studio_connected": False},
        {"name": "Kling", "provider": "Kuaishou", "tier": "free", "notes": "Best free option", "studio_connected": False},
        {"name": "Runway Gen-3", "provider": "Runway", "tier": "paid", "notes": "Fast iteration", "studio_connected": False},
        {"name": "Higgsfield", "provider": "Higgsfield", "tier": "free", "notes": "Original Series contests", "studio_connected": False},
        {"name": "Pika Labs", "provider": "Pika", "tier": "free", "notes": "Free tier available", "studio_connected": False},
        {"name": "Luma Dream Machine", "provider": "Luma AI", "tier": "free", "notes": "Free generations daily", "studio_connected": False},
    ],
    "search": [
        {"name": "Perplexity Pro", "provider": "Perplexity", "tier": "paid", "notes": "Best for research", "studio_connected": False},
        {"name": "You.com", "provider": "You.com", "tier": "free", "notes": "Free API available", "studio_connected": False},
        {"name": "Tavily", "provider": "Tavily", "tier": "free", "notes": "MCP connected", "studio_connected": True},
        {"name": "Brave Search API", "provider": "Brave", "tier": "free", "notes": "2000 free/month", "studio_connected": False},
        {"name": "SerpAPI", "provider": "SerpAPI", "tier": "free", "notes": "100 free/month", "studio_connected": False},
    ],
    "voice": [
        {"name": "ElevenLabs", "provider": "ElevenLabs", "tier": "paid", "notes": "Best voice cloning", "studio_connected": False},
        {"name": "OpenAI TTS", "provider": "OpenAI", "tier": "paid", "notes": "Good quality, fast", "studio_connected": False},
        {"name": "Whisper", "provider": "OpenAI/Local", "tier": "free", "notes": "Local transcription", "studio_connected": False},
        {"name": "Coqui TTS", "provider": "Coqui", "tier": "free", "notes": "Open source", "studio_connected": False},
    ],
    "embedding": [
        {"name": "text-embedding-3-large", "provider": "OpenAI", "tier": "paid", "notes": "Best quality", "studio_connected": False},
        {"name": "voyage-3", "provider": "Voyage AI", "tier": "paid", "notes": "Best for RAG", "studio_connected": False},
        {"name": "nomic-embed-text", "provider": "Ollama/Local", "tier": "free", "notes": "Local via Ollama", "studio_connected": True},
        {"name": "all-MiniLM-L6-v2", "provider": "HuggingFace/Local", "tier": "free", "notes": "ChromaDB default", "studio_connected": True},
    ]
}

# ── Main execution ────────────────────────────────────────────────────────────
try:
    registry_data = build_from_registry()
    print("Built from model-registry.json:")
    print("  Chat models: " + str(len(registry_data["chat"])))
    print("  Code models: " + str(len(registry_data["code"])))
    print("  Local models: " + str(len(registry_data["local"])))
    print("  Engines: " + str(len(registry_data["engines"])))
    print("  Task routes: " + str(len(registry_data["routing"])))
except Exception as e:
    print("Registry load failed (" + str(e)[:60] + ") - using minimal fallback")
    registry_data = {
        "chat": [
            {"name": "claude-sonnet-4-6", "provider": "Anthropic", "tier": "standard", "notes": "Primary workhorse"},
            {"name": "gemini-2.0-flash", "provider": "Google", "tier": "free", "notes": "Free tier"},
        ],
        "code": [],
        "local": [],
        "engines": [],
        "routing": [],
        "cost_gates": {},
        "clawcode_status": "unknown"
    }

# Try to fetch recency signals from HN
recency_flags = {}
try:
    import datetime as dt
    cutoff = int((now - dt.timedelta(days=7)).timestamp())
    hn = json.loads(fetch(
        "https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=50"
        "&numericFilters=created_at_i>" + str(cutoff)
        + "&query=AI+model+release"
    ))
    for hit in hn.get("hits", []):
        title = hit.get("title", "").lower()
        for svc in ["midjourney","runway","sora","kling","elevenlabs","flux","ideogram",
                    "gemini","claude","gpt","mistral","deepseek","cursor","copilot",
                    "ollama","qwen","llama","anthropic","openai"]:
            if svc in title:
                recency_flags[svc] = recency_flags.get(svc, 0) + 1
    print("HN recency signals: " + str(len(recency_flags)) + " services mentioned")
    time.sleep(0.5)
except Exception as e:
    print("HN recency fetch failed: " + str(e)[:60])

# Build output structure
output = {
    "_schema": "2.0",
    "_description": "AI services ranked by category. Built from model-registry.json + static additions.",
    "_note": "Supervisor uses this for routing decisions. Updated daily 05:30 AM.",
    "generated_at": now_iso,
    "date": today,
    
    # Registry-derived categories
    "chat_models": registry_data["chat"],
    "code_models": registry_data["code"],
    "local_models": registry_data["local"],
    "engines": registry_data["engines"],
    "task_routing": registry_data["routing"],
    "cost_gates": registry_data["cost_gates"],
    "clawcode_status": registry_data["clawcode_status"],
    
    # Static service categories (for sidebar display)
    "categories": {}
}

# Add static services with buzz scores
for category, services in STATIC_SERVICES.items():
    ranked = []
    for i, svc in enumerate(services):
        name_lower = svc["name"].lower()
        provider_lower = svc["provider"].lower()
        buzz = 0
        for flag_key, count in recency_flags.items():
            if flag_key in name_lower or flag_key in provider_lower:
                buzz += count
        ranked.append({
            "rank": i + 1,
            "name": svc["name"],
            "provider": svc["provider"],
            "tier": svc["tier"],
            "notes": svc["notes"],
            "studio_connected": svc.get("studio_connected", False),
            "buzz_score": buzz,
            "trending": buzz >= 2
        })
    # Re-sort: trending items float up
    ranked.sort(key=lambda x: (-x["buzz_score"], x["rank"]))
    for i, item in enumerate(ranked):
        item["rank"] = i + 1
    output["categories"][category] = ranked

# Write output
json.dump(output, open(OUT_FILE, "w", encoding="utf-8"), indent=2)
print("\nWritten: ai-services-rankings.json")
print("Categories: " + ", ".join(output["categories"].keys()))

# Summary
for cat, items in output["categories"].items():
    trending = [i["name"] for i in items if i.get("trending")]
    print("  " + cat + ": " + str(len(items)) + " services" +
          (" | TRENDING: " + ", ".join(trending) if trending else ""))

# Heartbeat
try:
    hb_path = STUDIO + "/heartbeat-log.json"
    try:
        hb = json.load(open(hb_path, encoding="utf-8"))
    except Exception:
        hb = {"_schema": "1.0", "entries": []}
    if isinstance(hb, list):
        hb = {"_schema": "1.0", "entries": hb}
    hb.setdefault("entries", []).append({
        "date": now_iso, 
        "agent": "ai-services-rankings",
        "status": "clean",
        "notes": (str(len(registry_data["chat"])) + " chat + " 
                  + str(len(registry_data["local"])) + " local + "
                  + str(len(output["categories"])) + " static categories")
    })
    json.dump(hb, open(hb_path, "w", encoding="utf-8"), indent=2)
    print("Heartbeat written")
except Exception as e:
    print("Heartbeat error: " + str(e)[:60])

print("Done.")
