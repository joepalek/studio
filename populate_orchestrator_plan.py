
MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule
"""
populate_orchestrator_plan.py
Reads orchestrator-briefing.json + whiteboard.json + project states.
Writes structured agent_runnable tasks to orchestrator-plan.json.
Run after orchestrator-briefing.bat each morning, or standalone.
Zero LLM cost — pure Python logic.
"""
import json, os, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO = "G:/My Drive/Projects/_studio"
BASE   = "G:/My Drive/Projects"
PLAN   = STUDIO + "/orchestrator-plan.json"
BRIEF  = STUDIO + "/orchestrator-briefing.json"
WB     = STUDIO + "/whiteboard.json"
QUEUE  = STUDIO + "/task-queue.json"

def load(path, default=None):
    try: return json.load(open(path, encoding="utf-8", errors="replace"))
    except: return default

def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def log(msg):
    print("[" + datetime.now().strftime("%H:%M:%S") + "] " + msg)

def get_dirty_repos():
    """Find repos with uncommitted files — agent can commit them."""
    import subprocess
    dirty = []
    for d in os.listdir(BASE):
        path = BASE + "/" + d
        if not os.path.isdir(path) or not os.path.exists(path + "/.git"): continue
        r = subprocess.run(["git", "-C", path, "status", "--short"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.stdout.strip():
            count = len([l for l in r.stdout.strip().split("\n") if l.strip()])
            dirty.append({"repo": d, "path": path, "files": count})
    return dirty

def get_whiteboard_build_tasks():
    """Get whiteboard items scored 8+ with action=BUILD that have no active project."""
    wb = load(WB, {})
    items = wb.get("items", [])
    tasks = []
    _consecutive_failures = 0
    for item in items:
        sc = item.get("gemini_score", {})
        if (sc.get("total_score", 0) >= 8 and
            sc.get("recommended_action") in ("BUILD", "PUBLISH", "RESEARCH") and
            not item.get("project_started")):
            tasks.append({
                "project": "whiteboard",
                "action": sc.get("recommended_action", "BUILD") + ": " + item.get("title","")[:60],
                "priority": "high" if sc.get("total_score",0) >= 9 else "medium",
                "source": "whiteboard",
                "score": sc.get("total_score", 0),
                "effort": sc.get("effort_estimate", "unknown"),
                "tier": "gemini"
            })
    return sorted(tasks, key=lambda x: x["score"], reverse=True)[:5]

def get_stale_agents():
    """Check which agents haven't run in 48h and queue a check."""
    import os
    LOG_DIR = STUDIO + "/scheduler/logs"
    now = datetime.now().timestamp()
    stale = []
    expected = {
        "overnight-auto-answer.log": "OvernightAutoAnswer",
        "overnight-whiteboard-score.log": "WhiteboardScorer",
        "overnight-product-archaeology.log": "ProductArchaeology",
        "overnight-vintage-agent.log": "VintageAgent",
        "overnight-agency-build.log": "AgencyBuild",
    }
    for logfile, agent in expected.items():
        path = LOG_DIR + "/" + logfile
        if not os.path.exists(path):
            stale.append(agent)
            continue
        age_hours = (now - os.path.getmtime(path)) / 3600
        if age_hours > 48:
            stale.append(agent + " (last ran " + str(int(age_hours)) + "h ago)")
    return stale

def main():
    log("Populating orchestrator-plan.json")

    # Load existing plan to preserve human_required/blocked sections
    existing = load(PLAN, {})
    brief    = load(BRIEF, {})

    agent_runnable = []

    # 1 — Dirty repos that need committing (git_commit.py handles this but
    #     queue it so Supervisor knows what's pending)
    dirty = get_dirty_repos()
    if dirty:
        agent_runnable.append({
            "id": "task-git-commit",
            "project": "_studio",
            "action": "Commit dirty repos: " + ", ".join(d["repo"] + "(" + str(d["files"]) + "f)" for d in dirty[:5]),
            "agent": "git_commit.py",
            "tier": "gemini",
            "priority": "high",
            "auto": True,
            "created": datetime.now().isoformat()
        })
        log("Dirty repos: " + str(len(dirty)))

    # 2 — Whiteboard high-score items ready to action
    wb_tasks = get_whiteboard_build_tasks()
    for t in wb_tasks:
        agent_runnable.append({
            "id": "task-wb-" + t["action"][:20].replace(" ","_").lower(),
            "project": "whiteboard",
            "action": t["action"],
            "agent": "human_session",
            "tier": "claude",
            "priority": t["priority"],
            "score": t["score"],
            "effort": t["effort"],
            "auto": False,
            "created": datetime.now().isoformat()
        })
    log("Whiteboard tasks: " + str(len(wb_tasks)))

    # 3 — Stale agent checks
    stale = get_stale_agents()
    if stale:
        agent_runnable.append({
            "id": "task-stale-check",
            "project": "_studio",
            "action": "Investigate stale agents: " + ", ".join(stale),
            "agent": "supervisor_check.py",
            "tier": "python",
            "priority": "medium",
            "auto": True,
            "created": datetime.now().isoformat()
        })
        log("Stale agents: " + ", ".join(stale))

    # 4 — Carry over any existing queued tasks from task-queue.json
    tq = load(QUEUE, [])
    tq_list = tq if isinstance(tq, list) else tq.get("tasks", [])
    queued = [t for t in tq_list if t.get("status") == "queued"]
    for t in queued[:3]:
        agent_runnable.append({
            "id": t.get("id", "task-queue-" + str(len(agent_runnable))),
            "project": t.get("project", "?"),
            "action": t.get("task", ""),
            "tier": "gemini",
            "priority": t.get("priority", "medium"),
            "auto": False,
            "created": t.get("queued_at", datetime.now().isoformat())
        })
    if queued: log("Task queue carry-over: " + str(len(queued)))

    # Build final plan preserving orchestrator's human_required/blocked
    plan = {
        "generated": datetime.now().isoformat(),
        "agent_runnable": agent_runnable,
        "human_required": brief.get("plan", {}).get("human_required", existing.get("human_required", [])),
        "blocked":        brief.get("plan", {}).get("blocked",        existing.get("blocked", [])),
        "ready_to_build": brief.get("plan", {}).get("ready_to_build", existing.get("ready_to_build", []))
    }

    save(PLAN, plan)
    log("Plan written: " + str(len(agent_runnable)) + " agent_runnable tasks")
    for t in agent_runnable:
        log("  [" + t["priority"] + "] " + t["project"] + ": " + t["action"][:60])

if __name__ == "__main__":
    main()
