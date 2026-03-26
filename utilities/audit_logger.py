"""
audit_logger.py — Studio Master Audit Log
Append-only. Atomic writes via file lock. Never overwrites.

Usage:
    from utilities.audit_logger import log_action

    log_action(
        agent="stress-tester",
        action_type="pre-write-gate",
        target="studio.html",
        result="fail",
        findings_count=3,
        notes="scope creep detected"
    )
"""

import json
import os
import time
import threading
from datetime import datetime

STUDIO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_FILE  = os.path.join(STUDIO_ROOT, "master-audit.json")

_lock = threading.Lock()


def _generate_id(agent: str, sequence_hint: int = 0) -> str:
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M")
    agent_slug = agent.replace("-", "").replace("_", "")[:12]
    seq = str(sequence_hint).zfill(3)
    return f"ACT-{date_part}-{time_part}-{agent_slug}-{seq}"


def _load_audit() -> dict:
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted file — preserve by renaming, start fresh
            backup = AUDIT_FILE + f".bak-{int(time.time())}"
            os.rename(AUDIT_FILE, backup)
    return {
        "_schema": "1.0",
        "_description": "Studio master audit log — append only",
        "_note": "Never overwrite. Entries are permanent record.",
        "entries": []
    }


def log_action(
    agent: str,
    action_type: str,
    target: str,
    result: str,
    findings_count: int = 0,
    notes: str = "",
    session_id: str = ""
) -> str:
    """
    Append one audit entry to master-audit.json.

    Parameters
    ----------
    agent         : which agent took the action
    action_type   : pre-write-gate | post-write-gate | heartbeat | lateral-flag |
                    peer-review | scheduler-fire | inbox-write | nit-test | rollup
    target        : file, agent, or system acted on
    result        : pass | fail | clean | flagged | promoted | dismissed
    findings_count: number of findings (for gate decisions)
    notes         : one-line summary or empty
    session_id    : Claude Code session ID for correlation (optional)

    Returns
    -------
    str : the generated ACT-... ID
    """
    valid_types = {
        "pre-write-gate", "post-write-gate", "heartbeat", "lateral-flag",
        "peer-review", "scheduler-fire", "inbox-write", "nit-test", "rollup"
    }
    if action_type not in valid_types:
        action_type = "rollup"  # safe fallback

    with _lock:
        data = _load_audit()
        seq = len(data["entries"])
        entry_id = _generate_id(agent, seq)

        entry = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action_type": action_type,
            "target": target,
            "result": result,
            "findings_count": findings_count,
            "notes": notes[:200] if notes else "",
            "session_id": session_id
        }

        data["entries"].append(entry)

        # Atomic write: write to temp, then rename
        tmp_path = AUDIT_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, AUDIT_FILE)

    return entry_id


def get_recent(hours: int = 24, agent: str = None, action_type: str = None) -> list:
    """Return entries from the last N hours, optionally filtered."""
    cutoff = datetime.now().timestamp() - (hours * 3600)
    data = _load_audit()
    results = []
    for entry in data.get("entries", []):
        try:
            ts = datetime.fromisoformat(entry["timestamp"]).timestamp()
            if ts < cutoff:
                continue
        except (KeyError, ValueError):
            continue
        if agent and entry.get("agent") != agent:
            continue
        if action_type and entry.get("action_type") != action_type:
            continue
        results.append(entry)
    return results


def summarize_24h() -> dict:
    """Produce a summary dict for the last 24 hours — used by nightly-rollup."""
    entries = get_recent(24)
    gate_entries    = [e for e in entries if e["action_type"] in ("pre-write-gate", "post-write-gate")]
    sched_entries   = [e for e in entries if e["action_type"] == "scheduler-fire"]
    heartbeats      = [e for e in entries if e["action_type"] == "heartbeat"]
    inbox_entries   = [e for e in entries if e["action_type"] == "inbox-write"]
    flag_entries    = [e for e in entries if e["action_type"] == "lateral-flag"]

    gate_passed = sum(1 for e in gate_entries if e["result"] == "pass")
    sched_confirmed = sum(1 for e in sched_entries if e["result"] in ("pass", "clean"))

    # Top failure category
    fail_notes = [e.get("notes","") for e in entries if e["result"] in ("fail","flagged") and e.get("notes")]
    top_failure = fail_notes[0][:60] if fail_notes else None

    return {
        "total_entries": len(entries),
        "gate_decisions": {
            "total": len(gate_entries),
            "passed": gate_passed,
            "failed": len(gate_entries) - gate_passed
        },
        "scheduler_fires": {
            "total": len(sched_entries),
            "confirmed": sched_confirmed,
            "silent": len(sched_entries) - sched_confirmed
        },
        "heartbeats": len(heartbeats),
        "inbox_items_written": len(inbox_entries),
        "flags_raised": len(flag_entries),
        "top_failure_category": top_failure
    }
