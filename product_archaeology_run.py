"""
product_archaeology_run.py
Extracted from product-archaeology.md spec.
Scans graveyard sources, scores via Gemini, saves to product-archaeology-results.json.
Does NOT push to whiteboard.json or mobile-inbox.json.
Output: product-archaeology-results.json (raw) + product-archaeology-scored.json (scored)
"""
import urllib.request, urllib.parse, json, re, time, os
from datetime import datetime

STUDIO  = "G:/My Drive/Projects/_studio"
OUTPUT  = STUDIO + "/product-archaeology-results.json"
SCORED  = STUDIO + "/product-archaeology-scored.json"
CONFIG  = json.load(open(STUDIO + "/studio-config.json", encoding="utf-8"))
KEY     = CONFIG.get("gemini_api_key", "")
GEMINI  = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key=" + KEY

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(ts + " " + msg)

def fetch(url, timeout=12, headers=None):
    h = {"User-Agent": "ProductArchaeologyBot/1.0"}
    if headers: h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def gather_graveyard():
    results = []

    # 1. Killed by Google
    try:
        content = fetch("https://killedbygoogle.com", timeout=10).decode("utf-8", errors="ignore")
        products = re.findall(r'"name":"([^"]+)"', content)
        dates    = re.findall(r'"dateClose":"([^"]+)"', content)
        for name, date in zip(products, dates):
            results.append({
                "product_name": name, "category": "google_killed",
                "source": "killedbygoogle.com", "killed_date": date,
                "why_failed": "Google acquisition/shutdown"
            })
        log("KilledByGoogle: " + str(len(products)) + " products")
    except Exception as e:
        log("KilledByGoogle ERROR: " + str(e)[:60])

    # 2. Reddit discontinued communities
    subreddits = ["shutdownsaddened", "discontinued", "DeadApps"]
    for sub in subreddits:
        url = "https://www.reddit.com/r/" + sub + "/top.json?limit=50&t=all"
        try:
            data = json.loads(fetch(url, headers={"User-Agent": "ProductArchBot/1.0"}))
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                pd = post.get("data", {})
                results.append({
                    "product_name": pd.get("title", "")[:80],
                    "source": "reddit.com/r/" + sub,
                    "category": "discontinued_product",
                    "description": pd.get("selftext", "")[:200],
                    "upvotes": pd.get("score", 0)
                })
            log("r/" + sub + ": " + str(len(posts)) + " posts")
            time.sleep(2)
        except Exception as e:
            log("r/" + sub + " ERROR: " + str(e)[:60])

    # 3. Wayback CDX — cancelled Kickstarter campaigns
    patterns = ["kickstarter.com/projects/*/updates*cancel*"]
    for pattern in patterns:
        encoded = urllib.parse.quote(pattern)
        url = ("http://web.archive.org/cdx/search/cdx?url=" + encoded +
               "&output=json&fl=original,timestamp&limit=50&collapse=urlkey&from=20150101")
        try:
            rows = json.loads(fetch(url, timeout=15))
            for row in rows[1:]:
                results.append({
                    "product_name": row[0].split("/")[-2] if "/" in row[0] else row[0],
                    "source": row[0], "category": "crowdfunding_failed"
                })
            log("Wayback Kickstarter: " + str(len(rows)-1) + " results")
            time.sleep(1)
        except Exception as e:
            log("Wayback ERROR: " + str(e)[:60])

    return results

def score_items(results):
    scored = []
    log("Scoring top 20 via Gemini...")
    for item in results[:20]:
        prompt = (
            "Product archaeology analysis. Dead/failed product: " + item["product_name"] +
            "\nCategory: " + item.get("category", "unknown") +
            "\nSource: " + item.get("source", "") +
            "\nReturn ONLY valid JSON (no markdown):\n"
            '{"market_void_exists":true,"2026_viability":"HIGH/MEDIUM/LOW",'
            '"why_could_work_now":"one sentence","market_size":"LARGE/MEDIUM/SMALL/NICHE",'
            '"build_effort":5,"revenue_potential":5,"total_score":5,'
            '"whiteboard_priority":"PUSH_UP/NEUTRAL/KILL"}'
        )
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(GEMINI, data=payload,
                                       headers={"Content-Type": "application/json"}), timeout=15)
            text = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.replace("```json", "").replace("```", "").strip()
            score = json.loads(text)
            item["score"] = score
            item["scored_at"] = datetime.now().isoformat()
            priority = score.get("whiteboard_priority", "NEUTRAL")
            total    = score.get("total_score", "?")
            log("  [" + priority + "] " + item["product_name"][:45] + ": " + str(total) + "/10")
            scored.append(item)
        except Exception as e:
            log("  SCORE ERROR: " + item["product_name"][:40] + " — " + str(e)[:50])
        time.sleep(1)
    return scored

def main():
    log("Product Archaeology starting")

    # Load existing results (append-only)
    existing = []
    if os.path.exists(OUTPUT):
        try:
            raw = json.load(open(OUTPUT, encoding="utf-8"))
            existing = raw.get("results", raw) if isinstance(raw, dict) else raw
        except: pass
    existing_names = {r.get("product_name","").lower() for r in existing}

    # Gather new results
    new_results = gather_graveyard()
    added = [r for r in new_results if r.get("product_name","").lower() not in existing_names]
    all_results = existing + added
    log("New items found: " + str(len(added)) + " | Total: " + str(len(all_results)))

    # Save raw results
    json.dump({"count": len(all_results), "updated": datetime.now().isoformat(),
               "results": all_results},
              open(OUTPUT, "w", encoding="utf-8"), indent=2)
    log("Saved to product-archaeology-results.json")

    # Score new items (top 20 unscored)
    unscored = [r for r in all_results if not r.get("score")][:20]
    if unscored and KEY:
        scored = score_items(unscored)
        json.dump({"count": len(scored), "updated": datetime.now().isoformat(),
                   "results": scored},
                  open(SCORED, "w", encoding="utf-8"), indent=2)
        log("Scored " + str(len(scored)) + " items — saved to product-archaeology-scored.json")
    else:
        log("Skipping score pass (no API key or nothing new to score)")

    log("Product Archaeology complete")

if __name__ == "__main__":
    main()
