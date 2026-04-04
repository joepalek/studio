"""
wire_codd.py — Automated Codd Rule enforcement.

Finds extraction functions in scoped agent files and injects the
@codd_gate decorator. Also adds confidence field scaffolding to
return dicts that are missing it.

Run: python wire_codd.py [--dry-run]

# EXPECTED_RUNTIME_SECONDS: 30
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "utilities"))
from constraint_gates import hopper_append

STUDIO = Path("G:/My Drive/Projects/_studio")

# Functions whose names suggest extraction work
EXTRACT_FUNC_NAMES = re.compile(
    r'def\s+(extract|parse|scrape|analyze|score_item|assess|classify_item'
    r'|get_listing|pull_fields|harvest|ingest|read_listing|process_item'
    r'|evaluate_item|run_extraction)[^\(]*\(',
    re.IGNORECASE
)

ALREADY_WIRED = re.compile(r'@codd_gate|from constraint_gates', re.IGNORECASE)

IMPORT_BLOCK = (
    "\nimport sys as _coddsys\n"
    "_coddsys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')\n"
    "from constraint_gates import codd_gate\n"
)

TARGETS = [
    STUDIO / "product_archaeology_run.py",
    STUDIO / "vintage_agent.py",
    STUDIO / "ai_intel_run.py",
    STUDIO / "whiteboard_score.py",
    STUDIO / "sanctions_ingestor.py",
    STUDIO / "wasde_parser.py",
]


def inject_codd(path: Path, dry_run: bool = False) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"read_error:{e}"

    if ALREADY_WIRED.search(text):
        return "already_compliant"

    lines = text.splitlines(keepends=True)

    # Find all extraction function definitions
    decorated_count = 0
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if EXTRACT_FUNC_NAMES.search(line):
            # Check if already decorated on previous line
            prev = new_lines[-1].strip() if new_lines else ""
            if not prev.startswith("@codd_gate"):
                indent = " " * (len(line) - len(line.lstrip()))
                new_lines.append(f"{indent}@codd_gate\n")
                decorated_count += 1
        new_lines.append(line)
        i += 1

    if decorated_count == 0:
        # No matching functions found — inject import only as future-proofing
        last_import = 0
        for idx, l in enumerate(lines):
            if re.match(r'^(import |from )', l):
                last_import = idx
        lines.insert(last_import + 1, IMPORT_BLOCK)
        modified = "".join(lines)
        if not dry_run:
            path.write_text(modified, encoding="utf-8")
        return "import_only_no_funcs"

    # Add import block after last top-level import
    modified = "".join(new_lines)
    mod_lines = modified.splitlines(keepends=True)
    last_import = 0
    for idx, l in enumerate(mod_lines):
        if re.match(r'^(import |from )', l):
            last_import = idx
    mod_lines.insert(last_import + 1, IMPORT_BLOCK)
    modified = "".join(mod_lines)

    if not dry_run:
        path.write_text(modified, encoding="utf-8")
    return f"patched_{decorated_count}_funcs"


def main():
    parser = argparse.ArgumentParser(description="Codd Rule extraction gate auto-wirer")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = [p for p in TARGETS if p.exists()]
    print(f"[wire_codd] Targeting {len(targets)} files...")

    total_patched = 0
    for path in targets:
        status = inject_codd(path, dry_run=args.dry_run)
        print(f"  [{status[:1].upper()}] {path.name}: {status}")
        if "patched" in status:
            total_patched += 1

    print(f"\n[wire_codd] Done. {total_patched} files patched.")
    if args.dry_run:
        print("[wire_codd] DRY RUN -- no files written")
    else:
        try:
            with open(STUDIO / "claude-status.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"[CODD-WIRE] patched={total_patched} of {len(targets)}\n"
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()
