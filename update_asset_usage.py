import re, json
from datetime import datetime, timezone, timedelta

STUDIO = "G:/My Drive/Projects/_studio"

def load_json(f, default):
    try: return json.load(open(STUDIO + "/" + f, encoding="utf-8"))
    except: return default

def count_usage_from_logs():
    """Count actual API usage from available logs this month."""
    usage = {}
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_str = now.strftime("%Y-%m")

    # Count from heartbeat-log entries this month
    hb = load_json("heartbeat-log.json", [])
    hb_entries = hb if isinstance(hb, list) else hb.get("entries", [])
    for entry in hb_entries:
        date_str = entry.get("date","")[:7]
        if date_str == month_str:
            agent = entry.get("agent","")
            if "ai-intel" in agent:
                usage["youtube-data-v3"] = usage.get("youtube-data-v3", 0) + 700  # 7 queries x 100 units
            if "ai-services" in agent:
                usage["youtube-data-v3"] = usage.get("youtube-data-v3", 0) + 10

    # Count Claude status entries this month
    try:
        lines = open(STUDIO + "/claude-status.txt", encoding="utf-8").readlines()
        claude_calls = sum(1 for l in lines if month_str in l and "AI-INTEL" in l)
        or_calls = sum(1 for l in lines if month_str in l and "SESSION" in l)
        if claude_calls > 0: usage["anthropic-claude"] = claude_calls
        if or_calls > 0: usage["openrouter"] = or_calls
    except: pass

    # Count supervisor inbox items as Supabase writes
    try:
        inbox = load_json("supervisor-inbox.json", {"items": []})
        items = inbox.get("items", inbox) if isinstance(inbox, dict) else inbox
        supabase_writes = sum(1 for i in items
                              if isinstance(i, dict) and i.get("date","")[:7] == month_str)
        if supabase_writes: usage["supabase"] = supabase_writes
    except: pass

    return usage

def run():
    path = STUDIO + "/asset-log.json"
    data = load_json("asset-log.json", {"assets": []})
    usage_counts = count_usage_from_logs()
    now_str = datetime.now().strftime("%Y-%m-%d")
    now_month = datetime.now().strftime("%Y-%m")

    for asset in data.get("assets", []):
        aid = asset.get("id","")
        # Update last_used to today for active APIs
        if aid in ["anthropic-claude","gemini","youtube-data-v3","openrouter","ollama",
                   "ebay-api","supabase","adzuna"]:
            if not asset.get("last_used") or asset["last_used"] < now_str[:7]:
                asset["last_used"] = now_str

        # Apply real usage counts where available
        if aid == "youtube-data-v3" and aid in usage_counts:
            asset.setdefault("usage_this_month", {})
            asset["usage_this_month"]["units"] = usage_counts[aid]
            asset["usage_this_month"]["calls"] = usage_counts[aid] // 100
        if aid == "anthropic-claude" and aid in usage_counts:
            asset.setdefault("usage_this_month", {})
            asset["usage_this_month"]["calls"] = usage_counts.get(aid, 0)
        if aid == "supabase" and aid in usage_counts:
            asset.setdefault("usage_this_month", {})
            asset["usage_this_month"]["calls"] = usage_counts.get(aid, 0)

        # AI Intel runs are eBay API indicator too
        hb = load_json("heartbeat-log.json", [])
        hb_entries = hb if isinstance(hb, list) else hb.get("entries", [])
        ebay_runs = sum(1 for e in hb_entries
                       if isinstance(e, dict) and e.get("agent","") == "ebay-agent"
                       and e.get("date","")[:7] == now_month)
        if aid == "ebay-api" and ebay_runs:
            asset.setdefault("usage_this_month", {})
            asset["usage_this_month"]["calls"] = ebay_runs

    data["_last_updated"] = now_str
    json.dump(data, open(path, "w", encoding="utf-8"), indent=2)
    print("asset-log.json updated with real usage counts")
    print("Usage found: " + str(usage_counts))

run()
