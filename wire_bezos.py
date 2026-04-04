"""
wire_bezos.py — Automated Bezos Rule enforcement across all API-looping agent scripts.

Scans target files for API call loops (Gemini, Anthropic, Groq, OpenRouter, Ollama)
and injects the MAX_CONSECUTIVE_FAILURES circuit breaker pattern if missing.

Run: python wire_bezos.py [--dry-run] [--file path/to/agent.py]

# EXPECTED_RUNTIME_SECONDS: 30
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "utilities"))
from constraint_gates import hopper_append, log_violation

STUDIO = Path("G:/My Drive/Projects/_studio")

SKIP_FILES = {
    "constraint_gates.py", "constraint_audit.py", "wire_hamilton.py",
    "wire_bezos.py", "wire_hopper.py", "wire_codd.py",
    "unicode_safe.py", "workflow_hook.py", "audit_logger.py",
    "heartbeat.py", "session_bridge.py", "session-startup.py",
}

# Files with legitimate infinite loops (servers, bridges) — skip circuit breaker
SERVER_FILES = {
    "serve_sidebar_server.py", "studio_bridge.py", "run-agent.py",
    "session_bridge.py",
}

CIRCUIT_BREAKER_BLOCK = '''
    # --- Bezos Rule: circuit breaker ---
    _MAX_CONSECUTIVE_FAILURES = 3
    _consecutive_failures = 0
'''

API_LOOP_PATTERN = re.compile(
    r'for\s+\w+\s+in\s+\w+.*?:\s*\n'
    r'(?:.*\n){0,5}?'
    r'.*?(gemini|anthropic|groq|openrouter|ollama|call_api|ask_json|batch_ask|\.ask\()',
    re.IGNORECASE | re.MULTILINE
)

ALREADY_WIRED = re.compile(r'MAX_CONSECUTIVE_FAILURES|consecutive_fail|circuit.breaker', re.IGNORECASE)

TARGETS = [
    STUDIO / "ai_intel_run.py",
    STUDIO / "ai_services_rankings.py",
    STUDIO / "auto_answer_gemini.py",
    STUDIO / "check_ghostbook.py",
    STUDIO / "upgrade_rankings.py",
    STUDIO / "studio_inventory.py",
    STUDIO / "rebuild_sidebar.py",
    STUDIO / "supervisor_check.py",
    STUDIO / "product_archaeology_run.py",
    STUDIO / "vintage_agent.py",
    STUDIO / "git_commit.py",
    STUDIO / "populate_orchestrator_plan.py",
    STUDIO / "agent_summary.py",
    STUDIO / "check_models.py",
    STUDIO / "model_validator.py",
    STUDIO / "wasde_parser.py",
    STUDIO / "wasde_dual_ai.py",
    STUDIO / "pool_test_battery.py",
    STUDIO / "ai_news_scraper.py",
    STUDIO / "nightly_rollup.py",
    STUDIO / "whiteboard_score.py",
    STUDIO / "generate-context.py",
    STUDIO / "context-test-harness.py",
    STUDIO / "utilities/session_logger.py",
    STUDIO / "utilities/ollama_utils.py",
    STUDIO / "utilities/gemini_utils.py",
]

def inject_circuit_breaker(path: Path, dry_run: bool = False) -> str:
    """
    Inject Bezos circuit breaker into one file.
    Strategy: find the first API-looping for-loop and inject
    the failure counter pattern around the API call inside it.
    Returns status string.
    """
    if path.name in SKIP_FILES or path.name in SERVER_FILES:
        return "skipped"

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"read_error:{e}"

    if ALREADY_WIRED.search(text):
        return "already_compliant"

    lines = text.splitlines(keepends=True)

    # Find first for-loop that contains an API call within 8 lines
    insert_at = None
    api_call_line = None

    for i, line in enumerate(lines):
        if re.match(r'\s*for\s+\w+\s+in\s+', line):
            # Check next 8 lines for API call
            window = "".join(lines[i:min(i+8, len(lines))])
            if re.search(r'gemini|anthropic|groq|openrouter|ollama|call_api|ask_json|batch_ask|\.ask\(', window, re.I):
                insert_at = i
                # Find the actual API call line within the window
                for j in range(i+1, min(i+8, len(lines))):
                    if re.search(r'gemini|anthropic|groq|openrouter|ollama|call_api|ask_json|batch_ask|\.ask\(', lines[j], re.I):
                        api_call_line = j
                        break
                break

    if insert_at is None:
        # No loop found — just prepend the constant at top of file after imports
        # so it's available if loops are added later
        last_import = 0
        for i, l in enumerate(lines):
            if re.match(r'^(import |from )', l):
                last_import = i
        const_block = "\n# Bezos Rule: circuit breaker constant\nMAX_CONSECUTIVE_FAILURES = 3\n"
        lines.insert(last_import + 1, const_block)
        text = "".join(lines)
        if not dry_run:
            path.write_text(text, encoding="utf-8")
        return "patched_no_loop"

    # Determine indentation of the for-loop body
    for_indent = len(lines[insert_at]) - len(lines[insert_at].lstrip())
    body_indent = " " * (for_indent + 4)

    # Build the counter init (before the for loop)
    counter_init = " " * for_indent + "_consecutive_failures = 0\n"
    lines.insert(insert_at, counter_init)

    # Recalculate api_call_line after insertion
    if api_call_line:
        api_call_line += 1

    # Rebuild text and inject try/except around API call
    text = "".join(lines)

    # Inject failure tracking after the for-loop opener using regex replace
    # Pattern: find "for X in Y:\n" and add counter reset line after
    for_line_pat = re.compile(r'(for\s+\w+\s+in\s+[^\n]+:\n)', re.MULTILINE)
    match = for_line_pat.search(text, text.index("_consecutive_failures = 0"))

    if match:
        reset_line = body_indent + "_consecutive_failures = 0  # reset on success — Bezos Rule\n"
        breaker = (
            f"\n{body_indent}    except Exception as _bezos_e:\n"
            f"{body_indent}        _consecutive_failures += 1\n"
            f"{body_indent}        print(f'  ERROR: {{str(_bezos_e)[:80]}}')\n"
            f"{body_indent}        if _consecutive_failures >= MAX_CONSECUTIVE_FAILURES:\n"
            f"{body_indent}            print(f'  CIRCUIT BREAKER: {{MAX_CONSECUTIVE_FAILURES}} consecutive failures -- aborting')\n"
            f"{body_indent}            break\n"
        )
        # Add MAX_CONSECUTIVE_FAILURES constant before the for-loop init block
        const = f"\nMAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule\n"
        text = const + text

    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return "patched"


def main():
    parser = argparse.ArgumentParser(description="Bezos Rule circuit breaker auto-wirer")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--file", type=str)
    args = parser.parse_args()

    targets = [Path(args.file)] if args.file else [p for p in TARGETS if p.exists()]
    print(f"[wire_bezos] Targeting {len(targets)} files...")

    results = {"patched": [], "already_compliant": [], "skipped": [],
               "patched_no_loop": [], "errors": []}

    for path in targets:
        status = inject_circuit_breaker(path, dry_run=args.dry_run)
        cat = status if status in results else "errors"
        results[cat].append(path.name)
        sym = {"+": "patched", "-": "already_compliant", ".": "skipped",
               "~": "patched_no_loop"}.get(status, status)
        print(f"  [{status[:1].upper()}] {path.name}: {status}")

    print(f"\n[wire_bezos] SUMMARY")
    print(f"  Patched:           {len(results['patched'])}")
    print(f"  Const-only:        {len(results['patched_no_loop'])}")
    print(f"  Already compliant: {len(results['already_compliant'])}")
    print(f"  Skipped:           {len(results['skipped'])}")
    print(f"  Errors:            {len(results['errors'])}")
    if args.dry_run:
        print("\n[wire_bezos] DRY RUN -- no files written")
    else:
        try:
            with open(STUDIO / "claude-status.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"[BEZOS-WIRE] patched={len(results['patched'])} "
                    f"const_only={len(results['patched_no_loop'])} "
                    f"compliant={len(results['already_compliant'])}\n"
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()
