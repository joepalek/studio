# ai_services_rankings.py
# Scrapes and scores AI services daily by category.
# Output: ai-services-rankings.json in _studio
# Schedule: daily 05:30 AM via Task Scheduler \Studio\AIServicesRankings

import urllib.request, json, re, html, time
from datetime import datetime, timezone

STUDIO = "G:/My Drive/Projects/_studio"
OUT_FILE = STUDIO + "/ai-services-rankings.json"
now = datetime.now(timezone.utc)
now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
today = now.strftime("%Y-%m-%d")

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")

# Static curated base — updated by scraper with recency/buzz signals
SERVICES = {
    "chat": [
        {"name":"Claude Sonnet 4.6","provider":"Anthropic","url":"https://anthropic.com","tier":"paid","notes":"Best for reasoning/coding/agents"},
        {"name":"GPT-4o","provider":"OpenAI","url":"https://openai.com","tier":"paid","notes":"Strong general purpose"},
        {"name":"Gemini 1.5 Pro","provider":"Google","url":"https://aistudio.google.com","tier":"free+paid","notes":"Large context, free tier available"},
        {"name":"Claude Haiku 4.5","provider":"Anthropic","url":"https://anthropic.com","tier":"paid","notes":"Fast + cheap, good for batch"},
        {"name":"Gemini Flash","provider":"Google","url":"https://aistudio.google.com","tier":"free","notes":"Best free-tier speed"},
        {"name":"Llama 3.2","provider":"Meta/Ollama","url":"https://ollama.com","tier":"free","notes":"Local, no API cost"},
        {"name":"Mistral Small","provider":"Mistral","url":"https://mistral.ai","tier":"free+paid","notes":"Good free tier via OpenRouter"},
        {"name":"DeepSeek R1","provider":"DeepSeek","url":"https://deepseek.com","tier":"free","notes":"Strong reasoning, free via OpenRouter"},
    ],
    "image_gen": [
        {"name":"Midjourney v6","provider":"Midjourney","url":"https://midjourney.com","tier":"paid","notes":"Best quality, no free tier"},
        {"name":"DALL-E 3","provider":"OpenAI","url":"https://openai.com","tier":"paid","notes":"Good prompt adherence"},
        {"name":"Stable Diffusion (local)","provider":"Stability AI","url":"https://stability.ai","tier":"free","notes":"Free local via ComfyUI/A1111. RTX 3060 threshold."},
        {"name":"Ideogram 2","provider":"Ideogram","url":"https://ideogram.ai","tier":"free+paid","notes":"Best text-in-image. Free tier available."},
        {"name":"Flux 1.1 Pro","provider":"Black Forest Labs","url":"https://replicate.com","tier":"paid","notes":"Top open model quality"},
        {"name":"Playground v3","provider":"Playground","url":"https://playground.com","tier":"free+paid","notes":"Free tier, strong aesthetic quality"},
    ],
    "video_gen": [
        {"name":"Sora","provider":"OpenAI","url":"https://openai.com","tier":"paid","notes":"Best coherence, limited access"},
        {"name":"Runway Gen-3","provider":"Runway","url":"https://runwayml.com","tier":"paid","notes":"Best for creative control"},
        {"name":"Kling 1.6","provider":"Kuaishou","url":"https://klingai.com","tier":"free+paid","notes":"Strong motion quality, free tier"},
        {"name":"Higgsfield","provider":"Higgsfield","url":"https://higgsfield.ai","tier":"free+paid","notes":"Character-consistent video. Studio distribution target."},
        {"name":"Hailuo MiniMax","provider":"MiniMax","url":"https://hailuoai.com","tier":"free","notes":"Generous free tier"},
        {"name":"Veo 2","provider":"Google","url":"https://deepmind.google","tier":"paid","notes":"High quality, limited access"},
    ],
    "code": [
        {"name":"Claude Code","provider":"Anthropic","url":"https://anthropic.com","tier":"paid","notes":"Best agentic coding. Primary studio tool."},
        {"name":"GitHub Copilot","provider":"Microsoft","url":"https://github.com/copilot","tier":"paid","notes":"Best IDE integration"},
        {"name":"Cursor","provider":"Cursor","url":"https://cursor.sh","tier":"free+paid","notes":"Strong Claude/GPT integration"},
        {"name":"Gemini Code Assist","provider":"Google","url":"https://cloud.google.com","tier":"free+paid","notes":"Free tier via IDX"},
        {"name":"Codeium","provider":"Codeium","url":"https://codeium.com","tier":"free","notes":"Best free autocomplete"},
    ],
    "embedding": [
        {"name":"text-embedding-3-small","provider":"OpenAI","url":"https://openai.com","tier":"paid","notes":"Cheap, good quality"},
        {"name":"Gemini Embedding","provider":"Google","url":"https://aistudio.google.com","tier":"free","notes":"Free tier available"},
        {"name":"nomic-embed-text","provider":"Nomic/Ollama","url":"https://ollama.com","tier":"free","notes":"Best free local embedding. Studio default (ChromaDB)."},
        {"name":"mxbai-embed-large","provider":"MixedBread/Ollama","url":"https://ollama.com","tier":"free","notes":"Strong local option"},
    ],
    "voice": [
        {"name":"ElevenLabs","provider":"ElevenLabs","url":"https://elevenlabs.io","tier":"free+paid","notes":"Best voice cloning quality"},
        {"name":"OpenAI TTS","provider":"OpenAI","url":"https://openai.com","tier":"paid","notes":"Fast, natural, cheap per char"},
        {"name":"Google TTS","provider":"Google","url":"https://cloud.google.com","tier":"free+paid","notes":"WaveNet quality, free tier"},
        {"name":"Whisper (local)","provider":"OpenAI/Local","url":"https://github.com/openai/whisper","tier":"free","notes":"Best free local STT"},
    ],
    "search": [
        {"name":"Tavily","provider":"Tavily","url":"https://tavily.com","tier":"free+paid","notes":"Best AI-optimized search API. Studio connected."},
        {"name":"Perplexity API","provider":"Perplexity","url":"https://perplexity.ai","tier":"paid","notes":"Good for research tasks"},
        {"name":"SerpAPI","provider":"SerpAPI","url":"https://serpapi.com","tier":"free+paid","notes":"Google results scraping"},
        {"name":"DuckDuckGo (free)","provider":"DDG","url":"https://duckduckgo.com","tier":"free","notes":"No key needed, rate limited"},
    ]
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
