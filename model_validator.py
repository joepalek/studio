
MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule
"""
model_validator.py — Nightly Model Health Check
================================================
Runs nightly (or on demand). Queries every provider's live model list,
compares against model-registry.json, flags deprecated/missing models,
updates provider-health.json, and pushes findings to supervisor inbox.

Schedule: Add to Task Scheduler — daily 06:30 AM after AIServicesRankings
Run manually: python model_validator.py
"""

# EXPECTED_RUNTIME_SECONDS: 120
import json, urllib.request, sys, os
sys.path.insert(0, "G:/My Drive/Projects/_studio")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datetime import datetime
import provider_health as ph

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

STUDIO        = "G:/My Drive/Projects/_studio"
REGISTRY_PATH = STUDIO + "/model-registry.json"
INBOX_PATH    = STUDIO + "/supervisor-inbox.json"
LOG_PATH      = STUDIO + "/scheduler/logs/model-validator.log"
CONFIG_PATH   = STUDIO + "/studio-config.json"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_json(url, headers, timeout=15):
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(r.read())

def load_cfg():
    return json.load(open(CONFIG_PATH, encoding="utf-8-sig", errors="replace"))

def fetch_live_models(cfg):
    """Query each provider's live model list. Returns {provider: [model_ids]}"""
    live = {}

    # Groq
    try:
        data = get_json("https://api.groq.com/openai/v1/models",
            {"Authorization": f"Bearer {cfg['Groq API Key']}", "User-Agent": UA})
        live["groq"] = [m["id"] for m in data.get("data", [])]
        log(f"  Groq: {len(live['groq'])} models live")
    except Exception as e:
        log(f"  Groq: FAILED to fetch ({str(e)[:60]})")

    # Cerebras
    try:
        data = get_json("https://api.cerebras.ai/v1/models",
            {"Authorization": f"Bearer {cfg['Cerebras API Key']}", "User-Agent": UA})
        live["cerebras"] = [m["id"] for m in data.get("data", [])]
        log(f"  Cerebras: {len(live['cerebras'])} models live")
    except Exception as e:
        log(f"  Cerebras: FAILED to fetch ({str(e)[:60]})")

    # Mistral
    try:
        data = get_json("https://api.mistral.ai/v1/models",
            {"Authorization": f"Bearer {cfg['Mistral API Key']}"})
        live["mistral"] = [m["id"] for m in data.get("data", [])]
        log(f"  Mistral: {len(live['mistral'])} models live")
    except Exception as e:
        log(f"  Mistral: FAILED to fetch ({str(e)[:60]})")

    # OpenRouter - free models
    try:
        data = get_json("https://openrouter.ai/api/v1/models",
            {"Authorization": f"Bearer {cfg['openrouter_api_key']}"})
        live["openrouter"] = [m["id"] for m in data.get("data", [])
                              if str(m.get("pricing",{}).get("prompt","1")) == "0"]
        log(f"  OpenRouter: {len(live['openrouter'])} free models live")
    except Exception as e:
        log(f"  OpenRouter: FAILED to fetch ({str(e)[:60]})")

    # Gemini - check known models with a lightweight call
    gemini_models = ["gemini-2.5-flash", "gemini-2.0-flash-001", "gemini-flash-lite", "gemini-1.5-pro"]
    live["gemini"] = []
    key = cfg.get("gemini_api_key", "")
    _consecutive_failures = 0
    for model in gemini_models:
        try:
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{model}:generateContent?key={key}")
            body = json.dumps({"contents":[{"parts":[{"text":"hi"}]}],
                               "generationConfig":{"maxOutputTokens":1}}).encode()
            req = urllib.request.Request(url, data=body,
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10)
            live["gemini"].append(model)
        except Exception as e:
            err = str(e)
            if "404" in err or "deprecated" in err.lower():
                log(f"  Gemini {model}: DEFUNCT ({err[:50]})")
                ph.record_failure("gemini", model, err[:120])
            # other errors = degraded, not defunct
    log(f"  Gemini: {len(live['gemini'])} models responding")

    return live

def validate_registry_against_live(live, registry):
    """Compare registry model_ids against live lists. Return findings."""
    findings = {"defunct": [], "not_checked": [], "ok": [], "new_available": []}
    providers = registry.get("providers", {})

    for prov_key, prov in providers.items():
        live_list = live.get(prov_key)
        if live_list is None:
            # Couldn't query this provider — skip, don't mark defunct
            for mk in prov.get("models", {}):
                findings["not_checked"].append(f"{prov_key}/{mk}")
            continue

        for mk, mv in prov.get("models", {}).items():
            if mv.get("status", "").startswith("active"):
                if mk not in live_list:
                    findings["defunct"].append({
                        "key": f"{prov_key}/{mk}",
                        "provider": prov_key,
                        "model": mk,
                        "display": mv.get("display", mk),
                        "reason": f"Not found in live {prov_key} model list"
                    })
                    ph.record_failure(prov_key, mk,
                        f"Not found in live model list — likely deprecated")
                else:
                    findings["ok"].append(f"{prov_key}/{mk}")
                    ph.record_success(prov_key, mk)

    return findings


def push_findings_to_inbox(findings):
    """Push defunct/new model findings to supervisor inbox."""
    if not findings["defunct"]:
        return 0

    try:
        inbox = json.load(open(INBOX_PATH, encoding="utf-8", errors="replace"))
    except Exception:
        inbox = []
    if isinstance(inbox, dict):
        inbox = inbox.get("items", [])

    existing_ids = {i.get("id","") for i in inbox}
    pushed = 0
    today = datetime.now().strftime("%Y-%m-%d")

    for item in findings["defunct"]:
        item_id = f"defunct-{item['key'].replace('/','_')}-{today}"
        if item_id in existing_ids:
            continue
        inbox.append({
            "id": item_id,
            "source": "model-validator",
            "type": "model_defunct",
            "urgency": "WARN",
            "title": f"DEFUNCT MODEL: {item['display']} ({item['key']})",
            "finding": (f"{item['reason']}. "
                       f"Action: remove from TASK_ROUTING in ai_gateway.py "
                       f"and mark status=deprecated in model-registry.json."),
            "status": "PENDING",
            "date": datetime.now().isoformat()
        })
        pushed += 1

    if pushed:
        json.dump(inbox, open(INBOX_PATH, "w", encoding="utf-8"), indent=2)
    return pushed


@hamilton_watchdog("model_validator", expected_seconds=120)
def main():
    log("Model validator starting")
    cfg = load_cfg()
    registry = json.load(open(REGISTRY_PATH, encoding="utf-8", errors="replace"))

    log("Fetching live model lists from all providers...")
    live = fetch_live_models(cfg)

    log("Comparing registry against live models...")
    findings = validate_registry_against_live(live, registry)

    ok_count      = len(findings["ok"])
    defunct_count = len(findings["defunct"])
    skip_count    = len(findings["not_checked"])

    log(f"Results: {ok_count} OK | {defunct_count} DEFUNCT | {skip_count} not checked")

    if findings["defunct"]:
        log("DEFUNCT MODELS:")
        for item in findings["defunct"]:
            log(f"  {item['key']} — {item['reason']}")
        pushed = push_findings_to_inbox(findings)
        log(f"Pushed {pushed} findings to supervisor inbox")
    else:
        log("All checked models confirmed live")

    # Also push any accumulated defunct from gateway log
    ph.push_defunct_to_inbox()

    # Write heartbeat
    try:
        hb_path = STUDIO + "/heartbeat-log.json"
        hb = json.load(open(hb_path, encoding="utf-8", errors="replace"))
        if isinstance(hb, list):
            hb = {"entries": hb}
        hb.setdefault("entries", []).append({
            "date": datetime.now().isoformat(),
            "agent": "model-validator",
            "status": "flagged" if defunct_count else "clean",
            "notes": f"ok={ok_count} defunct={defunct_count} skipped={skip_count}"
        })
        json.dump(hb, open(hb_path, "w", encoding="utf-8"), indent=2)
    except Exception as e:
        log(f"Heartbeat write failed: {e}")

    log("Model validator complete")


if __name__ == "__main__":
    main()
