"""
constraint_audit.py — SRE compliance scanner for constraint gates.

Scans all agent scripts in the studio for missing constraint enforcement.
Reports violations to supervisor-inbox.json.

Run manually:  python constraint_audit.py
Scheduled:     Add to Windows Task Scheduler (weekly, Monday 07:00)

# EXPECTED_RUNTIME_SECONDS: 60
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "utilities"))
from constraint_gates import hopper_append, log_violation

STUDIO_ROOT  = Path("G:/My Drive/Projects/_studio")
AUDIT_REPORT = STUDIO_ROOT / "constraint-audit.json"

# Files intentionally exempt from Bezos audit
BEZOS_EXEMPT = {
    "ai_gateway.py",          # IS the router — intentional loops
    "constraint_gates.py",    # utility — intentional
    "constraint_audit.py",    # this file
    "wire_bezos.py", "wire_hamilton.py", "wire_hopper.py", "wire_codd.py",
    "update_asset_usage.py",  # iterates JSON data, no API calls
    "test_groq_debug.py",     # one-shot debug script
    "test_cerebras2.py",
    "test_connections.py",
    "test_fallback.py",
    "debug_search.py",
}

CODD_SCOPE_PATTERNS = [
    "*hibid*", "*arbitrage*", "*listing_optim*", "*ai_scout*",
    "*ghost_book*", "*ai_intel*", "*market_scout*", "*vintage_agent*",
    "*product_archaeology*", "*wayback*", "*job_source_crawler*",
    "*product_archaeology_run*", "*ai_intel_run*",
]


def scan_file(path: Path) -> dict:
    """Scan one Python file for constraint gate usage."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"path": str(path), "error": str(e)}

    return {
        "path": str(path),
        "has_circuit_breaker": bool(re.search(
            r'MAX_CONSECUTIVE_FAILURES|circuit.breaker|consecutive_fail', text, re.I)),
        "has_codd_gate":  bool(re.search(
            r'codd_gate|codd_check|from constraint_gates', text, re.I)),
        "has_hopper":     bool(re.search(
            r'hopper_append|hopper_validate|from constraint_gates', text, re.I)),
        "has_hamilton":   bool(re.search(
            r'hamilton_watchdog|EXPECTED_RUNTIME_SECONDS', text, re.I)),
        "has_turing":     bool(re.search(
            r'turing_check|turing_wrap|from turing_gate', text, re.I)),
        "writes_inbox_raw": bool(re.search(
            r'json\.dump.*inbox|open.*inbox.*["\']w["\']', text, re.I)),
        "loops_api_calls":  bool(re.search(
            r'for\s+\w+\s+in\s+\w+.*?:\s*\n.*?(gemini|anthropic|openrouter|groq)',
            text, re.I | re.S)),
    }


def audit_all() -> dict:
    """Scan all .py files in studio root and key subdirs."""
    scan_roots = [
        STUDIO_ROOT,
        STUDIO_ROOT / "utilities",
        STUDIO_ROOT / "agency",
        STUDIO_ROOT / "game_archaeology",
        STUDIO_ROOT / "automation",
    ]

    violations = []
    scanned = 0

    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.py")):
            if "__pycache__" in str(path):
                continue
            result = scan_file(path)
            scanned += 1

            # Bezos: API loop without circuit breaker
            if (result.get("loops_api_calls")
                    and not result.get("has_circuit_breaker")
                    and path.name not in BEZOS_EXEMPT):
                violations.append({
                    "file": result["path"],
                    "rule": "BEZOS",
                    "issue": "API loop without circuit breaker",
                    "fix": "Add MAX_CONSECUTIVE_FAILURES pattern — see constraint_gates.py docs"
                })

            # Hopper: raw inbox write without validation
            if result.get("writes_inbox_raw") and not result.get("has_hopper"):
                violations.append({
                    "file": result["path"],
                    "rule": "HOPPER",
                    "issue": "Raw inbox write — no hopper_append",
                    "fix": "Replace json.dump to inbox with hopper_append()"
                })

            # Codd: extraction agent missing decorator
            for pattern in CODD_SCOPE_PATTERNS:
                if path.match(pattern) and not result.get("has_codd_gate"):
                    violations.append({
                        "file": result["path"],
                        "rule": "CODD",
                        "issue": "Extraction agent missing @codd_gate",
                        "fix": "Wrap extraction functions with @codd_gate from constraint_gates"
                    })
                    break

            # Turing: legal/assessment agents missing citation checks
            if (re.search(r'legal|assess|reasoning|extract', path.stem, re.I)
                    and not result.get("has_turing")
                    and path.name not in BEZOS_EXEMPT):
                violations.append({
                    "file": result["path"],
                    "rule": "TURING",
                    "issue": "Assessment/extraction agent missing turing_check",
                    "fix": "Import turing_check from utilities/turing_gate.py and check output"
                })

    return {"scanned": scanned, "violations": violations, "ts": datetime.now().isoformat()}


def main():
    print("[constraint_audit] Scanning studio agents...")
    report = audit_all()

    with open(AUDIT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[constraint_audit] Scanned {report['scanned']} files | "
          f"{len(report['violations'])} violations found")

    # Load existing inbox — resolve stale audit items before adding new ones
    inbox_path = STUDIO_ROOT / "supervisor-inbox.json"
    try:
        existing = json.loads(inbox_path.read_text(encoding="utf-8"))
    except Exception:
        existing = []

    # Mark old audit items as resolved (don't delete — keep audit trail)
    audit_prefixes = ("AUDIT-BEZOS-", "AUDIT-HOPPER-", "AUDIT-CODD-",
                      "AUDIT-TURING-", "AUDIT-HAMILTON-")
    for item in existing:
        if (any(item.get("id", "").startswith(p) for p in audit_prefixes)
                and item.get("status") == "pending"):
            item["status"] = "resolved"
            item["resolved_at"] = datetime.now().isoformat()
            item["resolution"] = "constraint_audit_pass"

    # Only push NEW violations not already in inbox
    existing_ids = {i.get("id") for i in existing}
    new_violations = 0
    for v in report["violations"]:
        vid = (f"AUDIT-{v['rule']}-{Path(v['file']).stem}-"
               f"{datetime.now().strftime('%Y%m%d%H%M%S')}")
        print(f"  [{v['rule']}] {Path(v['file']).name}: {v['issue']}")
        if vid not in existing_ids:
            try:
                hopper_append(
                    str(inbox_path),
                    {
                        "id": vid,
                        "source": "constraint_audit",
                        "type": "constraint_violation",
                        "urgency": "medium",
                        "title": f"{v['rule']} missing: {Path(v['file']).name}",
                        "finding": f"{v['issue']} | Fix: {v['fix']}",
                        "status": "pending",
                        "date": datetime.now().isoformat()
                    }
                )
                new_violations += 1
            except Exception as e:
                print(f"  WARNING: inbox write failed: {e}")

    # Write back with resolved items updated
    if not report["violations"]:
        # Audit clean — write resolved items back
        inbox_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print("[constraint_audit] All scanned files: COMPLIANT — stale violations resolved")
    else:
        print(f"[constraint_audit] {new_violations} new violations pushed to inbox")

    try:
        with open(STUDIO_ROOT / "claude-status.txt", "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"[CONSTRAINT-AUDIT] scanned={report['scanned']} "
                f"violations={len(report['violations'])}\n"
            )
    except Exception:
        pass

    return report


if __name__ == "__main__":
    main()
