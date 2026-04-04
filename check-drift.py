"""
check-drift.py — Studio Project Drift Monitor
Runs daily at 06:00 AM via Task Scheduler (Studio/CheckDrift).
Scans all project state.json files for staleness.
Flags any project not touched in 14+ days as drift_risk: HIGH.
Writes findings to supervisor-inbox.json and updates each state.json.

Usage:
    python check-drift.py
"""

# EXPECTED_RUNTIME_SECONDS: 60

import json
import os
import sys
from datetime import datetime, timedelta

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

STUDIO_ROOT  = "G:/My Drive/Projects/_studio"
PROJECTS_ROOT = "G:/My Drive/Projects"
INBOX_FILE   = os.path.join(STUDIO_ROOT, "supervisor-inbox.json")
HB_FILE      = os.path.join(STUDIO_ROOT, "heartbeat-log.json")

DRIFT_THRESHOLD_DAYS = 14

PROJECTS = {
    "acuscan-ar":         "acuscan-ar-state.json",
    "arbitrage-pulse":    "arbitrage-pulse-state.json",
    "CTW":                "state.json",
    "hibid-analyzer":     "hibid-analyzer-state.json",
    "job-match":          "state.json",
    "listing-optimizer":  "listing-optimizer-state.json",
    "nutrimind":          "nutrimind-state.json",
    "sentinel-core":      "state.json",
    "sentinel-performer": "state.json",
    "sentinel-viewer":    "state.json",
    "squeeze-empire":     "squeeze-empire-state.json",
    "whatnot-apps":       "whatnot-apps-state.json",
}

# Known date fields across schema variants
DATE_FIELDS = ["last_touched", "_last_updated", "lastUpdated", "last_updated", "_created"]


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def get_date_value(state):
    """Return the best available date string from a state dict."""
    for field in DATE_FIELDS:
        val = state.get(field)
        if val and isinstance(val, str) and len(val) >= 10:
            return val[:10]
    # Try nested project.last_updated
    proj = state.get("project", {})
    if isinstance(proj, dict):
        for field in DATE_FIELDS:
            val = proj.get(field)
            if val and isinstance(val, str) and len(val) >= 10:
                return val[:10]
    return None


def compute_drift(date_str):
    """Return (age_days, risk_level) for a date string."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        age = (datetime.now() - dt).days
        risk = "HIGH" if age >= DRIFT_THRESHOLD_DAYS else "LOW"
        return age, risk
    except Exception:
        return 999, "HIGH"


def write_heartbeat(status, notes):
    data = load_json(HB_FILE)
    if not isinstance(data, dict) or "entries" not in data:
        data = {"_schema": "1.0", "_description": "Daily agent checkin log", "entries": []}
    data["entries"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "agent": "check-drift",
        "status": status,
        "notes": notes
    })
    save_json(HB_FILE, data)


def write_inbox(findings):
    """Write one inbox item summarising all HIGH drift projects."""
    data = load_json(INBOX_FILE)
    if not isinstance(data, dict) or "items" not in data:
        data = {"_schema": "1.0", "items": []}

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    names = [f["project"] for f in findings]
    ages  = [f"{f['project']} ({f['age_days']}d)" for f in findings]

    data["items"].append({
        "id":      f"drift-alert-{ts}",
        "source":  "check-drift",
        "type":    "audit",
        "urgency": "WARN",
        "title":   f"Drift Alert — {len(findings)} project(s) stale 14+ days",
        "finding": f"Projects not touched in {DRIFT_THRESHOLD_DAYS}+ days: {', '.join(ages)}. "
                   "Update state.json or mark as inactive.",
        "status":  "PENDING",
        "date":    datetime.now().isoformat(),
        "affected_projects": names,
    })
    save_json(INBOX_FILE, data)


@hamilton_watchdog("check-drift", expected_seconds=60)
def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    results   = []
    high_risk = []
    errors    = []

    for project, fname in PROJECTS.items():
        state_path = os.path.join(PROJECTS_ROOT, project, fname)

        if not os.path.exists(state_path):
            # Try alternate name
            alt = os.path.join(PROJECTS_ROOT, project, "state.json")
            if os.path.exists(alt):
                state_path = alt
            else:
                errors.append(f"{project}: state file not found")
                continue

        state = load_json(state_path)
        if state is None:
            errors.append(f"{project}: JSON parse error")
            continue

        date_val = get_date_value(state)
        if date_val is None:
            date_val = today_str  # Treat unknown as touched today — conservative
            age, risk = 0, "LOW"
        else:
            age, risk = compute_drift(date_val)

        # Update last_touched and drift_risk in state file
        if isinstance(state.get("project"), dict):
            state["project"]["last_touched"] = date_val
            state["project"]["drift_risk"]   = risk
        else:
            state["last_touched"] = date_val
            state["drift_risk"]   = risk

        save_json(state_path, state)

        entry = {"project": project, "last_touched": date_val, "age_days": age, "drift_risk": risk}
        results.append(entry)
        if risk == "HIGH":
            high_risk.append(entry)

        print(f"  {'!' if risk == 'HIGH' else ' '} {project}: {date_val} ({age}d) — {risk}")

    # Write inbox alert if any HIGH drift found
    if high_risk:
        write_inbox(high_risk)
        print(f"\nINBOX ALERT: {len(high_risk)} project(s) flagged as drift_risk: HIGH")
    else:
        print("\nAll projects within drift threshold. No inbox alert.")

    status  = "flagged" if high_risk else "clean"
    summary = f"{len(high_risk)}/{len(results)} projects drift_risk HIGH"
    write_heartbeat(status, f"[check-drift] {summary}")

    # Audit log
    try:
        sys.path.insert(0, os.path.join(STUDIO_ROOT, "utilities"))
        from audit_logger import log_action
        log_action(
            agent="check-drift",
            action_type="rollup",
            target="supervisor-inbox.json",
            result="flagged" if high_risk else "clean",
            findings_count=len(high_risk),
            notes=f"[check-drift] {summary}"
        )
    except Exception as e:
        print(f"[check-drift] audit log failed (non-fatal): {e}")

    # Session logger
    try:
        from session_logger import complete_task
        complete_task(
            task_name="check-drift",
            result_summary=summary,
            next_recommended="Review supervisor inbox for drift alerts" if high_risk else ""
        )
    except Exception as e:
        print(f"[check-drift] session_logger failed (non-fatal): {e}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  ! {e}")

    print(f"\nDrift check complete. {summary}.")


if __name__ == "__main__":
    main()
