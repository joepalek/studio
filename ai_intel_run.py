
MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule

# EXPECTED_RUNTIME_SECONDS: 300
# ai_intel_run.py - AI Intel daily scraper v2
# Sources: YouTube, Reddit (5 subs), HackerNews, Anthropic news, OpenAI RSS,
#          GitHub Trending, arXiv AI abstracts
# Schedule: 05:00 AM daily via Task Scheduler \Studio\AgentAIIntel

import urllib.request, urllib.parse, json, re, html, time, os
from datetime import datetime, timedelta, timezone

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

STUDIO = "G:/My Drive/Projects/_studio"
DAILY_FILE   = STUDIO + "/ai-intel-daily.json"
SUMMARY_FILE = STUDIO + "/ai-intel-summary.txt"
INBOX_FILE   = STUDIO + "/supervisor-inbox.json"
CONFIG_FILE  = STUDIO + "/studio-config.json"
VAULT_FILE   = STUDIO + "/.studio-vault.json"

now = datetime.now(timezone.utc)
cutoff_24h = now - timedelta(hours=24)
cutoff_unix = int(cutoff_24h.timestamp())
today_str = now.strftime("%Y-%m-%d")
now_iso   = now.strftime("%Y-%m-%dT%H:%M:%SZ")

# Load API key from vault (primary) or config (fallback)
def get_youtube_key():
    """Load YouTube API key from vault, falling back to studio-config."""
    # Try vault first
    if os.path.exists(VAULT_FILE):
        try:
            vault = json.load(open(VAULT_FILE, encoding="utf-8"))
            key = vault.get("youtube_api_key", "")
            if key:
                return key
        except Exception:
            pass
    # Fallback to studio-config
    if os.path.exists(CONFIG_FILE):
        try:
            cfg = json.load(open(CONFIG_FILE, encoding="utf-8"))
            return cfg.get("youtube_api_key", "")
        except Exception:
            pass
    return ""

YOUTUBE_KEY = get_youtube_key()

AI_KW = [
    "ai", "llm", "claude", "gpt", "anthropic", "openai", "gemini",
    "machine learning", "neural", "model", "agent", "automation",
    "mistral", "ollama", "langchain", "copilot", "multimodal",
    "rag", "inference", "transformer", "diffusion", "deepmind",
    "hugging face", "stable diffusion", "midjourney", "sora",
    "reasoning model", "fine-tun", "embedding", "vector", "prompt"
]

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; StudioIntelAgent/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def ai_rel(text):
    return any(k in text.lower() for k in AI_KW)

def score_item(title, snippet):
    text = (title + " " + snippet).lower()
    s = 8 if any(w in text for w in ["deprecat","shutdown","breaking","price change","rate limit"]) else \
        6 if any(w in text for w in ["update","new version","changed","migration","policy"]) else \
        4 if any(w in text for w in ["anthropic","openai","claude","gemini","gpt"]) else 2
    v = 8 if any(w in text for w in ["free","open source","open-source","cheaper","faster","replaces","free tier"]) else \
        6 if any(w in text for w in ["new feature","capability","improvement","workflow","tool"]) else \
        5 if "research" in text else 3
    n = 9 if any(w in text for w in ["launch","release","announce","introduce","new model","first"]) else \
        7 if any(w in text for w in ["update","version","upgrade","acqui"]) else \
        5 if any(w in text for w in ["study","paper","benchmark","research"]) else 3
    r = 9 if any(w in text for w in ["claude","anthropic","agent","ebay","automation","scraping","workflow","ollama"]) else \
        7 if any(w in text for w in ["openai","gpt","llm","model","api","openrouter","gemini"]) else \
        5 if "ai" in text else 3
    total = s + v + n + r
    tier = "HIGH_PRIORITY" if total >= 28 else "WORTH_READING" if total >= 20 else "LOGGED_ONLY"
    return {"stability": s, "value": v, "novelty": n, "relevance": r, "total": total}, tier

raw = []
sa = 0  # sources attempted
ss = 0  # sources succeeded

# SOURCE 1: YOUTUBE
print("Fetching YouTube...")
sa += 1
yt_count = 0
if YOUTUBE_KEY:
    try:
        after_iso = cutoff_24h.strftime("%Y-%m-%dT%H:%M:%SZ")
        _consecutive_failures = 0
        for q in ["AI news today","AI tools 2026","Claude Anthropic update",
                  "ChatGPT OpenAI update","AI automation workflow","new AI model release","LLM breakthrough"]:
            params = urllib.parse.urlencode({
                "part":"snippet","q":q,"type":"video","publishedAfter":after_iso,
                "order":"relevance","maxResults":5,"key":YOUTUBE_KEY
            })
            data = json.loads(fetch("https://www.googleapis.com/youtube/v3/search?" + params, timeout=15))
            for item in data.get("items", []):
                s = item["snippet"]
                title = s.get("title","")
                desc  = s.get("description","")[:300]
                vid_id = item["id"].get("videoId","")
                if not title or not ai_rel(title + desc):
                    continue
                raw.append({"source":"youtube","title":title,
                            "url":"https://www.youtube.com/watch?v=" + vid_id,
                            "published":s.get("publishedAt",""),
                            "snippet":desc,"channel":s.get("channelTitle","")})
                yt_count += 1
            time.sleep(0.3)
        ss += 1
        print("  YouTube: OK - " + str(yt_count) + " AI videos")
    except Exception as e:
        print("  YouTube: FAIL - " + str(e)[:80])
else:
    print("  YouTube: SKIPPED - no api key")

# SOURCE 2: REDDIT
print("Fetching Reddit...")
for sub in ["artificial","MachineLearning","ChatGPT","ClaudeAI","LocalLLaMA"]:
    sa += 1
    try:
        data = json.loads(fetch("https://www.reddit.com/r/" + sub + "/new.json?limit=25&t=day"))
        added = 0
        for p in data["data"]["children"]:
            d = p["data"]
            if d["created_utc"] < cutoff_unix:
                continue
            t = html.unescape(d.get("title",""))
            snip = html.unescape(d.get("selftext","")[:300])
            if not ai_rel(t + snip):
                continue
            raw.append({"source":"reddit/r/"+sub,"title":t,
                        "url":"https://reddit.com" + d.get("permalink",""),
                        "published":datetime.fromtimestamp(d["created_utc"],tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "snippet":snip})
            added += 1
        ss += 1
        print("  r/" + sub + ": OK (" + str(added) + " items)")
    except Exception as e:
        print("  r/" + sub + ": FAIL - " + str(e)[:60])
    time.sleep(0.5)

# SOURCE 3: HACKERNEWS
print("Fetching HackerNews...")
sa += 1
try:
    data = json.loads(fetch("https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=100&numericFilters=created_at_i>" + str(cutoff_unix)))
    hn_count = 0
    for h in data["hits"]:
        t = h.get("title","")
        if t and ai_rel(t):
            raw.append({"source":"hackernews","title":t,
                        "url":h.get("url") or "https://news.ycombinator.com/item?id=" + str(h.get("objectID","")),
                        "published":h.get("created_at",""),"snippet":""})
            hn_count += 1
    ss += 1
    print("  HackerNews: OK - " + str(hn_count) + " AI items")
except Exception as e:
    print("  HackerNews: FAIL - " + str(e)[:60])

# SOURCE 4: ANTHROPIC NEWS
print("Fetching Anthropic news...")
sa += 1
try:
    content = fetch("https://www.anthropic.com/news").decode("utf-8", errors="replace")
    seen_hrefs = set()
    ant_count = 0
    for m in re.finditer(r'href="(/news/([^"?#]{5,}))"', content):
        href = m.group(1)
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        start = max(0, m.start() - 200)
        end = min(len(content), m.end() + 200)
        nearby = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', content[start:end])).strip()
        title_m = re.search(r'([A-Z][^.!?]{20,120})', nearby)
        title = title_m.group(1).strip() if title_m else href.split("/")[-1].replace("-"," ").title()
        raw.append({"source":"anthropic-news","title":title,
                    "url":"https://www.anthropic.com" + href,
                    "published":today_str,"snippet":""})
        ant_count += 1
    ss += 1
    print("  Anthropic news: OK - " + str(ant_count) + " articles")
except Exception as e:
    print("  Anthropic news: FAIL - " + str(e)[:60])

# SOURCE 5: OPENAI RSS
print("Fetching OpenAI RSS...")
sa += 1
try:
    content = fetch("https://openai.com/blog/rss.xml").decode("utf-8", errors="replace")
    oai_count = 0
    for item in re.findall(r"<item>(.*?)</item>", content, re.DOTALL)[:30]:
        tm = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item)
        lm = re.search(r"<link>(.*?)</link>", item)
        dm = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.DOTALL)
        t = html.unescape((tm.group(1) or "").strip()) if tm else ""
        l = (lm.group(1) or "").strip() if lm else ""
        snip = html.unescape(re.sub(r"<[^>]+>","", (dm.group(1) or ""))[:300]) if dm else ""
        if t:
            raw.append({"source":"openai-blog","title":t,"url":l,"published":"","snippet":snip})
            oai_count += 1
    ss += 1
    print("  OpenAI RSS: OK - " + str(oai_count) + " items")
except Exception as e:
    print("  OpenAI RSS: FAIL - " + str(e)[:60])

# SOURCE 6: GITHUB TRENDING
print("Fetching GitHub Trending...")
sa += 1
try:
    content = fetch("https://github.com/trending?since=daily", timeout=15).decode("utf-8", errors="replace")
    gh_count = 0
    seen_repos = set()
    for m in re.finditer(r'href="/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"', content):
        repo_path = m.group(1)
        if "/" not in repo_path or repo_path in seen_repos:
            continue
        seen_repos.add(repo_path)
        if not ai_rel(repo_path):
            continue
        raw.append({"source":"github-trending","title":repo_path,
                    "url":"https://github.com/" + repo_path,
                    "published":today_str,"snippet":repo_path})
        gh_count += 1
        if gh_count >= 20:
            break
    ss += 1
    print("  GitHub Trending: OK - " + str(gh_count) + " AI repos")
except Exception as e:
    print("  GitHub Trending: FAIL - " + str(e)[:60])

# SOURCE 7: ARXIV
print("Fetching arXiv...")
sa += 1
try:
    url = ("https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG"
           "&sortBy=submittedDate&sortOrder=descending&max_results=30")
    content = fetch(url, timeout=20).decode("utf-8", errors="replace")
    ax_count = 0
    for entry in re.findall(r"<entry>(.*?)</entry>", content, re.DOTALL):
        tm = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        lm = re.search(r"<id>(.*?)</id>", entry)
        dm = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        pub_m = re.search(r"<published>(.*?)</published>", entry)
        t = re.sub(r"\s+"," ",(tm.group(1) or "").strip()) if tm else ""
        l = (lm.group(1) or "").strip() if lm else ""
        snip = re.sub(r"\s+"," ",(dm.group(1) or "").strip())[:300] if dm else ""
        pub = (pub_m.group(1) or "")[:10] if pub_m else ""
        if pub and pub < cutoff_24h.strftime("%Y-%m-%d"):
            continue
        if t and ai_rel(t + snip):
            raw.append({"source":"arxiv","title":t,"url":l,"published":pub,"snippet":snip})
            ax_count += 1
    ss += 1
    print("  arXiv: OK - " + str(ax_count) + " papers")
except Exception as e:
    print("  arXiv: FAIL - " + str(e)[:60])

print("\nRaw: " + str(len(raw)) + " items from " + str(ss) + "/" + str(sa) + " sources")

# DEDUPLICATE
seen_u, seen_t, deduped = set(), set(), []
for item in raw:
    uk = item["url"].rstrip("/")
    tk = item["title"][:60].lower().strip()
    if uk in seen_u or tk in seen_t:
        continue
    seen_u.add(uk)
    seen_t.add(tk)
    deduped.append(item)
print("After dedup: " + str(len(deduped)) + " unique items")

# SCORE
scored = []
for item in deduped:
    sc, tier = score_item(item["title"], item.get("snippet",""))
    entry = {"title":item["title"],"url":item["url"],"source":item["source"],
             "published":item.get("published",""),"scores":sc,"tier":tier,
             "dependency_escalated":False,"affected_projects":[],
             "summary":item["title"][:80] + " via " + item["source"]}
    if item["source"] == "youtube" and item.get("channel"):
        entry["channel"] = item["channel"]
    scored.append(entry)

high  = [i for i in scored if i["tier"] == "HIGH_PRIORITY"]
worth = [i for i in scored if i["tier"] == "WORTH_READING"]
logged = [i for i in scored if i["tier"] == "LOGGED_ONLY"]
yt_surfaced = [i for i in high + worth if i["source"] == "youtube"]
print("Tiers: " + str(len(high)) + " HIGH / " + str(len(worth)) + " WORTH / " + str(len(logged)) + " LOGGED")
print("YouTube in digest: " + str(len(yt_surfaced)))

# WRITE ai-intel-daily.json
run_entry = {"date":today_str,"generated_at":now_iso,"sources_attempted":sa,
             "sources_succeeded":ss,"items_found":len(scored),
             "youtube_videos":len([i for i in scored if i["source"]=="youtube"]),
             "high_priority":high,"worth_reading":worth,"logged_only":logged}
try:
    daily = json.load(open(DAILY_FILE, encoding="utf-8"))
except Exception:
    daily = {"_schema":"1.0","_description":"Daily AI intelligence feed - 14 day rolling window",
             "_note":"Written by ai-intel-agent at 05:00 AM daily.","runs":[]}
cutoff_14d = (now - timedelta(days=14)).strftime("%Y-%m-%d")
daily["runs"] = [r for r in daily.get("runs",[]) if r.get("date","") >= cutoff_14d]
daily["runs"].append(run_entry)
daily["generated"] = now_iso
daily["high_priority"] = high[:5]  # top 5 for sidebar quick access
json.dump(daily, open(DAILY_FILE,"w",encoding="utf-8"), indent=2)
print("Written: ai-intel-daily.json")

# WRITE ai-intel-summary.txt
lines = [
    "AI INTEL - " + today_str,
    "Generated: " + now_iso,
    "Sources: " + str(ss) + "/" + str(sa) + " OK | "
    + str(len(high)) + " HIGH / " + str(len(worth)) + " WORTH / " + str(len(logged)) + " LOGGED"
    + " | YouTube: " + str(len(yt_surfaced)) + " videos surfaced","",
]
lines.append("HIGH PRIORITY (" + str(len(high)) + "):") if high else lines.append("HIGH PRIORITY: None today.")
for i in high[:10]:
    lines.append("  * " + i["title"][:90] + " | score:" + str(i["scores"]["total"]) + " | " + i["url"])
lines.append("")
if worth:
    lines.append("WORTH READING (" + str(len(worth)) + "):")
    for i in worth[:10]:
        lines.append("  * " + i["title"][:90] + " | score:" + str(i["scores"]["total"]) + " | " + i["url"])
if yt_surfaced:
    lines += ["","YOUTUBE PICKS:"]
    for i in yt_surfaced[:5]:
        ch = i.get("channel","")
        lines.append("  * " + i["title"][:80] + (" [" + ch + "]" if ch else "") + " | " + i["url"])
lines += ["","DEPENDENCY FLAGS: none"]
open(SUMMARY_FILE,"w",encoding="utf-8").write("\n".join(lines))
print("Written: ai-intel-summary.txt")

# SUPERVISOR INBOX -- handle both list and dict formats
if high:
    try:
        raw_inbox = json.load(open(INBOX_FILE, encoding="utf-8"))
    except Exception:
        raw_inbox = {"items": []}
    # Normalize: supervisor-inbox.json is a dict with "items" key
    if isinstance(raw_inbox, list):
        raw_inbox = {"items": raw_inbox}
    if "items" not in raw_inbox:
        raw_inbox["items"] = []
    raw_inbox["items"].append({
        "id": "ai-intel-" + today_str, "source": "ai-intel-agent",
        "type": "intel", "urgency": "WARN",
        "title": "AI Intel - " + str(len(high)) + " HIGH PRIORITY - " + today_str,
        "finding": high[0]["title"] + ". See ai-intel-summary.txt.",
        "status": "PENDING", "date": now_iso,
    })
    json.dump(raw_inbox, open(INBOX_FILE,"w",encoding="utf-8"), indent=2)
    print("Supervisor inbox updated.")

# HEARTBEAT
try:
    hb_path = STUDIO + "/heartbeat-log.json"
    try:
        hb = json.load(open(hb_path, encoding="utf-8"))
    except Exception:
        hb = []
    if isinstance(hb, list):
        hb = {"_schema": "1.0", "entries": hb}
    if "entries" not in hb:
        hb["entries"] = []
    hb["entries"].append({
        "date": now_iso, "agent": "ai-intel-agent", "status": "clean",
        "notes": (str(len(high)) + " high / " + str(len(worth)) + " worth / "
                  + str(len(logged)) + " logged -- "
                  + str(ss) + "/" + str(sa) + " sources"
                  + " -- YouTube: " + str(len(yt_surfaced)) + " videos")
    })
    json.dump(hb, open(hb_path,"w",encoding="utf-8"), indent=2)
except Exception as e:
    print("Heartbeat write failed: " + str(e)[:60])

# STATUS
with open(STUDIO + "/claude-status.txt","a",encoding="utf-8") as f:
    f.write("[AI-INTEL] " + now_iso + " -- "
            + str(len(high)) + " HIGH / " + str(len(worth)) + " WORTH"
            + " -- YouTube: " + str(len(yt_surfaced)) + " videos"
            + " -- " + str(ss) + "/" + str(sa) + " sources\n")

print("\nDONE. " + str(len(high)) + " HIGH / " + str(len(worth)) + " WORTH / " + str(len(logged)) + " LOGGED")
print("YouTube videos surfaced: " + str(len(yt_surfaced)))
