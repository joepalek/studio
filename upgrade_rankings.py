"""
upgrade_rankings_schema.py
Upgrades ai-services-rankings.json to schema 2.0:
- Adds pricing fields: free_tier, free_tier_limits, price_input_1m, price_output_1m, price_notes
- Adds routing_tags for AI Scout offload decisions
- Adds rating_basis field explaining what the rank is based on
- Preserves all existing data
"""
import json, sys
from datetime import datetime

# Bezos Rule: circuit breaker constant
MAX_CONSECUTIVE_FAILURES = 3
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TODAY = datetime.now().strftime("%Y-%m-%d")
PATH = "G:/My Drive/Projects/_studio/ai-services-rankings.json"

d = json.load(open(PATH, encoding='utf-8-sig'))

# Pricing data per service — verified from official sources
PRICING = {
    # CHAT
    "Mistral Small":        {"free_tier": True,  "free_tier_limits": "Via OpenRouter free tier, rate limited", "price_input_1m": 0.10, "price_output_1m": 0.30, "price_notes": ""},
    "Claude Sonnet 4.6":    {"free_tier": False, "free_tier_limits": None, "price_input_1m": 3.00, "price_output_1m": 15.00, "price_notes": "Claude.ai Pro $20/mo includes usage"},
    "GPT-5.4 mini":         {"free_tier": True,  "free_tier_limits": "Free via ChatGPT Thinking feature, rate limited", "price_input_1m": 0.75, "price_output_1m": 4.50, "price_notes": "API pricing; free ChatGPT tier available"},
    "GPT-4o":               {"free_tier": True,  "free_tier_limits": "Limited free via ChatGPT", "price_input_1m": 2.50, "price_output_1m": 10.00, "price_notes": "check_for_newer: GPT-5.4"},
    "Gemini 2.5 Pro":       {"free_tier": True,  "free_tier_limits": "15 req/min, 1500 req/day via AI Studio", "price_input_1m": 1.25, "price_output_1m": 10.00, "price_notes": "Free tier generous for low-volume"},
    "Claude Haiku 4.5":     {"free_tier": False, "free_tier_limits": None, "price_input_1m": 1.00, "price_output_1m": 5.00, "price_notes": "Cheapest Claude; good for batch"},
    "Gemini 2.5 Flash":     {"free_tier": True,  "free_tier_limits": "15 req/min, 1500 req/day via AI Studio", "price_input_1m": 0.075, "price_output_1m": 0.30, "price_notes": "Best free-tier cost ratio in class"},
    "Llama 3.2":            {"free_tier": True,  "free_tier_limits": "Unlimited local via Ollama", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Free local; hardware cost only"},
    "DeepSeek R1":          {"free_tier": True,  "free_tier_limits": "Via OpenRouter free tier", "price_input_1m": 0.55, "price_output_1m": 2.19, "price_notes": "Strong reasoning at low cost"},
    # IMAGE GEN
    "Midjourney v6":        {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "$10/mo basic (200 imgs), check v7"},
    "DALL-E 3":             {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "$0.040-0.120 per image via API"},
    "Stable Diffusion (local)": {"free_tier": True, "free_tier_limits": "Unlimited local, RTX 3060 threshold", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Free after hardware; no API needed"},
    "Ideogram 2":           {"free_tier": True,  "free_tier_limits": "10 free images/day", "price_input_1m": None, "price_output_1m": None, "price_notes": "$8/mo for 400 imgs"},
    "Flux 1.1 Pro":         {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "~$0.04/image via Replicate"},
    "Playground v3":        {"free_tier": True,  "free_tier_limits": "50 free images/day", "price_input_1m": None, "price_output_1m": None, "price_notes": "$15/mo unlimited"},
    # VIDEO GEN
    "Sora":                 {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "ChatGPT Plus $20/mo includes limited Sora"},
    "Runway Gen-3":         {"free_tier": True,  "free_tier_limits": "125 one-time credits on signup", "price_input_1m": None, "price_output_1m": None, "price_notes": "$12/mo standard"},
    "Kling 1.6":            {"free_tier": True,  "free_tier_limits": "166 free credits/day", "price_input_1m": None, "price_output_1m": None, "price_notes": "Best free video tier currently"},
    "Higgsfield":           {"free_tier": True,  "free_tier_limits": "Limited free generations", "price_input_1m": None, "price_output_1m": None, "price_notes": "Studio distribution target"},
    "Hailuo MiniMax":       {"free_tier": True,  "free_tier_limits": "Generous daily free credits", "price_input_1m": None, "price_output_1m": None, "price_notes": "Best free video tier for volume"},
    "Veo 2":                {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "Limited access, waitlist"},
    # CODE
    "Claude Code":          {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "Uses Claude API quota; primary studio tool"},
    "GitHub Copilot":       {"free_tier": True,  "free_tier_limits": "2000 completions + 50 chat/mo free", "price_input_1m": None, "price_output_1m": None, "price_notes": "$10/mo Pro"},
    "Cursor":               {"free_tier": True,  "free_tier_limits": "2 week trial then $0 hobby (limited)", "price_input_1m": None, "price_output_1m": None, "price_notes": "$20/mo Pro"},
    "Gemini Code Assist":   {"free_tier": True,  "free_tier_limits": "Free via Google IDX, unlimited", "price_input_1m": None, "price_output_1m": None, "price_notes": "Best free code assist tier"},
    "Windsurf (fka Codeium)": {"free_tier": True, "free_tier_limits": "Unlimited completions free", "price_input_1m": None, "price_output_1m": None, "price_notes": "$15/mo Pro; best free autocomplete"},
    # EMBEDDING
    "text-embedding-3-small": {"free_tier": False, "free_tier_limits": None, "price_input_1m": 0.02, "price_output_1m": 0.00, "price_notes": "Cheapest quality embedding"},
    "Gemini Embedding":     {"free_tier": True,  "free_tier_limits": "1500 req/day free", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Free tier sufficient for most uses"},
    "nomic-embed-text":     {"free_tier": True,  "free_tier_limits": "Unlimited local via Ollama", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Studio default (ChromaDB). Free local."},
    "mxbai-embed-large":    {"free_tier": True,  "free_tier_limits": "Unlimited local via Ollama", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Strong local option"},
    # VOICE
    "ElevenLabs":           {"free_tier": True,  "free_tier_limits": "10k chars/mo free", "price_input_1m": None, "price_output_1m": None, "price_notes": "$5/mo Starter (30k chars)"},
    "OpenAI TTS":           {"free_tier": False, "free_tier_limits": None, "price_input_1m": None, "price_output_1m": None, "price_notes": "$15/1M chars (TTS-1), $30 HD"},
    "Google TTS":           {"free_tier": True,  "free_tier_limits": "1M chars/mo free (WaveNet 100k)", "price_input_1m": None, "price_output_1m": None, "price_notes": "Best free voice tier by volume"},
    "Whisper (local)":      {"free_tier": True,  "free_tier_limits": "Unlimited local", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Free local STT; OpenAI API $0.006/min"},
    # SEARCH
    "Tavily":               {"free_tier": True,  "free_tier_limits": "1000 searches/mo free", "price_input_1m": None, "price_output_1m": None, "price_notes": "$25/mo Pro (5k searches). Studio connected."},
    "Perplexity API":       {"free_tier": False, "free_tier_limits": None, "price_input_1m": 1.00, "price_output_1m": 1.00, "price_notes": "Per-request pricing"},
    "SerpAPI":              {"free_tier": True,  "free_tier_limits": "100 searches/mo free", "price_input_1m": None, "price_output_1m": None, "price_notes": "$50/mo 5k searches"},
    "DuckDuckGo (free)":    {"free_tier": True,  "free_tier_limits": "Unlimited, no key, rate limited", "price_input_1m": 0.00, "price_output_1m": 0.00, "price_notes": "Free always; no official API"},
}

# Routing tags for AI Scout — which services are safe to offload to for free
ROUTING_TAGS = {
    "Gemini 2.5 Flash":     ["free-offload", "batch", "triage", "classification"],
    "Gemini 2.5 Pro":       ["free-offload", "long-context", "analysis"],
    "Gemini Embedding":     ["free-offload", "embedding", "rag"],
    "nomic-embed-text":     ["free-offload", "local", "embedding", "rag"],
    "Llama 3.2":            ["free-offload", "local", "no-quota"],
    "GPT-5.4 mini":         ["subagent", "coding", "fast"],
    "Mistral Small":        ["free-offload", "general"],
    "DuckDuckGo (free)":    ["free-offload", "search"],
    "Tavily":               ["search", "ai-optimized"],
    "Whisper (local)":      ["free-offload", "local", "stt"],
    "Google TTS":           ["free-offload", "voice"],
    "Kling 1.6":            ["free-offload", "video"],
    "Hailuo MiniMax":       ["free-offload", "video"],
    "Stable Diffusion (local)": ["free-offload", "local", "image"],
    "Ideogram 2":           ["free-offload", "image", "text-in-image"],
    "Playground v3":        ["free-offload", "image"],
    "GitHub Copilot":       ["free-offload", "code"],
    "Gemini Code Assist":   ["free-offload", "code"],
    "Windsurf (fka Codeium)": ["free-offload", "code"],
}

# Apply pricing and routing data to all services
updated = 0
free_count = 0
for cat_name, services in d['categories'].items():
    for s in services:
        name = s['name']
        if name in PRICING:
            p = PRICING[name]
            s['free_tier'] = p['free_tier']
            s['free_tier_limits'] = p['free_tier_limits']
            s['price_input_per_1m'] = p['price_input_1m']
            s['price_output_per_1m'] = p['price_output_1m']
            s['price_notes'] = p['price_notes']
            updated += 1
            if p['free_tier']:
                free_count += 1
        if name in ROUTING_TAGS:
            s['routing_tags'] = ROUTING_TAGS[name]

# Upgrade schema version and add rating basis
d['_schema'] = "2.0"
d['_description'] = "AI services ranked by category with pricing and routing data. Updated daily 05:30 AM."
d['_rating_basis'] = {
    "rank": "Composite: capability quality + free tier value + studio relevance + community buzz",
    "buzz_score": "Reddit/HN/GitHub mentions in last 7 days via AI Intel agent",
    "trending": "True if buzz_score increased >50% week-over-week",
    "free_tier": "Whether service has a usable free tier (not just trial)",
    "routing_tags": "Tags used by AI Scout to identify free-offload candidates",
    "check_for_newer": "Agent should verify if a newer version exists before using this entry",
    "outdated_entry": "Original name preserved when service was renamed/versioned"
}
d['_routing_guide'] = {
    "free_offload_priority": [
        "Gemini 2.5 Flash (chat/triage - 1500 req/day)",
        "Gemini 2.5 Pro (analysis/long-context - 1500 req/day)",
        "nomic-embed-text (embedding - unlimited local)",
        "Llama 3.2 (general - unlimited local)",
        "Gemini Embedding (rag - 1500 req/day)",
        "Whisper local (STT - unlimited local)",
        "Google TTS (voice - 1M chars/mo free)",
        "Kling 1.6 (video - 166 credits/day)",
        "Stable Diffusion local (image - unlimited local)"
    ],
    "rule": "Route mechanical/batch tasks to free_offload tier first. Escalate to paid only if quality gate fails or quota exhausted."
}
d['date'] = TODAY
d['last_schema_upgrade'] = TODAY

json.dump(d, open(PATH, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

print(f"Schema upgraded to 2.0")
print(f"Services updated with pricing: {updated}")
print(f"Services with free tier: {free_count}/{updated}")
print(f"\nFree offload candidates by category:")
for cat_name, services in d['categories'].items():
    free = [s['name'] for s in services if s.get('free_tier')]
    if free:
        print(f"  {cat_name}: {', '.join(free)}")
