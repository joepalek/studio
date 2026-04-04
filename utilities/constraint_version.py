"""
constraint_version.py — Constraint versioning system.

Tracks the version of the constraint ruleset active during every agent decision.
Enables quality delta measurement as constraints are tuned over time.

Named in response to the Anthropic Expert recommendation:
  'Once five constraints are enforced, implement constraint versioning.
   Version constraints in code, log constraint_version with every decision.
   Measure quality delta per version as the studio evolves.'

Usage:
    from constraint_version import get_version, log_decision_with_version, get_version_history

# EXPECTED_RUNTIME_SECONDS: 5
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

STUDIO_ROOT   = Path("G:/My Drive/Projects/_studio")
VERSION_FILE  = STUDIO_ROOT / "constraint-version.json"
DECISION_LOG  = STUDIO_ROOT / "decision-log.json"
STATUS_FILE   = STUDIO_ROOT / "claude-status.txt"

# ─────────────────────────────────────────────────────────────────
# CONSTRAINT REGISTRY — single source of truth for active rules
# Bump version string whenever any rule changes threshold or logic
# ─────────────────────────────────────────────────────────────────

CONSTRAINT_REGISTRY = {
    "version": "1.2.0",
    "released": "2026-04-04",
    "constraints": {
        "shannon":    {"mode": "enforced", "threshold": 200,   "unit": "tokens",  "gate": "shannon_check"},
        "hamilton":   {"mode": "enforced", "threshold": 1.5,   "unit": "ttl_multiplier", "gate": "hamilton_watchdog"},
        "hopper":     {"mode": "enforced", "threshold": None,  "unit": "schema",  "gate": "hopper_validate"},
        "kay":        {"mode": "enforced", "threshold": None,  "unit": "pattern", "gate": "kay_validate"},
        "codd":       {"mode": "enforced", "threshold": 0.95,  "unit": "confidence", "gate": "codd_gate"},
        "lovelace":   {"mode": "enforced", "threshold": None,  "unit": "baseline_ref", "gate": "lovelace_start"},
        "bezos":      {"mode": "enforced", "threshold": 3,     "unit": "consecutive_failures", "gate": "circuit_breaker"},
        "compounding":{"mode": "enforced", "threshold": 3,     "unit": "attempts", "gate": "compounding_guard"},
        "turing":     {"mode": "enforced", "threshold": 1,     "unit": "min_citations", "gate": "turing_check"},
    },
    "changelog": [
        {"version": "1.0.0", "date": "2026-04-04",
         "change": "Initial enforcement — Shannon, Hamilton, Hopper, Kay, Codd, Lovelace, Bezos, Compounding"},
        {"version": "1.1.0", "date": "2026-04-04",
         "change": "Phase 2 validation: Codd VALIDATES (+22.9% predicted). Shannon gate applied live (356t->200t)"},
        {"version": "1.2.0", "date": "2026-04-04",
         "change": "Turing Rule added — source citation enforcement on all assessment/extraction outputs"},
    ]
}


def _compute_registry_hash() -> str:
    """Stable hash of current constraint thresholds — changes when any rule is tuned."""
    payload = json.dumps(
        {k: v["threshold"] for k, v in CONSTRAINT_REGISTRY["constraints"].items()},
        sort_keys=True
    )
    return hashlib.md5(payload.encode()).hexdigest()[:8]


def get_version() -> str:
    """Return current constraint version string. Format: vMAJOR.MINOR.PATCH+HASH"""
    h = _compute_registry_hash()
    return f"v{CONSTRAINT_REGISTRY['version']}+{h}"


def get_active_constraints() -> dict:
    """Return full constraint registry for the current version."""
    return {
        "version":     get_version(),
        "released":    CONSTRAINT_REGISTRY["released"],
        "constraints": CONSTRAINT_REGISTRY["constraints"],
    }


def log_decision_with_version(
    decision_id: str,
    agent: str,
    decision_summary: str,
    outcome: Optional[str] = None,
    quality_signals: Optional[dict] = None
) -> dict:
    """
    Log an agent decision with its constraint_version stamp.
    This is the core of the versioning system — every significant
    decision is tagged so quality can be measured per version.

    Usage:
        from constraint_version import log_decision_with_version
        log_decision_with_version(
            decision_id="ga-legal-hellmaze-20260404",
            agent="game_archaeology_legal",
            decision_summary="Hellmaze assessed GREEN, confidence=0.88",
            quality_signals={"codd_passed": False, "turing_citations": 3}
        )
    """
    version = get_version()
    entry = {
        "decision_id":        decision_id,
        "constraint_version": version,
        "agent":              agent,
        "decision_summary":   decision_summary,
        "outcome":            outcome,
        "quality_signals":    quality_signals or {},
        "ts":                 datetime.now().isoformat(),
    }

    # Append to version-log.json
    version_log = STUDIO_ROOT / "constraint-version-log.json"
    records = []
    if version_log.exists():
        try:
            records = json.loads(version_log.read_text(encoding="utf-8"))
        except Exception:
            records = []
    records.append(entry)
    # Keep last 1000 entries
    if len(records) > 1000:
        records = records[-1000:]
    version_log.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    return entry


def get_version_history() -> list:
    """Return changelog of all constraint versions."""
    return CONSTRAINT_REGISTRY["changelog"]


def get_quality_delta_by_version(target_version: Optional[str] = None) -> dict:
    """
    Aggregate quality signals from version-log.json grouped by constraint_version.
    Useful for measuring actual quality improvement as constraints are tuned.

    Returns dict: {version: {total_decisions, codd_pass_rate, turing_avg_citations, ...}}
    """
    version_log = STUDIO_ROOT / "constraint-version-log.json"
    if not version_log.exists():
        return {}

    try:
        records = json.loads(version_log.read_text(encoding="utf-8"))
    except Exception:
        return {}

    # Group by version
    by_version: dict = {}
    for r in records:
        v = r.get("constraint_version", "unknown")
        if target_version and v != target_version:
            continue
        if v not in by_version:
            by_version[v] = {
                "total_decisions": 0,
                "codd_pass": 0, "codd_fail": 0,
                "turing_citations": [],
                "agents": set(),
            }
        grp = by_version[v]
        grp["total_decisions"] += 1
        grp["agents"].add(r.get("agent", "?"))
        qs = r.get("quality_signals", {})
        if "codd_passed" in qs:
            if qs["codd_passed"]:
                grp["codd_pass"] += 1
            else:
                grp["codd_fail"] += 1
        if "turing_citations" in qs:
            grp["turing_citations"].append(qs["turing_citations"])

    # Compute rates
    result = {}
    for v, g in by_version.items():
        total = g["total_decisions"]
        codd_checked = g["codd_pass"] + g["codd_fail"]
        cites = g["turing_citations"]
        result[v] = {
            "total_decisions":      total,
            "codd_pass_rate":       round(g["codd_pass"] / codd_checked, 3) if codd_checked else None,
            "turing_avg_citations": round(sum(cites) / len(cites), 2) if cites else None,
            "agents_active":        list(g["agents"]),
        }
    return result


def save_version_snapshot():
    """
    Write current constraint version state to constraint-version.json.
    Call this after any rule change to create a persistent snapshot.
    """
    snapshot = {
        "snapshot_ts":   datetime.now().isoformat(),
        "version":       get_version(),
        "registry":      get_active_constraints(),
        "changelog":     get_version_history(),
        "registry_hash": _compute_registry_hash(),
    }
    VERSION_FILE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return snapshot


def bump_version(change_description: str, bump: str = "patch"):
    """
    Increment version and add changelog entry.
    bump: 'major', 'minor', or 'patch'

    Usage:
        from constraint_version import bump_version
        bump_version("Raised Codd threshold from 0.95 to 0.97", bump="minor")
    """
    parts = CONSTRAINT_REGISTRY["version"].split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump == "major":
        major += 1; minor = 0; patch = 0
    elif bump == "minor":
        minor += 1; patch = 0
    else:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    today = datetime.now().strftime("%Y-%m-%d")

    CONSTRAINT_REGISTRY["version"] = new_version
    CONSTRAINT_REGISTRY["released"] = today
    CONSTRAINT_REGISTRY["changelog"].append({
        "version": new_version,
        "date":    today,
        "change":  change_description,
    })

    save_version_snapshot()

    try:
        with open(STATUS_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"[CONSTRAINT-VERSION] bumped to v{new_version}: {change_description[:60]}\n"
            )
    except Exception:
        pass

    print(f"[constraint_version] Version bumped: v{new_version} — {change_description}")
    return new_version
