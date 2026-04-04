"""
vintage_agent.py
Converted from Claude call to Gemini Flash free tier.
Checks which decade profiles are missing or incomplete, fills them via Gemini.
Output: vintage/[decade]-profile.json for each decade 1920s-2010s
"""

# EXPECTED_RUNTIME_SECONDS: 300
import json, os, urllib.request, time
from datetime import datetime

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

# Bezos Rule: circuit breaker constant
MAX_CONSECUTIVE_FAILURES = 3

STUDIO   = "G:/My Drive/Projects/_studio"
VINT_DIR = STUDIO + "/vintage"
CONFIG   = json.load(open(STUDIO + "/studio-config.json", encoding="utf-8"))
KEY      = CONFIG.get("gemini_api_key", "")
GEMINI   = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key=" + KEY
LOG_PATH = STUDIO + "/scheduler/logs/overnight-vintage-agent.log"

DECADES  = ["1920s","1930s","1940s","1950s","1960s","1970s","1980s","1990s","2000s","2010s"]

REQUIRED = ["slang","concerns","aspirations","fashion","food","entertainment",
            "technology","defining_products","failed_products",
            "ebay_hot_now","ebay_sleepers","character_voice","story_accuracy"]

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = ts + " " + msg
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except: pass

def needs_fill(decade):
    path = VINT_DIR + "/" + decade + "-profile.json"
    if not os.path.exists(path): return True
    try:
        d = json.load(open(path, encoding="utf-8"))
        return any(k not in d for k in REQUIRED)
    except: return True

def build_profile(decade):
    prompt = (
        "Build a complete cultural profile for the " + decade + " in the United States.\n"
        "Return ONLY valid JSON (no markdown) with these exact keys:\n"
        "slang (list of 10 common terms),\n"
        "concerns (list: top social/political worries),\n"
        "aspirations (list: what people wanted to own/achieve),\n"
        "fashion (object: mens, womens, colors),\n"
        "food (list: defining foods and drinks),\n"
        "entertainment (object: tv, music, games, movies),\n"
        "technology (object: home_tech, aspirational_tech, work_tech),\n"
        "defining_products (list: products that defined the era),\n"
        "failed_products (list of objects: name, why_failed, modern_gap),\n"
        "ebay_hot_now (list: trending vintage items from this decade),\n"
        "ebay_sleepers (list: undervalued items worth watching),\n"
        "character_voice (string: how someone from this era talks and thinks),\n"
        "story_accuracy (list: what did NOT exist yet that writers often get wrong)"
    )
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    r = urllib.request.urlopen(
        urllib.request.Request(GEMINI, data=payload,
                               headers={"Content-Type": "application/json"}), timeout=30)
    text = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["text"].strip()
    text = text.replace("```json","").replace("```","").strip()
    return json.loads(text)

@hamilton_watchdog("vintage_agent", expected_seconds=300)
def main():
    log("Vintage Agent starting")
    os.makedirs(VINT_DIR, exist_ok=True)

    if not KEY:
        log("ERROR: no gemini_api_key in studio-config.json")
        return

    filled = 0
    skipped = 0
    for decade in DECADES:
        if not needs_fill(decade):
            log("  " + decade + ": OK (complete)")
            skipped += 1
            continue
        log("  " + decade + ": filling profile...")
        try:
            profile = build_profile(decade)
            profile["decade"]     = decade
            profile["updated_at"] = datetime.now().isoformat()
            profile["source"]     = "gemini-2.0-flash"
            path = VINT_DIR + "/" + decade + "-profile.json"
            json.dump(profile, open(path, "w", encoding="utf-8"), indent=2)
            log("  " + decade + ": saved (" + str(len(profile)) + " keys)")
            filled += 1
            time.sleep(3)  # rate limit
        except Exception as e:
            log("  " + decade + " ERROR: " + str(e)[:80])
            if "429" in str(e) or "quota" in str(e).lower():
                log("  Rate limit — pausing 60s")
                time.sleep(60)

    # Build combined eBay intelligence file
    try:
        ebay_intel = {"hot": [], "sleepers": [], "gaps": [], "updated": datetime.now().isoformat()}
        for decade in DECADES:
            path = VINT_DIR + "/" + decade + "-profile.json"
            if os.path.exists(path):
                d = json.load(open(path, encoding="utf-8"))
                for item in d.get("ebay_hot_now", []):
                    ebay_intel["hot"].append({"decade": decade, "item": item})
                for item in d.get("ebay_sleepers", []):
                    ebay_intel["sleepers"].append({"decade": decade, "item": item})
                for fp in d.get("failed_products", []):
                    if fp.get("modern_gap"):
                        ebay_intel["gaps"].append({"decade": decade, **fp})
        json.dump(ebay_intel, open(VINT_DIR + "/ebay-vintage-intel.json", "w", encoding="utf-8"), indent=2)
        log("eBay intel file updated: " + str(len(ebay_intel["hot"])) + " hot, " +
            str(len(ebay_intel["sleepers"])) + " sleepers, " + str(len(ebay_intel["gaps"])) + " gaps")
    except Exception as e:
        log("eBay intel ERROR: " + str(e)[:60])

    log("Vintage Agent complete: " + str(filled) + " filled, " + str(skipped) + " already complete")

    # Heartbeat
    import sys as _sys; _sys.path.insert(0, STUDIO)
    try:
        from utilities.heartbeat import write as hb_write
        hb_write('vintage-agent', 'clean', 'filled=' + str(filled) + ' skipped=' + str(skipped))
    except Exception as e: log('[heartbeat] ' + str(e)[:60])

if __name__ == "__main__":
    main()
