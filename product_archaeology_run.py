"""
product_archaeology_run.py
Extracted from product-archaeology.md spec.
Scans graveyard sources, scores via AI Gateway (free tier routing).
Does NOT push to whiteboard.json or mobile-inbox.json.
Output: product-archaeology-results.json (raw) + product-archaeology-scored.json (scored)
"""
import urllib.request, urllib.parse, json, re, time, os, sys
sys.path.insert(0, "G:/My Drive/Projects/_studio")
from datetime import datetime
from ai_gateway import score as gw_score

STUDIO  = "G:/My Drive/Projects/_studio"
OUTPUT  = STUDIO + "/product-archaeology-results.json"
SCORED  = STUDIO + "/product-archaeology-scored.json"

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
    log("Scoring top 20 via AI Gateway (free tier with fallback)...")
    MAX_CONSECUTIVE_FAILURES = 3
    consecutive_failures = 0
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
        try:
            r = gw_score(prompt, max_tokens=200)
            if not r.success:
                raise Exception(r.error or "gateway returned no response")
            # Robust JSON extraction — handles markdown fences, leading text, special chars
            text = r.text
            text = text.replace("```json", "").replace("```", "").strip()
            # Find the JSON object — extract from first { to last }
            start = text.find("{")
            end   = text.rfind("}")
            if start >= 0 and end > start:
                text = text[start:end+1]
            # Replace smart quotes and common unicode issues
            text = (text.replace("\u201c", '"').replace("\u201d", '"')
                        .replace("\u2018", "'").replace("\u2019", "'")
                        .replace("\u2013", "-").replace("\u2014", "-"))
            score = json.loads(text)
            item["score"] = score
            item["scored_at"] = datetime.now().isoformat()
            item["scored_by"] = f"{r.provider}/{r.model}"
            priority = score.get("whiteboard_priority", "NEUTRAL")
            total    = score.get("total_score", "?")
            log("  [" + priority + "] " + item["product_name"][:45] + ": " + str(total) + "/10 via " + r.provider)
            scored.append(item)
            consecutive_failures = 0
        except Exception as e:
            consecutive_failures += 1
            log("  SCORE ERROR: " + item["product_name"][:40] + " — " + str(e)[:50])
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                log("  CIRCUIT BREAKER: " + str(MAX_CONSECUTIVE_FAILURES) +
                    " consecutive failures — aborting score pass to avoid API waste")
                break
        time.sleep(1)
    return scored

def main():
    log("Product Archaeology starting")

    # Determine mode: collection (runs anytime) vs scoring (only 6AM-11PM)
    hour = datetime.now().hour
    run_scoring = (6 <= hour <= 23)  # skip Gemini scoring overnight — unreliable 1AM-5AM

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

    # Score new items — only daytime (Gemini unreliable 1AM-5AM)
    unscored = [r for r in all_results if not r.get("score")][:20]
    if unscored and run_scoring:
        scored_items = score_items(unscored)
        json.dump({"count": len(scored_items), "updated": datetime.now().isoformat(),
                   "results": scored_items},
                  open(SCORED, "w", encoding="utf-8"), indent=2)
        log("Scored " + str(len(scored_items)) + " items — saved to product-archaeology-scored.json")

        # Auto-promote: items scored 7+ with PUSH_UP → whiteboard.json
        promote = [r for r in scored_items
                   if r.get("score",{}).get("total_score",0) >= 7
                   and r.get("score",{}).get("whiteboard_priority") == "PUSH_UP"]
        if promote:
            wb_path = STUDIO + "/whiteboard.json"
            try:
                wb = json.load(open(wb_path, encoding="utf-8"))
                existing_titles = {i.get("title","").lower() for i in wb.get("items",[])}
                added_to_wb = 0
                for r in promote:
                    title = r.get("product_name","")
                    if title.lower() not in existing_titles:
                        wb["items"].append({
                            "id": "pa-" + str(int(time.time())) + "-" + str(added_to_wb),
                            "title": title,
                            "description": r.get("description","")[:200],
                            "type": "product_archaeology",
                            "source": r.get("source",""),
                            "why_failed": r.get("why_failed",""),
                            "tags": ["product_archaeology"],
                            "added_at": datetime.now().isoformat()
                        })
                        existing_titles.add(title.lower())
                        added_to_wb += 1
                if added_to_wb:
                    json.dump(wb, open(wb_path, "w", encoding="utf-8"), indent=2)
                    log("Promoted " + str(added_to_wb) + " items to whiteboard.json")
            except Exception as e:
                log("Whiteboard promote error: " + str(e)[:60])
    elif unscored and not run_scoring:
        log("Skipping score pass — hour " + str(hour) + " outside 6AM-11PM window")
    else:
        log("Nothing new to score")

    log("Product Archaeology complete")

    # Heartbeat
    import sys as _sys; _sys.path.insert(0, STUDIO)
    try:
        from utilities.heartbeat import write as hb_write
        hb_write('product-archaeology', 'clean',
                 'added=' + str(len(added)) + ' total=' + str(len(all_results)))
    except Exception as e: log('[heartbeat] ' + str(e)[:60])

if __name__ == "__main__":
    main()
