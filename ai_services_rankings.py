# ai_services_rankings.py
# Generates ai-services-rankings.json from model-registry.json (source of truth).
# Falls back to static list if registry unavailable.
# Output: ai-services-rankings.json in _studio
# Schedule: daily 05:30 AM via Task Scheduler \Studio\AIServicesRankings

import urllib.request, json, re, html, time
from datetime import datetime, timezone

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

# ── Build categories from model-registry.json ──────────────────────────────
def _build_search(registry):
    search_section = registry.get("search", {})
    result = []
    for key, svc in search_section.items():
        if key.startswith("_") or not isinstance(svc, dict):
            continue
        result.append({
            "name": svc.get("name", key),
            "provider": svc.get("name", key),
            "url": svc.get("url", ""),
            "tier": "free" if svc.get("free_tier") else "paid",
            "free_tier": svc.get("free_tier", False),
            "notes": svc.get("studio_use", "")[:100],
            "free_limits": svc.get("free_limits", ""),
            "studio_connected": svc.get("studio_connected", False),
            "api_available": svc.get("api_available", False),
        })
    return result

def build_from_registry():
    registry = json.load(open(REGISTRY_FILE, encoding="utf-8", errors="replace"))
    providers = registry.get("providers", {})
    image_gen = registry.get("image_generation", {})
    video_gen = registry.get("video_generation", {})

    chat = []
    code = []
    embedding = []
    voice = []

    for prov_key, prov in providers.items():
        prov_name = prov.get("name", prov_key)
        prov_url  = prov.get("url", "")
        studio_connected = prov.get("studio_connected", False)
        for model_key, model in prov.get("models", {}).items():
            tier = model.get("tier", "paid")
            if "local" in tier:
                tier = "free"
            display = model.get("display", model_key)
            notes = model.get("studio_use", model.get("notes", ""))
            if model.get("status","").startswith("active"):
                best = model.get("best_for", [])
                entry = {
                    "name": display,
                    "provider": prov_name,
                    "url": prov_url,
                    "tier": tier,
                    "notes": notes[:100],
                    "model_id": model_key,
                    "studio_connected": studio_connected,
                    "free_limits": model.get("free_limits", ""),
                    "context_window": str(model.get("context_window", "")),
                }
                # Route to correct category
                if any(k in best for k in ["embeddings", "semantic search"]):
                    embedding.append(entry)
                elif any(k in best for k in ["code generation", "code review", "coding"]):
                    code.append(entry)
                elif "speech" in " ".join(best) or "transcription" in " ".join(best):
                    voice.append(entry)
                elif model.get("status") not in ["active_legacy", "active_but_superseded", "leaked_codename_in_development", "just_released"]:
                    chat.append(entry)

    # Image gen from registry
    img = []
    for key, svc in image_gen.items():
        if key.startswith('_') or not isinstance(svc, dict):
            continue
        img.append({
            "name": svc.get("name", key),
            "provider": svc.get("name", key),
            "url": svc.get("url", ""),
            "tier": "free" if svc.get("free_tier") else "paid",
            "notes": svc.get("studio_use", ""),
            "free_limits": svc.get("free_limits", ""),
            "api_available": svc.get("api_available", False),
        })

    # Video gen from registry
    vid = []
    for key, svc in video_gen.items():
        if key.startswith('_') or not isinstance(svc, dict):
            continue
        vid.append({
            "name": svc.get("name", key),
            "provider": svc.get("name", key),
            "url": svc.get("url", ""),
            "tier": "free" if svc.get("free_tier") else "paid",
            "notes": svc.get("studio_use", ""),
        })

    return {"chat": chat, "image_gen": img, "video_gen": vid,
            "code": code, "embedding": embedding, "voice": voice,
            "search": _build_search(registry)}

try:
    SERVICES = build_from_registry()
    print("Built from model-registry.json: " +
          str(sum(len(v) for v in SERVICES.values())) + " total models")
except Exception as e:
    print("Registry load failed (" + str(e)[:60] + ") — using static fallback")
    SERVICES = {
        "chat": [
            {"name":"Claude Sonnet 4.6","provider":"Anthropic","url":"https://anthropic.com","tier":"paid","notes":"Primary reasoning engine"},
            {"name":"Gemini 2.5 Flash","provider":"Google","url":"https://aistudio.google.com","tier":"free","notes":"Primary free workhorse — 1500 RPD"},
            {"name":"Groq Llama 3.3 70B","provider":"Groq","url":"https://console.groq.com","tier":"free","notes":"Fastest free inference — 14400 RPD"},
            {"name":"Mistral Large","provider":"Mistral","url":"https://console.mistral.ai","tier":"free","notes":"1B tokens/month free"},
            {"name":"Cerebras Qwen3 235B","provider":"Cerebras","url":"https://cloud.cerebras.ai","tier":"free","notes":"1M tokens/day free"},
            {"name":"gemma3:4b","provider":"Ollama/Local","url":"http://localhost:11434","tier":"free","notes":"Local — zero API cost"},
        ],
        "image_gen": [],
        "video_gen": [],
        "code": [],
        "embedding": [],
        "voice": [],
    }

# Try to fetch recency signals from a few public sources
# to flag newly trending or newly released services
recency_flags = {}

try:
    # Check HN for AI service mentions in last 7 days
    cutoff = int((now - __import__("datetime").timedelta(days=7)).timestamp())
    hn = json.loads(fetch(
        "https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=50"
        "&numericFilters=created_at_i>" + str(cutoff)
        + "&query=AI+model+release"
    ))
    for hit in hn.get("hits", []):
        title = hit.get("title", "").lower()
        for svc in ["midjourney","runway","sora","kling","elevenlabs","flux","ideogram",
                    "gemini","claude","gpt","mistral","deepseek","cursor","copilot"]:
            if svc in title:
                recency_flags[svc] = recency_flags.get(svc, 0) + 1
    print("HN recency signals: " + str(len(recency_flags)) + " services mentioned")
    time.sleep(0.5)
except Exception as e:
    print("HN recency fetch failed: " + str(e)[:60])

# Build output structure with rank + recency signal
output = {
    "_schema": "1.0",
    "_description": "AI services ranked by category. Updated daily 05:30 AM.",
    "generated_at": now_iso,
    "date": today,
    "categories": {}
}

for category, services in SERVICES.items():
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
            "url": svc["url"],
            "tier": svc["tier"],
            "notes": svc["notes"],
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
print("Written: ai-services-rankings.json")
print("Categories: " + ", ".join(output["categories"].keys()))
for cat, items in output["categories"].items():
    trending = [i["name"] for i in items if i["trending"]]
    print("  " + cat + ": " + str(len(items)) + " services" +
          (" | TRENDING: " + ", ".join(trending) if trending else ""))

# Heartbeat
try:
    hb_path = STUDIO + "/heartbeat-log.json"
    try:
        hb = json.load(open(hb_path, encoding="utf-8"))
    except Exception:
        hb = []
    if isinstance(hb, list):
        hb = {"_schema": "1.0", "entries": hb}
    hb.setdefault("entries", []).append({
        "date": now_iso, "agent": "ai-services-rankings",
        "status": "clean",
        "notes": str(len(SERVICES)) + " categories updated"
    })
    json.dump(hb, open(hb_path, "w", encoding="utf-8"), indent=2)
except Exception as e:
    print("Heartbeat error: " + str(e)[:60])

print("Done.")
