"""
provider_health.py
Maintains a rolling health status for every model in the gateway routing table.
Called by ai_gateway.py on every call — reads/writes provider-health.json.
Also callable standalone to generate a health report.

provider-health.json structure:
{
  "groq/llama-3.3-70b-versatile": {
    "status": "ok" | "degraded" | "defunct",
    "last_success": "2026-04-01T09:30:00",
    "last_failure": "2026-04-01T09:25:00",
    "last_error": "HTTP Error 404: Model deprecated",
    "consecutive_failures": 0,
    "total_calls": 142,
    "total_failures": 3,
    "failure_reasons": {"HTTP Error 404": 2, "timeout": 1},
    "notes": ""
  }
}
"""
import json, os
from datetime import datetime

STUDIO      = "G:/My Drive/Projects/_studio"
HEALTH_PATH = STUDIO + "/provider-health.json"

DEFUNCT_SIGNALS = [
    "deprecated", "does not exist", "model not found",
    "no longer available", "decommissioned", "removed",
    "not supported", "404"
]

DEGRADED_SIGNALS = [
    "429", "rate limit", "quota", "too many requests",
    "503", "service unavailable", "timeout"
]


def _load():
    try:
        return json.load(open(HEALTH_PATH, encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _save(data):
    tmp = HEALTH_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, HEALTH_PATH)


def _key(provider, model):
    return f"{provider}/{model}"


def _classify_error(error_str):
    e = error_str.lower()
    for sig in DEFUNCT_SIGNALS:
        if sig in e:
            return "defunct"
    for sig in DEGRADED_SIGNALS:
        if sig in e:
            return "degraded"
    return "degraded"


def record_success(provider, model):
    """Call this when a provider/model call succeeds."""
    data = _load()
    k = _key(provider, model)
    entry = data.get(k, {})
    entry["status"] = "ok"
    entry["last_success"] = datetime.now().isoformat()
    entry["consecutive_failures"] = 0
    entry["total_calls"] = entry.get("total_calls", 0) + 1
    data[k] = entry
    _save(data)


def record_failure(provider, model, error_str):
    """Call this when a provider/model call fails."""
    data = _load()
    k = _key(provider, model)
    entry = data.get(k, {})

    # Classify the error
    new_status = _classify_error(error_str)

    # Only downgrade status, never upgrade on failure
    current = entry.get("status", "ok")
    if current == "defunct" or new_status == "defunct":
        entry["status"] = "defunct"
    else:
        entry["status"] = new_status

    entry["last_failure"]         = datetime.now().isoformat()
    entry["last_error"]           = error_str[:120]
    entry["consecutive_failures"] = entry.get("consecutive_failures", 0) + 1
    entry["total_calls"]          = entry.get("total_calls", 0) + 1
    entry["total_failures"]       = entry.get("total_failures", 0) + 1

    # Track failure reason distribution
    reasons = entry.get("failure_reasons", {})
    # Normalize error to short bucket
    bucket = error_str[:50]
    reasons[bucket] = reasons.get(bucket, 0) + 1
    entry["failure_reasons"] = reasons

    data[k] = entry
    _save(data)

    return entry["status"]  # return "defunct" | "degraded"

def get_status(provider, model):
    """Returns current status string for a provider/model: ok | degraded | defunct | unknown"""
    data = _load()
    return data.get(_key(provider, model), {}).get("status", "unknown")


def is_usable(provider, model):
    """Returns False if model is known defunct — skip it in routing."""
    return get_status(provider, model) != "defunct"


def get_report():
    """Returns dict of all provider statuses grouped by health."""
    data = _load()
    report = {"ok": [], "degraded": [], "defunct": [], "unknown": []}
    for key, entry in data.items():
        status = entry.get("status", "unknown")
        report.setdefault(status, []).append({
            "model": key,
            "last_success": entry.get("last_success", "never"),
            "last_failure": entry.get("last_failure", "never"),
            "last_error": entry.get("last_error", ""),
            "consecutive_failures": entry.get("consecutive_failures", 0),
            "total_calls": entry.get("total_calls", 0),
            "total_failures": entry.get("total_failures", 0),
        })
    return report


def push_defunct_to_inbox(supervisor_inbox_path=None):
    """Push newly defunct models to supervisor inbox as WARN items."""
    import os
    inbox_path = supervisor_inbox_path or STUDIO + "/supervisor-inbox.json"
    data   = _load()
    defunct = [k for k, v in data.items() if v.get("status") == "defunct"]
    if not defunct:
        return 0

    try:
        inbox = json.load(open(inbox_path, encoding="utf-8", errors="replace"))
    except Exception:
        inbox = []
    if isinstance(inbox, dict):
        inbox = inbox.get("items", [])

    existing_ids = {i.get("id","") for i in inbox}
    pushed = 0
    for key in defunct:
        item_id = f"defunct-model-{key.replace('/','_')}"
        if item_id in existing_ids:
            continue
        entry = data[key]
        inbox.append({
            "id": item_id,
            "source": "provider-health",
            "type": "model_defunct",
            "urgency": "WARN",
            "title": f"DEFUNCT MODEL: {key}",
            "finding": (f"Model {key} appears deprecated/removed. "
                       f"Last error: {entry.get('last_error','unknown')}. "
                       f"Failures: {entry.get('consecutive_failures',0)} consecutive. "
                       f"Remove from TASK_ROUTING in ai_gateway.py."),
            "status": "PENDING",
            "date": datetime.now().isoformat()
        })
        pushed += 1

    if pushed:
        json.dump(inbox, open(inbox_path, "w", encoding="utf-8"), indent=2)

    return pushed


# ── Standalone: print health report ────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = get_report()
    total = sum(len(v) for v in report.values())
    print(f"\n=== PROVIDER HEALTH REPORT ===")
    print(f"Total tracked: {total} models\n")

    for status in ["ok", "degraded", "defunct", "unknown"]:
        items = report.get(status, [])
        if not items:
            continue
        label = {"ok": "OK", "degraded": "DEGRADED", "defunct": "DEFUNCT", "unknown": "UNTRACKED"}[status]
        print(f"[{label}] ({len(items)})")
        for item in items:
            cf = item["consecutive_failures"]
            err = f" | last_error: {item['last_error'][:60]}" if item["last_error"] else ""
            print(f"  {item['model']}")
            print(f"    calls={item['total_calls']} failures={item['total_failures']} consecutive={cf}{err}")
        print()

    defunct = push_defunct_to_inbox()
    if defunct:
        print(f"Pushed {defunct} defunct model(s) to supervisor inbox.")
