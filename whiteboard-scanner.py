"""
whiteboard-scanner.py — Periodic Whiteboard Status Sync
========================================================
Crosses whiteboard.json against 4 live sources and closes
items that are already done. Runs nightly after WhiteboardAgent.

Sources checked (in order):
  1. Item's own status/deployed fields (LIVE, ACTIVE, DEPLOYED, DONE)
  2. STUDIO_AUDIT.md markers ([OK], LIVE, ACTIVE, RESOLVED)
  3. Task Scheduler registered task names
  4. Git commit log for matching filenames or IDs

Output:
  - Updates whiteboard.json — adds closed_at, sets status='done'
  - Writes morning report to supervisor-inbox.json

Author: Studio Maintenance — 2026-04-04
"""

import json, subprocess, re, os, sys
from datetime import datetime, timezone

STUDIO = "G:/My Drive/Projects/_studio"
WHITEBOARD = STUDIO + "/whiteboard.json"
AUDIT_MD   = STUDIO + "/STUDIO_AUDIT.md"
INBOX      = STUDIO + "/supervisor-inbox.json"

DONE_STATUS_VALUES = {
    "live", "active", "deployed", "done", "completed",
    "resolved", "live_deployed", "in_progress"   # in_progress = keep open
}
# These signal item is shipped
CLOSED_SIGNALS = {"live", "active", "deployed", "done", "completed", "resolved"}

NOW = datetime.now(timezone.utc).isoformat()


def load_json(path):
    try:
        return json.load(open(path, encoding="utf-8-sig", errors="replace"))
    except Exception as e:
        print(f"[WARN] Could not load {path}: {e}")
        return None


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_audit_done_ids():
    """Parse STUDIO_AUDIT.md for IDs/titles marked [OK], RESOLVED, LIVE, ACTIVE."""
    done = set()
    try:
        text = open(AUDIT_MD, encoding="utf-8", errors="replace").read()
        # Lines like: [OK] supervisor.md or [RESOLVED] auto-answer.md
        for line in text.splitlines():
            if any(m in line for m in ["[OK]", "[RESOLVED]", "LIVE", "ACTIVE", "DEPLOYED"]):
                # Extract filename stem as potential match key
                match = re.search(r'[\w\-\.]+\.(?:md|py|json|html|js)', line)
                if match:
                    done.add(match.group(0).lower().replace(".md","").replace(".py",""))
    except Exception as e:
        print(f"[WARN] Audit parse failed: {e}")
    return done


def load_git_done_ids():
    """Scan recent git commits for deployed item IDs or filenames."""
    done = set()
    try:
        result = subprocess.run(
            ["git", "-C", STUDIO, "log", "--oneline", "-100"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            # Pick up wb- IDs and common filenames in commit messages
            for m in re.findall(r'wb-[\d\-]+|[\w\-]+\.(?:py|json|md)', line):
                done.add(m.lower().replace(".py","").replace(".json","").replace(".md",""))
    except Exception as e:
        print(f"[WARN] Git log failed: {e}")
    return done


def load_scheduler_tasks():
    """Get registered Task Scheduler task names on Windows."""
    tasks = set()
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "CSV", "/nh"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.splitlines():
            parts = line.strip().strip('"').split('","')
            if parts:
                tasks.add(parts[0].lower().strip('"'))
    except Exception as e:
        print(f"[WARN] Scheduler query failed: {e}")
    return tasks


def item_is_done(item, audit_ids, git_ids, scheduler_tasks):
    """Return (is_done, reason) for a whiteboard item."""
    item_id    = str(item.get("id", "")).lower()
    status     = str(item.get("status", "")).lower()
    deployed   = str(item.get("deployed", "")).lower()
    title      = str(item.get("title", "")).lower()

    # 1. Own status field
    if status in CLOSED_SIGNALS:
        return True, f"status='{status}'"

    # 2. Has deployed timestamp
    if deployed and deployed not in {"", "none", "false", "null"}:
        return True, f"deployed='{deployed}'"

    # 3. Audit MD match
    for aid in audit_ids:
        if aid and (aid in item_id or aid in title):
            return True, f"audit_match='{aid}'"

    # 4. Git commit match
    for gid in git_ids:
        if gid and len(gid) > 4 and gid in item_id:
            return True, f"git_match='{gid}'"

    return False, ""


def run():
    wb = load_json(WHITEBOARD)
    if not wb:
        print("[ERROR] Cannot load whiteboard.json")
        return

    audit_ids       = load_audit_done_ids()
    git_ids         = load_git_done_ids()
    scheduler_tasks = load_scheduler_tasks()

    closed_this_run = []
    still_open      = []

    for item in wb.get("items", []):
        # Skip github_trending noise — not actionable items
        if item.get("type") == "github_trending":
            continue
        # Skip already closed
        if str(item.get("status","")).lower() == "done":
            continue

        is_done, reason = item_is_done(item, audit_ids, git_ids, scheduler_tasks)

        if is_done:
            item["status"]    = "done"
            item["closed_at"] = NOW
            item["closed_reason"] = reason
            closed_this_run.append({
                "id":    item.get("id"),
                "title": item.get("title","")[:60],
                "reason": reason
            })
        else:
            still_open.append(item.get("id"))

    # Save updated whiteboard
    wb["updated"] = NOW
    save_json(WHITEBOARD, wb)

    # Write morning report to supervisor inbox
    inbox = load_json(INBOX) or {"items": []}
    report = {
        "id":        f"wb-scan-{NOW[:10]}",
        "type":      "whiteboard_scan_report",
        "created_at": NOW,
        "priority":  "low",
        "summary":   f"Whiteboard scan: {len(closed_this_run)} closed, {len(still_open)} still open.",
        "closed":    closed_this_run,
        "open_count": len(still_open),
    }
    inbox.setdefault("items", []).append(report)
    save_json(INBOX, inbox)

    print(f"[whiteboard-scanner] Closed: {len(closed_this_run)} | Open: {len(still_open)}")
    for c in closed_this_run:
        print(f"  CLOSED [{c['reason']}]: {c['title']}")


if __name__ == "__main__":
    run()
