"""
nightly_rollup.py — Studio Daily Digest Writer
Runs at 1:00 AM via Task Scheduler (AgentNightlyRollup).
Reads logs, computes health score, writes daily-digest.json entry.
Zero LLM cost — pure Python aggregation.

Replaces: nightly-rollup.md Claude Code agent run
"""

import json
import os
import sys
from datetime import datetime, timedelta

STUDIO = "G:/My Drive/Projects/_studio"
DIGEST_PATH    = os.path.join(STUDIO, "daily-digest.json")
HEARTBEAT_PATH = os.path.join(STUDIO, "heartbeat-log.json")
INBOX_PATH     = os.path.join(STUDIO, "supervisor-inbox.json")
FLAG_PATH      = os.path.join(STUDIO, "lateral-flag.json")
STATUS_PATH    = os.path.join(STUDIO, "claude-status.txt")
HANDOFF_PATH   = os.path.join(STUDIO, "session-handoff.md")
LOG_PATH       = os.path.join(STUDIO, "scheduler/logs/nightly-rollup.log")

EXPECTED_AGENTS = [
    "nightly-rollup",
    "supervisor",
    "vector-reindex",
    "janitor",
    "whiteboard-scorer",
    "ai-intel",
    "agency-build",
    "vintage-agent",
    "product-archaeology",
    "git-commit",
    "check-drift",
]  # All agents that write heartbeat entries nightly


# ── Helpers ──────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    # Try main log, then fallback, then silently continue
    for path in [LOG_PATH, LOG_PATH.replace(".log", "-fallback.log")]:
        try:
            with open(path, "a", encoding="utf-8", errors="replace") as f:
                f.write(line + "\n")
            break  # wrote successfully, stop trying
        except (PermissionError, OSError):
            continue


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# ── Step 1: summarize_24h via audit_logger ───────────────────────────────────

def summarize_24h():
    sys.path.insert(0, os.path.join(STUDIO, "utilities"))
    try:
        from audit_logger import summarize_24h as _s24
        return _s24()
    except Exception as e:
        log(f"WARNING: audit_logger unavailable ({e}) — using zero summary")
        return {
            "total_entries": 0,
            "gate_decisions": {"total": 0, "passed": 0, "failed": 0},
            "scheduler_fires": {"total": 0, "confirmed": 0, "silent": 0},
            "heartbeats": 0,
            "inbox_items_written": 0,
            "flags_raised": 0,
            "top_failure_category": None
        }


# ── Step 2: count agent check-ins from heartbeat-log.json ────────────────────

def get_agent_checkins():
    data = load_json(HEARTBEAT_PATH)
    cutoff = (datetime.now() - timedelta(hours=25)).isoformat()
    checked_in = set()

    if isinstance(data, dict):
        entries = data.get("entries", [])
    elif isinstance(data, list):
        entries = data
    else:
        entries = []

    for entry in entries:
        if isinstance(entry, dict):
            date_str = entry.get("date", "")
            if date_str >= cutoff[:10]:   # date prefix compare
                agent = entry.get("agent", "")
                if agent:
                    checked_in.add(agent)

    missed = [a for a in EXPECTED_AGENTS if a not in checked_in]
    return sorted(checked_in), missed


# ── Step 3: count pending items ───────────────────────────────────────────────

def count_pending_inbox():
    inbox = load_json(INBOX_PATH, [])
    if isinstance(inbox, list):
        return sum(1 for i in inbox if isinstance(i, dict) and i.get("status") == "PENDING")
    return 0


def count_pending_flags():
    flags = load_json(FLAG_PATH, [])
    if isinstance(flags, list):
        return sum(1 for f in flags if isinstance(f, dict) and f.get("status") == "pending")
    elif isinstance(flags, dict):
        return sum(1 for f in flags.get("flags", []) if f.get("status") == "pending")
    return 0


# ── Step 4: compute health score ─────────────────────────────────────────────

def compute_health(audit_summary, missed_agents, pending_flags):
    score = 100
    deductions = []

    for agent in missed_agents:
        score -= 10
        deductions.append(f"-10 missed agent: {agent}")

    failed_gates = audit_summary["gate_decisions"]["failed"]
    for _ in range(failed_gates):
        score -= 5
        deductions.append("-5 failed gate")

    silent_fires = audit_summary["scheduler_fires"]["silent"]
    for _ in range(silent_fires):
        score -= 5
        deductions.append("-5 silent scheduler fire")

    if audit_summary["total_entries"] == 0:
        score -= 20
        deductions.append("-20 zero audit entries")

    for _ in range(pending_flags):
        score -= 3
        deductions.append(f"-3 pending flag")

    score = max(0, score)
    if score >= 80:
        status = "GREEN"
    elif score >= 50:
        status = "YELLOW"
    else:
        status = "RED"

    return score, status, deductions


# ── Step 5: write digest entry ────────────────────────────────────────────────

def write_digest(date_str, generated_at, audit_summary, checked_in, missed,
                 pending_inbox, pending_flags, score, status, notes):
    digest = load_json(DIGEST_PATH)
    if not isinstance(digest, dict) or "digests" not in digest:
        digest = {
            "_schema": "1.0",
            "_description": "Daily studio health digest — append only",
            "_note": "One entry per day. Written by nightly_rollup.py at 1:00am.",
            "digests": []
        }
    entry = {
        "date": date_str,
        "generated_at": generated_at,
        "audit_summary": audit_summary,
        "agent_checkins": {
            "checked_in": checked_in,
            "missed": missed
        },
        "pending_inbox_items": pending_inbox,
        "pending_flags": pending_flags,
        "health_score": score,
        "health_status": status,
        "notes": notes
    }
    digest["digests"].append(entry)
    save_json(DIGEST_PATH, digest)


# ── Step 6: write supervisor inbox briefing ───────────────────────────────────

def write_supervisor_briefing(date_str, score, status, checked_in, missed,
                               audit_summary, top_issue):
    inbox = load_json(INBOX_PATH)
    if isinstance(inbox, list):
        items = inbox
    elif isinstance(inbox, dict):
        items = inbox.get("items", [])
    else:
        items = []

    urgency = "INFO"
    if score < 50:
        urgency = "ALERT"
    elif score < 80:
        urgency = "WARN"

    gate = audit_summary["gate_decisions"]
    finding = (
        f"Score: {score}/100. {len(checked_in)} agents checked in"
        + (f"; missed: {', '.join(missed)}" if missed else "")
        + f". Gate: {gate['passed']} pass / {gate['failed']} fail."
        + (f" Top issue: {top_issue[:80]}" if top_issue else "")
    )

    items.append({
        "id": f"nightly-rollup-{date_str.replace('-','')}",
        "source": "nightly-rollup",
        "type": "audit",
        "urgency": urgency,
        "title": f"Nightly Rollup — {date_str} — {status}",
        "finding": finding,
        "status": "PENDING"
    })

    if isinstance(inbox, list):
        save_json(INBOX_PATH, items)
    else:
        inbox["items"] = items
        save_json(INBOX_PATH, inbox)


# ── Step 7: write heartbeat entry ─────────────────────────────────────────────

def write_heartbeat(status, notes):
    data = load_json(HEARTBEAT_PATH)
    if not isinstance(data, dict) or "entries" not in data:
        data = {"_schema": "1.0", "entries": []}
    data["entries"].append({
        "date": datetime.now().isoformat(),
        "agent": "nightly-rollup",
        "status": status,
        "notes": notes
    })
    save_json(HEARTBEAT_PATH, data)


# ── Step 8: update session-handoff.md ────────────────────────────────────────

def update_handoff(date_str, status, score):
    line = f"System tightness last reviewed: {date_str} — {status} ({score}/100)"
    try:
        with open(HANDOFF_PATH, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        import re
        pattern = r"System tightness last reviewed:.*"
        if re.search(pattern, content):
            content = re.sub(pattern, line, content)
        else:
            content = content.rstrip() + f"\n{line}\n"
        with open(HANDOFF_PATH, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        log(f"WARNING: could not update session-handoff.md: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log("Nightly rollup starting")
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    generated_at = now.isoformat()

    # Step 1 — audit summary
    audit_summary = summarize_24h()
    log(f"Audit: {audit_summary['total_entries']} entries, "
        f"{audit_summary['gate_decisions']['failed']} gate fails")

    # Step 2 — agent check-ins
    checked_in, missed = get_agent_checkins()
    log(f"Check-ins: {len(checked_in)} agents in, {len(missed)} missed: {missed}")

    # Step 3 — pending counts
    pending_inbox = count_pending_inbox()
    pending_flags = count_pending_flags()
    log(f"Inbox: {pending_inbox} pending | Flags: {pending_flags} pending")

    # Step 4 — health score
    score, status, deductions = compute_health(audit_summary, missed, pending_flags)
    top_issue = audit_summary.get("top_failure_category")
    notes_parts = [f"{len(checked_in)} agents in"]
    if missed:
        notes_parts.append(f"missed: {', '.join(missed)}")
    if deductions:
        notes_parts.append(deductions[0])
    summary_note = " | ".join(notes_parts)
    log(f"Health: {status} {score}/100 — {summary_note}")

    # Step 5 — write digest
    write_digest(date_str, generated_at, audit_summary, checked_in, missed,
                 pending_inbox, pending_flags, score, status, summary_note)
    log("Digest entry written to daily-digest.json")

    # Step 6 — supervisor briefing
    write_supervisor_briefing(date_str, score, status, checked_in, missed,
                               audit_summary, top_issue)
    log("Supervisor briefing written to supervisor-inbox.json")

    # Step 7 — heartbeat
    hb_notes = f"[nightly-rollup] {status} {score}/100 — digest written"
    write_heartbeat("clean" if score >= 80 else "flagged", hb_notes)
    log("Heartbeat written")

    # Step 8 — update handoff
    update_handoff(date_str, status, score)
    log("session-handoff.md updated")

    # Step 8b — update STUDIO_BRIEFING.md timestamp and health line
    try:
        briefing_path = os.path.join(STUDIO, "STUDIO_BRIEFING.md")
        if os.path.exists(briefing_path):
            import re as _re
            content = open(briefing_path, encoding="utf-8", errors="replace").read()
            # Update the date line at top
            content = _re.sub(
                r"\*Updated: [\d-]+ \|",
                f"*Updated: {date_str} |",
                content
            )
            # Update system health line if present
            health_line = f"**System Health:** {status} {score}/100 (as of {date_str})"
            if "**System Health:**" in content:
                content = _re.sub(r"\*\*System Health:\*\*.*", health_line, content)
            open(briefing_path, "w", encoding="utf-8").write(content)
    except Exception as e:
        log(f"WARNING: could not update STUDIO_BRIEFING.md: {e}")

    # Step 9 — audit log entry
    sys.path.insert(0, os.path.join(STUDIO, "utilities"))
    try:
        from audit_logger import log_action
        log_action(
            agent="nightly-rollup",
            action_type="rollup",
            target="daily-digest.json",
            result="pass",
            notes=f"{status} score={score}/100 entries={audit_summary['total_entries']}"
        )
        log("Audit entry written")
    except Exception as e:
        log(f"WARNING: audit log write failed: {e}")

    log(f"Nightly rollup complete: {status} {score}/100")


if __name__ == "__main__":
    main()
