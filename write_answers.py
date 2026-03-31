import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().isoformat()[:19]

# Add to AI intel daily review queue
intel_path = "G:/My Drive/Projects/_studio/ai-intel-daily.json"
d = json.load(open(intel_path, encoding='utf-8', errors='replace'))

# Find today's or most recent entry to append review items
entries = d.get('entries', d.get('results', [d] if 'items' in d else []))
review_items = [
    {
        "title": "GPT-5.4 mini — review for AI Scout routing",
        "url": "https://openai.com/index/introducing-gpt-5-4-mini-and-nano/",
        "source": "manual-queue",
        "published": TODAY,
        "scores": {"stability": 8, "value": 8, "novelty": 7, "relevance": 9, "total": 32},
        "tier": "HIGH",
        "review_reason": (
            "Released Mar 17 2026. $0.75/1M in, $0.20/1M nano. "
            "2x faster than GPT-5 mini. 400K context. "
            "Subagent candidate for studio mechanical tasks (classification, extraction, ranking). "
            "Compare vs Gemini 2.5 Flash for cost routing. "
            "nano at $0.20/1M input is cheaper than Gemini 3.1 Flash-Lite."
        ),
        "dependency_escalated": True,
        "affected_projects": ["ai-scout", "auto-answer", "translation-layer", "listing-optimizer"],
        "added_by": "joe-session-2026-03-31"
    },
    {
        "title": "Zanat — CLI + MCP server for versioning AI agent skills",
        "url": "https://reddit.com/r/LocalLLaMA/comments/1s823ue/zanat_an_opensource_cli_mcp_server_to_version/",
        "source": "manual-queue",
        "published": TODAY,
        "scores": {"stability": 6, "value": 8, "novelty": 8, "relevance": 10, "total": 32},
        "tier": "HIGH",
        "review_reason": (
            "Open-source CLI + MCP server for versioning, sharing, installing AI agent skills. "
            "Studio already has /mnt/skills/ skill system with SKILL.md files. "
            "Zanat appears to be a standardization layer for exactly this pattern. "
            "Evaluate: does it align with or replace current skill architecture? "
            "Key question: does it support Windows + Claude Code?"
        ),
        "dependency_escalated": True,
        "affected_projects": ["_studio", "skill-improver"],
        "added_by": "joe-session-2026-03-31"
    }
]

# Append to most recent day entry or create new
if isinstance(d, dict) and 'items' in d:
    d['items'].extend(review_items)
elif isinstance(d, list):
    d.extend(review_items)
else:
    if 'review_queue' not in d:
        d['review_queue'] = []
    d['review_queue'].extend(review_items)

json.dump(d, open(intel_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Added {len(review_items)} items to ai-intel-daily.json review queue")
for item in review_items:
    print(f"  [{item['scores']['total']}] {item['title'][:60]}")
