"""
wire_hamilton.py — Automated Hamilton Rule enforcement across all scheduled agents.

For each .py file registered with Windows Task Scheduler under Studio\:
1. Reads the file to determine a reasonable EXPECTED_RUNTIME_SECONDS
2. Injects the TTL header comment if missing
3. Wraps the main() or entry point with @hamilton_watchdog if missing
4. Skips utility files and files already compliant

Run: python wire_hamilton.py [--dry-run] [--file path/to/agent.py]
     --dry-run  : show what would change, don't write
     --file     : target one specific file

# EXPECTED_RUNTIME_SECONDS: 30
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "utilities"))
from constraint_gates import log_violation

STUDIO = Path("G:/My Drive/Projects/_studio")

# TTL budgets by agent type (seconds). Used when no existing runtime hint found.
TTL_BUDGETS = {
    "harvest":      600,
    "scraper":      480,
    "crawler":      480,
    "intel":        300,
    "score":        180,
    "whiteboard":   180,
    "rank":         120,
    "archaeology":  600,
    "agency":       120,
    "commit":        60,
    "rollup":       180,
    "briefing":     120,
    "reindex":      300,
    "digest":        60,
    "drift":         60,
    "validator":    120,
    "health":        60,
    "supervisor":   120,
    "wasde":        300,
    "sanctions":    300,
    "default":      300,
}

SKIP_FILES = {
    "constraint_gates.py", "constraint_audit.py", "wire_hamilton.py",
    "session_logger.py", "unicode_safe.py", "scraper_utils.py",
    "ollama_utils.py", "gemini_utils.py", "workflow_hook.py",
    "audit_logger.py", "heartbeat.py", "ai_gateway.py",
    "session-startup.py", "session_bridge.py",
}

IMPORT_BLOCK = '''import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog
'''


def get_scheduled_scripts() -> list[Path]:
    """
    Returns the definitive list of agent Python scripts that run via Task Scheduler.
    Built from direct inspection of tasks and known bat-file targets.
    """
    direct = [
        STUDIO / "model_validator.py",
        STUDIO / "sanctions_ingestor.py",
        STUDIO / "wasde_parser.py",
        STUDIO / "serve_sidebar_server.py",
        STUDIO / "studio_bridge.py",
        STUDIO / "ai_intel_run.py",
        STUDIO / "ai_news_scraper.py",
        STUDIO / "product_archaeology_run.py",
        STUDIO / "vintage_agent.py",
        STUDIO / "whiteboard_score.py",
        STUDIO / "auto_answer_gemini.py",
        STUDIO / "nightly_rollup.py",
        STUDIO / "vector_reindex.py",
        STUDIO / "check-drift.py",
        STUDIO / "git_commit.py",
        STUDIO / "janitor_run.py",
        STUDIO / "inject_sidebar_data.py",
        STUDIO / "ai_services_rankings.py",
        STUDIO / "run_inbox_sync.py",
        STUDIO / "send_digest_to_inbox.py",
    ]
    return [p for p in direct if p.exists()]


def guess_ttl(path: Path) -> int:
    """Guess appropriate TTL from filename keywords."""
    name = path.stem.lower()
    for keyword, ttl in TTL_BUDGETS.items():
        if keyword in name:
            return ttl
    return TTL_BUDGETS["default"]


def already_compliant(text: str) -> bool:
    """Return True if file already has Hamilton wiring."""
    return bool(
        re.search(r'EXPECTED_RUNTIME_SECONDS', text) or
        re.search(r'hamilton_watchdog', text)
    )


def find_main_def(text: str) -> tuple[int, str] | None:
    """Find main() OR run() function definition — either counts as entry point."""
    for i, line in enumerate(text.splitlines()):
        if re.match(r'^def (main|run)\s*\(', line):
            return i, line
    return None


def inject_hamilton(path: Path, dry_run: bool = False) -> str:
    """
    Inject Hamilton TTL header + watchdog decorator into one agent file.
    Returns 'skipped', 'already_compliant', 'patched', or 'no_main'.
    """
    if path.name in SKIP_FILES:
        return "skipped"

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"read_error:{e}"

    if already_compliant(text):
        return "already_compliant"

    ttl = guess_ttl(path)
    main_info = find_main_def(text)

    lines = text.splitlines(keepends=True)

    # --- 1. Inject TTL header comment after first docstring or at line 1 ---
    insert_header_at = 0
    # Find end of module docstring if present
    if lines and lines[0].strip().startswith('"""'):
        for i, l in enumerate(lines):
            if i > 0 and '"""' in l:
                insert_header_at = i + 1
                break
    elif lines and lines[0].strip().startswith("'''"):
        for i, l in enumerate(lines):
            if i > 0 and "'''" in l:
                insert_header_at = i + 1
                break

    header_line = f"\n# EXPECTED_RUNTIME_SECONDS: {ttl}\n"
    lines.insert(insert_header_at, header_line)

    # Reparse after header insertion
    text = "".join(lines)
    lines = text.splitlines(keepends=True)

    # --- 2. Inject import block after last existing import ---
    last_import = 0
    for i, l in enumerate(lines):
        if re.match(r'^(import |from )', l):
            last_import = i
    lines.insert(last_import + 1, "\n" + IMPORT_BLOCK)
    text = "".join(lines)
    lines = text.splitlines(keepends=True)

    # --- 3. Inject @hamilton_watchdog decorator before def main() ---
    main_info = find_main_def(text)
    if main_info:
        main_line_idx, _ = main_info
        decorator = f'@hamilton_watchdog("{path.stem}", expected_seconds={ttl})\n'
        lines.insert(main_line_idx, decorator)
        text = "".join(lines)
        status = "patched"
    else:
        # No main() — still add header + import, flag for manual review
        status = "patched_no_main"

    if not dry_run:
        path.write_text(text, encoding="utf-8")

    return status


def main():
    parser = argparse.ArgumentParser(description="Hamilton Rule auto-wirer for scheduled agents")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--file", type=str, help="Target a single file instead of all scheduled scripts")
    args = parser.parse_args()

    if args.file:
        targets = [Path(args.file)]
        print(f"[wire_hamilton] Targeting single file: {args.file}")
    else:
        targets = get_scheduled_scripts()
        print(f"[wire_hamilton] Found {len(targets)} scheduled agent scripts")

    if not targets:
        print("[wire_hamilton] No targets found. Check Task Scheduler paths.")
        return

    results = {"patched": [], "already_compliant": [], "skipped": [],
                "patched_no_main": [], "errors": []}

    for path in targets:
        status = inject_hamilton(path, dry_run=args.dry_run)
        category = status if status in results else "errors"
        results[category].append(path.name)
        symbol = {"patched": "+", "already_compliant": "-", "skipped": ".",
                  "patched_no_main": "!", "errors": "X"}.get(status, "?")
        print(f"  [{symbol}] {path.name}: {status}")

    print(f"\n[wire_hamilton] SUMMARY")
    print(f"  Patched:           {len(results['patched'])}")
    print(f"  Patched (no main): {len(results['patched_no_main'])} — needs manual review")
    print(f"  Already compliant: {len(results['already_compliant'])}")
    print(f"  Skipped (utility): {len(results['skipped'])}")
    print(f"  Errors:            {len(results['errors'])}")

    if args.dry_run:
        print("\n[wire_hamilton] DRY RUN — no files written")
    else:
        # Log to supervisor inbox
        try:
            from constraint_gates import hopper_append
            if results["patched"] or results["patched_no_main"]:
                hopper_append(
                    str(STUDIO / "supervisor-inbox.json"),
                    {
                        "id": f"HAMILTON-WIRE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "source": "wire_hamilton",
                        "type": "constraint_enforcement",
                        "urgency": "low",
                        "title": f"Hamilton wired: {len(results['patched'])} agents patched",
                        "finding": (
                            f"Patched: {', '.join(results['patched'][:5])}{'...' if len(results['patched']) > 5 else ''}. "
                            f"Manual review needed: {', '.join(results['patched_no_main'])}"
                        ),
                        "status": "pending",
                        "date": datetime.now().isoformat()
                    }
                )
        except Exception as e:
            print(f"  [inbox] write failed: {e}")

        # Append to claude-status.txt
        try:
            with open(STUDIO / "claude-status.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"[HAMILTON-WIRE] patched={len(results['patched'])} "
                    f"no_main={len(results['patched_no_main'])} "
                    f"compliant={len(results['already_compliant'])}\n"
                )
        except Exception:
            pass

    return results


if __name__ == "__main__":
    main()
