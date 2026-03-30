"""
ai_intel_run.py - Manual AI Intel scrape (free sources only)
Scrapes Reddit, HackerNews, OpenAI RSS, Anthropic news page
Writes: ai-intel-daily.json, ai-intel-summary.txt, supervisor-inbox.json
"""
import urllib.request
import json
import re
import html
from datetime import datetime, timedelta, timezone

STUDIO_ROOT = "G:/My Drive/Projects/_studio"
DAILY_FILE = STUDIO_ROOT + "/ai-intel-daily.json"
SUMMARY_FILE = STUDIO_ROOT + "/ai-intel-summary.txt"
INBOX_FILE = STUDIO_ROOT + "/supervisor-inbox.json"

now = datetime.now(timezone.utc)
cutoff_24h = now - timedelta(hours=24)
cutoff_unix = int(cutoff_24h.timestamp())
today_str = now.strftime("%Y-%m-%d")
now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

AI_KW = [
    "ai", "llm", "claude", "gpt", "anthropic", "openai", "gemini",
    "machine learning", "neural", "model", "agent", "automation",
    "mistral", "ollama", "langchain", "copilot", "multimodal",
    "rag", "inference", "transformer"
]

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; StudioIntelAgent/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def ai_rel(text):
    return any(k in text.lower() for k in AI_KW)

def score_item(title, snippet):
    text = (title + " " + snippet).lower()
    s = 8 if any(w in text for w in ["deprecat","shutdown","breaking","price change"]) else \
        6 if any(w in text for w in ["update","new version","changed","migration"]) else \
        4 if any(w in text for w in ["anthropic","openai","claude","gpt"]) else 2
    v = 8 if any(w in text for w in ["free","open source","cheaper","faster","replaces"]) else \
        6 if any(w in text for w in ["new feature","capability","improvement"]) else \
        5 if "workflow" in text else 3
    n = 8 if any(w in text for w in ["launch","release","announce","introduce","first","new model"]) else \
        6 if any(w in text for w in ["update","version","upgrade"]) else \
        5 if "research" in text else 3
    r = 9 if any(w in text for w in ["claude","anthropic","agent","ebay","automation","scraping","workflow"]) else \
        7 if any(w in text for w in ["openai","gpt","llm","model","api","openrouter"]) else \
        5 if "ai" in text else 3
    total = s + v + n + r
    tier = "HIGH_PRIORITY" if total >= 28 else "WORTH_READING" if total >= 20 else "LOGGED_ONLY"
    return {"stability": s, "value": v, "novelty": n, "relevance": r, "total": total}, tier

raw, sa, ss = [], 0, 0

# SOURCE 1: Reddit
print("Fetching Reddit...")
for sub in ["artificial", "MachineLearning", "ChatGPT", "ClaudeAI", "LocalLLaMA"]:
    sa += 1
    try:
        data = json.loads(fetch("https://www.reddit.com/r/" + sub + "/new.json?limit=25&t=day"))
        for p in data["data"]["children"]:
            d = p["data"]
            if d["created_utc"] < cutoff_unix:
                continue
            t = html.unescape(d.get("title", ""))
            snip = html.unescape(d.get("selftext", "")[:300])
            if not ai_rel(t + snip):
                continue
            raw.append({"source": "reddit/r/" + sub, "title": t,
                        "url": "https://reddit.com" + d.get("permalink", ""),
                        "published": datetime.utcfromtimestamp(d["created_utc"]).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "snippet": snip})
        ss += 1
        print("  r/" + sub + ": OK")
    except Exception as e:
        print("  r/" + sub + ": FAIL - " + str(e))

# SOURCE 2: HackerNews
print("Fetching HackerNews...")
sa += 1
try:
    data = json.loads(fetch(
        "https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=50&numericFilters=created_at_i>" + str(cutoff_unix)
    ))
    for h in data["hits"]:
        t = h.get("title", "")
        if t and ai_rel(t):
            raw.append({"source": "hackernews", "title": t,
                        "url": h.get("url") or "https://news.ycombinator.com/item?id=" + str(h.get("objectID", "")),
                        "published": h.get("created_at", ""), "snippet": ""})
    ss += 1
    print("  HN: OK - " + str(len([h for h in data["hits"] if ai_rel(h.get("title",""))])) + " AI items")
except Exception as e:
    print("  HN: FAIL - " + str(e))

# SOURCE 3: OpenAI RSS
print("Fetching OpenAI RSS...")
sa += 1
try:
    content = fetch("https://openai.com/blog/rss.xml").decode("utf-8", errors="replace")
    items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
    for item in items[:30]:
        tm = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item)
        lm = re.search(r"<link>(.*?)</link>", item)
        dm = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.DOTALL)
        t = html.unescape(tm.group(1).strip()) if tm else ""
        l = (lm.group(1) or "").strip() if lm else ""
        snip = html.unescape(re.sub(r"<[^>]+>", "", dm.group(1) or "")[:300]) if dm else ""
        if t:
            raw.append({"source": "openai-blog", "title": t, "url": l, "published": "", "snippet": snip})
    ss += 1
    print("  OpenAI RSS: OK - " + str(len(items)) + " items")
except Exception as e:
    print("  OpenAI RSS: FAIL - " + str(e))

# SOURCE 4: Anthropic News page (RSS is dead)
print("Fetching Anthropic news page...")
sa += 1
try:
    content = fetch("https://www.anthropic.com/news").decode("utf-8", errors="replace")
    seen2 = set()
    found = 0
    for href, text in re.findall(r'href="(/news/[^"]+)"[^>]*>[^<]*<[^>]+>([^<]{10,120})', content, re.DOTALL)[:25]:
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        if len(text) < 10 or href in seen2:
            continue
        seen2.add(href)
        raw.append({"source": "anthropic-news", "title": text,
                    "url": "https://www.anthropic.com" + href,
                    "published": today_str, "snippet": ""})
        found += 1
    ss += 1
    print("  Anthropic news: OK - " + str(found) + " items")
except Exception as e:
    print("  Anthropic news: FAIL - " + str(e))

print("Raw: " + str(len(raw)) + " items from " + str(ss) + "/" + str(sa) + " sources")

# Deduplicate
seen_u, seen_t, deduped = set(), set(), []
for item in raw:
    uk = item["url"].rstrip("/")
    tk = item["title"][:60].lower().strip()
    if uk in seen_u or tk in seen_t:
        continue
    seen_u.add(uk)
    seen_t.add(tk)
    deduped.append(item)
print("After dedup: " + str(len(deduped)))

# Score
scored = []
for item in deduped:
    sc, tier = score_item(item["title"], item["snippet"])
    scored.append({"title": item["title"], "url": item["url"], "source": item["source"],
                   "published": item["published"], "scores": sc, "tier": tier,
                   "dependency_escalated": False, "affected_projects": [],
                   "summary": item["title"][:80] + " via " + item["source"]})

high = [i for i in scored if i["tier"] == "HIGH_PRIORITY"]
worth = [i for i in scored if i["tier"] == "WORTH_READING"]
logged = [i for i in scored if i["tier"] == "LOGGED_ONLY"]
print("Tiers: " + str(len(high)) + " HIGH / " + str(len(worth)) + " WORTH / " + str(len(logged)) + " LOGGED")

# Write ai-intel-daily.json
run_entry = {"date": today_str, "generated_at": now_iso, "sources_attempted": sa,
             "sources_succeeded": ss, "items_found": len(scored),
             "high_priority": high, "worth_reading": worth, "logged_only": logged}
try:
    with open(DAILY_FILE, "r", encoding="utf-8", errors="replace") as f:
        daily = json.load(f)
except Exception:
    daily = {"_schema": "1.0", "_description": "Daily AI intelligence feed - 14 day rolling window", "runs": []}
cutoff_14d = (now - timedelta(days=14)).strftime("%Y-%m-%d")
daily["runs"] = [r for r in daily.get("runs", []) if r.get("date", "") >= cutoff_14d]
daily["runs"].append(run_entry)
with open(DAILY_FILE, "w", encoding="utf-8") as f:
    json.dump(daily, f, indent=2)
print("Written: ai-intel-daily.json")

# Write summary
lines = [
    "AI INTEL - " + today_str,
    "Generated: " + now_iso,
    "Sources: " + str(ss) + "/" + str(sa) + " OK | " + str(len(high)) + " HIGH / " + str(len(worth)) + " WORTH / " + str(len(logged)) + " LOGGED",
    "",
]
if high:
    lines.append("HIGH PRIORITY (" + str(len(high)) + "):")
    for i in high[:10]:
        lines.append("  * " + i["title"][:90] + " | score:" + str(i["scores"]["total"]) + " | " + i["url"])
else:
    lines.append("HIGH PRIORITY: None today.")
lines.append("")
if worth:
    lines.append("WORTH READING (" + str(len(worth)) + "):")
    for i in worth[:10]:
        lines.append("  * " + i["title"][:90] + " | score:" + str(i["scores"]["total"]) + " | " + i["url"])
lines += ["", "DEPENDENCY FLAGS: none"]
with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Written: ai-intel-summary.txt")

# Supervisor inbox if HIGH items
if high:
    try:
        with open(INBOX_FILE, "r", encoding="utf-8", errors="replace") as f:
            inbox = json.load(f)
    except Exception:
        inbox = []
    inbox.append({"id": "ai-intel-" + today_str, "source": "ai-intel-agent", "type": "intel",
                  "urgency": "WARN", "title": "AI Intel - " + str(len(high)) + " HIGH PRIORITY - " + today_str,
                  "finding": high[0]["title"] + ". See ai-intel-summary.txt.",
                  "status": "PENDING", "date": now_iso})
    with open(INBOX_FILE, "w", encoding="utf-8") as f:
        json.dump(inbox, f, indent=2)
    print("Supervisor inbox updated.")

print("\nDONE.")
