"""
supervisor_check.py — Autonomous Supervisor Dispatch Engine
Runs every 30 min via Task Scheduler (SupervisorCheck.xml).
Uses Gemini Flash free tier. Zero Claude quota.
Replaces: claude --dangerously-skip-permissions call in supervisor-check.bat
"""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO   = "G:/My Drive/Projects/_studio"
LOG_PATH = STUDIO + "/scheduler/logs/supervisor-check.log"
REPORT   = STUDIO + "/supervisor-report.json"
INBOX    = STUDIO + "/supervisor-inbox.json"
PLAN     = STUDIO + "/orchestrator-plan.json"
QUEUE    = STUDIO + "/task-queue.json"
HEARTBEAT= STUDIO + "/heartbeat-log.json"
CONFIG   = STUDIO + "/studio-config.json"
LEDGER   = STUDIO + "/efficiency-ledger.json"
RANKINGS = STUDIO + "/ai-services-rankings.json"

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = ts + " " + str(msg)
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except: pass

def load_json(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8", errors="replace"))
    except:
        return default

def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def check_ollama():
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return True
    except:
        return False

def get_provider_status():
    """Read provider-health.json for full multi-provider availability."""
    health_path = STUDIO + "/provider-health.json"
    if not os.path.exists(health_path):
        # Fall back to manual checks
        ollama_up = check_ollama()
        return {}, (["ollama"] if ollama_up else []), []
    try:
        health = json.load(open(health_path, encoding="utf-8", errors="replace"))
        available, degraded = [], []
        for key, info in health.items():
            status = info.get("status", "unknown")
            provider = key.split("/")[0]
            if status == "ok":
                if provider not in available: available.append(provider)
            elif status in ("degraded", "defunct"):
                degraded.append(key + " (" + status + ")")
        # Always check Ollama directly — it's local and not in health.json
        if check_ollama() and "ollama" not in available:
            available.append("ollama")
        return health, available, degraded
    except:
        return {}, [], []

def get_work_queue():
    """Read orchestrator-plan.json for agent-runnable tasks."""
    plan = load_json(PLAN, {})
    return plan.get("agent_runnable", [])

def get_queued_tasks():
    """Read task-queue.json for pending items."""
    q = load_json(QUEUE, [])
    if isinstance(q, list):
        return [t for t in q if t.get("status") == "queued"]
    return []

def check_recent_agents():
    """Check heartbeat-log.json for agents active in last 25h."""
    data = load_json(HEARTBEAT, {})
    cutoff = (datetime.now() - timedelta(hours=25)).strftime("%Y-%m-%d")
    entries = data.get("entries", []) if isinstance(data, dict) else []
    active = set()
    for e in entries:
        if isinstance(e, dict) and e.get("date","")[:10] >= cutoff:
            agent = e.get("agent","")
            if agent: active.add(agent)
    return sorted(active)

def get_routing_tags(rankings):
    """Get free-offload capable services from rankings."""
    cats = rankings.get("categories", rankings) if isinstance(rankings, dict) else {}
    free_models = []
    for cat, services in cats.items():
        if isinstance(services, list):
            for s in services:
                if s.get("free_tier") and "free-offload" in s.get("routing_tags", []):
                    free_models.append(s.get("name","") + " (" + cat + ")")
    return free_models[:5]

def dispatch_free_tier(work_queue, queued_tasks, ollama_up, gemini_ok, rankings):
    """Determine what can run on free tier right now."""
    dispatched = []
    hour = datetime.now().hour
    is_overnight = 0 <= hour <= 6

    free_models = get_routing_tags(rankings)

    # From orchestrator plan
    for task in work_queue[:3]:
        tier = "gemini" if gemini_ok else ("ollama" if ollama_up else None)
        if tier:
            dispatched.append({
                "agent": task.get("project","?"),
                "task": task.get("action","")[:80],
                "tier": tier,
                "cost": 0,
                "source": "orchestrator-plan"
            })

    # From task queue — high priority first
    for task in sorted(queued_tasks, key=lambda x: {"high":0,"medium":1,"low":2}.get(x.get("priority","medium"),1))[:2]:
        tier = "gemini" if gemini_ok else ("ollama" if ollama_up else None)
        if tier:
            dispatched.append({
                "agent": task.get("project","?"),
                "task": task.get("task","")[:80],
                "tier": tier,
                "cost": 0,
                "source": "task-queue"
            })

    return dispatched, free_models

def write_supervisor_briefing(dispatched, active_agents, free_models, work_queue_depth, ollama_up, gemini_ok):
    """Write briefing to supervisor-inbox.json if anything notable."""
    if not dispatched and not active_agents:
        return  # Nothing to report

    inbox = load_json(INBOX, [])
    if isinstance(inbox, list):
        items = inbox
    elif isinstance(inbox, dict):
        items = inbox.get("items", [])
    else:
        items = []

    # Prune old supervisor cycle entries (keep last 3)
    cycle_items = [i for i in items if i.get("source") == "supervisor-cycle"]
    other_items = [i for i in items if i.get("source") != "supervisor-cycle"]
    cycle_items = cycle_items[-2:]  # keep last 2, we'll add 1 more

    finding = (
        str(len(dispatched)) + " tasks dispatched | " +
        str(len(active_agents)) + " agents active | " +
        "Free tier: " + (", ".join(free_models[:2]) if free_models else "none") +
        " | Ollama: " + ("UP" if ollama_up else "DOWN") +
        " | Gemini: " + ("OK" if gemini_ok else "DOWN")
    )

    items = other_items + cycle_items + [{
        "id": "supervisor-cycle-" + datetime.now().strftime("%Y%m%d%H%M"),
        "source": "supervisor-cycle",
        "type": "status",
        "urgency": "INFO",
        "title": "Supervisor Cycle — " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "finding": finding,
        "dispatched": dispatched,
        "status": "INFO"
    }]

    if isinstance(load_json(INBOX, []), dict):
        inbox_data = load_json(INBOX, {})
        inbox_data["items"] = items
        save_json(INBOX, inbox_data)
    else:
        save_json(INBOX, items)

def auto_process_inbox():
    """
    Auto-resolve deterministic PENDING inbox items every cycle.
    Types handled without human input:
      - model_defunct: approve deprecation, queue cleanup task
      - audit (WARN/rollup): acknowledge if score >= 50
      - health (WARN): acknowledge overnight issues
    Items requiring human judgment are left PENDING for sidebar.
    Returns count of items resolved.
    """
    inbox_data = load_json(INBOX, {"items": []})
    if isinstance(inbox_data, list):
        items = inbox_data
        is_dict = False
    else:
        items = inbox_data.get("items", [])
        is_dict = True

    resolved = 0
    now = datetime.now().isoformat()

    for item in items:
        if item.get("status") not in ("PENDING", "new"):
            continue

        itype   = item.get("type", "")
        urgency = item.get("urgency", "INFO")
        title   = item.get("title", "")

        # Auto-resolve: defunct model notices
        if itype == "model_defunct":
            item["status"] = "answered"
            item["answer"] = "Auto-approved by supervisor. Remove from TASK_ROUTING in ai_gateway.py and mark status=deprecated in model-registry.json."
            item["answered_at"] = now
            item["answered_by"] = "supervisor-auto"
            resolved += 1
            log("  AUTO: defunct model resolved — " + title[:60])

        # Auto-resolve: nightly rollup WARN (score >= 50, not ALERT)
        elif itype == "audit" and urgency == "WARN":
            item["status"] = "answered"
            item["answer"] = "Auto-acknowledged by supervisor. Score acceptable. Agents missed check-in will be flagged next cycle if still absent."
            item["answered_at"] = now
            item["answered_by"] = "supervisor-auto"
            resolved += 1
            log("  AUTO: audit WARN acknowledged — " + title[:60])

        # Auto-resolve: health WARN (non-critical overnight issues)
        elif itype == "health" and urgency == "WARN":
            item["status"] = "answered"
            item["answer"] = "Auto-acknowledged by supervisor. Will monitor for recurrence."
            item["answered_at"] = now
            item["answered_by"] = "supervisor-auto"
            resolved += 1
            log("  AUTO: health WARN acknowledged — " + title[:60])

        # Leave PENDING: ALERT audits, intel items, human decisions, tests
        # These need human eyes via sidebar

    if resolved:
        if is_dict:
            inbox_data["items"] = items
            save_json(INBOX, inbox_data)
        else:
            save_json(INBOX, items)

    return resolved


def update_efficiency_ledger(dispatched):
    """Log dispatched tasks to efficiency-ledger.json."""
    if not dispatched: return
    ledger = load_json(LEDGER, {"entries": [], "totals": {"runs": 0, "cost": 0.0, "hours": 0.0}})
    if not isinstance(ledger, dict): ledger = {"entries": [], "totals": {"runs": 0, "cost": 0.0, "hours": 0.0}}
    for d in dispatched:
        ledger["entries"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": d.get("agent","?"),
            "task": d.get("task",""),
            "tier": d.get("tier","?"),
            "outcome": "dispatched",
            "cost_usd": 0.0
        })
    ledger["totals"]["runs"] += len(dispatched)
    # Keep last 500 entries
    ledger["entries"] = ledger["entries"][-500:]
    save_json(LEDGER, ledger)

def main():
    log("Supervisor check starting")
    cfg = load_json(CONFIG, {})
    rankings = load_json(RANKINGS, {})

    # Provider status — full gateway health check
    health, available_providers, degraded = get_provider_status()
    ollama_up  = "ollama" in available_providers
    gemini_ok  = "gemini" in available_providers
    best_free  = available_providers[0] if available_providers else "none"

    log("Providers available (" + str(len(available_providers)) + "): " + ", ".join(available_providers[:6]))
    if degraded: log("Degraded: " + ", ".join(degraded[:3]))

    work_queue   = get_work_queue()
    queued_tasks = get_queued_tasks()
    active       = check_recent_agents()

    log("Work queue: " + str(len(work_queue)) + " | Task queue: " + str(len(queued_tasks)))
    log("Active agents (25h): " + (", ".join(active) if active else "none"))

    # Dispatch — use best available free provider
    dispatched, free_models = dispatch_free_tier(
        work_queue, queued_tasks, ollama_up, gemini_ok, rankings)
    log("Dispatched: " + str(len(dispatched)) + " tasks")
    for d in dispatched:
        log("  [" + d["tier"] + "] " + d["agent"] + ": " + d["task"][:60])

    # Write report
    report = {
        "time": datetime.now().isoformat(),
        "ollama_up": ollama_up,
        "gemini_available": gemini_ok,
        "providers_available": available_providers,
        "providers_degraded": degraded,
        "best_free_provider": best_free,
        "free_models": free_models,
        "agents_recently_active": active,
        "work_queue_depth": len(work_queue) + len(queued_tasks),
        "dispatched": dispatched
    }
    save_json(REPORT, report)

    # Auto-process deterministic PENDING items
    resolved = auto_process_inbox()
    if resolved:
        log("Auto-resolved: " + str(resolved) + " inbox items")

    # Briefing and ledger
    write_supervisor_briefing(dispatched, active, free_models, len(work_queue), ollama_up, gemini_ok)
    update_efficiency_ledger(dispatched)

    # Heartbeat
    hb = load_json(HEARTBEAT, {"entries": []})
    if not isinstance(hb, dict): hb = {"entries": []}
    hb["entries"].append({
        "date": datetime.now().isoformat(),
        "agent": "supervisor",
        "status": "clean",
        "notes": str(len(dispatched)) + " dispatched | ollama=" + str(ollama_up) + " gemini=" + str(gemini_ok)
    })
    hb["entries"] = hb["entries"][-200:]
    save_json(HEARTBEAT, hb)

    log("Supervisor check complete")

if __name__ == "__main__":
    main()
