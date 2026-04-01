import json, re, os
from datetime import datetime, timezone

STUDIO = "G:/My Drive/Projects/_studio"
SIDEBAR = STUDIO + "/sidebar-agent.html"

def safe_str(s):
    if not isinstance(s, str): return s
    s = s.replace("</script>", "<\\/script>").replace("`", "'")
    s = s.replace("\u2018","'").replace("\u2019","'").replace("\u201c",'"').replace("\u201d",'"')
    s = s.replace("\u2013","-").replace("\u2014","-")
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
    return s

def sanitize(obj):
    if isinstance(obj, dict): return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [sanitize(i) for i in obj]
    elif isinstance(obj, str): return safe_str(obj)
    return obj

def load_json(f, default):
    try: return json.load(open(STUDIO + "/" + f, encoding="utf-8"))
    except: return default

def load_text(f, default=""):
    try: return open(STUDIO + "/" + f, encoding="utf-8", errors="replace").read()
    except: return default

def refresh_asset_usage():
    import importlib.util
    spec = importlib.util.spec_from_file_location("uau", STUDIO + "/update_asset_usage.py")
    mod = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(mod)
    except Exception as e: print("Asset usage refresh skipped: " + str(e)[:60])

refresh_asset_usage()

now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
today = datetime.now().strftime("%Y-%m-%d")

supervisor_inbox = load_json("supervisor-inbox.json", {"items": []})
mobile_inbox     = load_json("mobile-inbox.json", [])
whiteboard       = load_json("whiteboard.json", {"items": []})
asset_log        = load_json("asset-log.json", {"assets": []})
services         = load_json("ai-services-rankings.json", {"categories": {}})
intel_summary    = load_text("ai-intel-summary.txt", "")

sup_items = supervisor_inbox.get("items", supervisor_inbox) if isinstance(supervisor_inbox, dict) else supervisor_inbox
mob_items = mobile_inbox if isinstance(mobile_inbox, list) else mobile_inbox.get("items", mobile_inbox.get("questions", []))

inbox_items = []
for i in sup_items:
    if isinstance(i, dict) and i.get("status") not in ("RESOLVED", "resolved"):
        inbox_items.append(sanitize({"id": i.get("id", "sup-" + str(len(inbox_items))), "title": i.get("title","Untitled"), "finding": i.get("finding","")[:150], "urgency": i.get("urgency","INFO"), "date": i.get("date",""), "source": "supervisor"}))
RESOLVED_STATUSES = ("resolved","RESOLVED","auto-resolved","build","done","DONE")
for i in mob_items:
    if isinstance(i, dict) and i.get("status") not in RESOLVED_STATUSES:
        # Skip whiteboard items - they belong in PLAN tab only
        title = i.get("question", i.get("title",""))
        if "WHITEBOARD" in title or i.get("id","").startswith("wb-"):
            continue
        inbox_items.append(sanitize({"id": i.get("id","mob-"+str(len(inbox_items))), "title": title[:100], "finding": i.get("context",i.get("description",""))[:100], "urgency": "WARN" if i.get("priority")=="high" else "INFO", "date": i.get("created_at",i.get("date","")), "source": "mobile"}))

wb_items = whiteboard.get("items", [])
wb_scored = sorted([i for i in wb_items if i.get("gemini_score")], key=lambda x: x.get("gemini_score",{}).get("total_score",0), reverse=True)
wb_top = [sanitize({"title": i.get("title",""), "description": (i.get("description","") or "")[:80], "score": i.get("gemini_score",{}).get("total_score",0), "action": i.get("gemini_score",{}).get("recommended_action","")}) for i in wb_scored[:10]]

intel_clean = intel_summary.encode("ascii","replace").decode("ascii")[:2000].replace("\\","\\\\").replace("`","'")
assets_clean = sanitize(asset_log.get("assets",[]))
services_clean = sanitize(services.get("categories",{}))
services_date  = services.get("date", today)

injected_json = json.dumps({"generated": now_iso, "inbox": inbox_items, "whiteboard": wb_top, "assets": assets_clean, "services": services_clean, "servicesDate": services_date, "intelSummary": intel_clean}, ensure_ascii=True)

new_script_tag = (
    '<script>\n'
    '// INJECTED STUDIO DATA - generated: ' + now_iso + '\n'
    'const INJECTED = ' + injected_json + ';\n'
    '// END INJECTED DATA\n'
    '</script>\n'
)

src = open(SIDEBAR, encoding="utf-8").read()

# Remove any existing INJECTED script tag(s)
src = re.sub(r'<script>\s*// INJECTED STUDIO DATA.*?// END INJECTED DATA\s*</script>\s*', '', src, flags=re.DOTALL)

# Also remove any inline const INJECTED still in the main script
# (find and remove just the const INJECTED = {...}; statement)
def remove_inline_injected(s):
    idx = s.find("const INJECTED = ")
    if idx < 0: return s
    depth = 0; started = False
    for i in range(idx, min(idx+60000, len(s))):
        c = s[i]
        if c == '{': depth += 1; started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                end = i + 1
                if end < len(s) and s[end] == ';': end += 1
                if end < len(s) and s[end] == '\n': end += 1
                return s[:idx] + s[end:]
    return s

src = remove_inline_injected(src)
# Run again in case there were 2
src = remove_inline_injected(src)

# Insert BEFORE the tab bar (after <body>)
insert_pos = src.find("<body>") + len("<body>") + 1
src = src[:insert_pos] + new_script_tag + src[insert_pos:]

open(SIDEBAR, "w", encoding="utf-8").write(src)

inj_line = src[:src.find("const INJECTED")].count('\n') + 1
onload_line = src[:src.find("window.onload")].count('\n') + 1
print("Injected: " + str(len(inbox_items)) + " inbox, " + str(len(wb_top)) + " whiteboard, " + str(len(assets_clean)) + " assets")
print("INJECTED at line " + str(inj_line) + ", window.onload at line " + str(onload_line) + " - order: " + ("OK" if inj_line < onload_line else "WRONG"))
print("Done.")
