"""
utilities/heartbeat.py
Shared heartbeat writer. Call write(agent_name, status, notes) at end of any agent run.
Zero dependencies beyond stdlib.
"""
import json, os
from datetime import datetime

STUDIO   = "G:/My Drive/Projects/_studio"
HB_PATH  = STUDIO + "/heartbeat-log.json"
MAX_KEEP = 500

def write(agent: str, status: str = "clean", notes: str = ""):
    """Write one heartbeat entry. status: clean | flagged | error"""
    try:
        hb = {}
        if os.path.exists(HB_PATH):
            try: hb = json.load(open(HB_PATH, encoding="utf-8", errors="replace"))
            except: hb = {}
        if not isinstance(hb, dict): hb = {}
        entries = hb.get("entries", [])
        entries.append({
            "date":   datetime.now().isoformat(),
            "agent":  agent,
            "status": status,
            "notes":  notes[:200]
        })
        hb["entries"] = entries[-MAX_KEEP:]
        tmp = HB_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(hb, f, indent=2, ensure_ascii=False)
        os.replace(tmp, HB_PATH)
    except Exception as e:
        print("[heartbeat] write failed: " + str(e)[:60])
