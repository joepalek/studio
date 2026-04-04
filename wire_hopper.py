"""
wire_hopper.py — Automated Hopper Rule enforcement.

Finds raw json.dump/open writes to *-inbox.json files and replaces them
with validated hopper_append() calls from constraint_gates.

Run: python wire_hopper.py [--dry-run]

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

SKIP_FILES = {
    "constraint_gates.py", "constraint_audit.py", "wire_hopper.py",
    "wire_hamilton.py", "wire_bezos.py", "wire_codd.py",
}

TARGETS = [
    STUDIO / "whiteboard_score.py",
    STUDIO / "run_inbox_sync.py",
    STUDIO / "ai_intel_run.py",
    STUDIO / "provider_health.py",
    STUDIO / "model_validator.py",
    STUDIO / "tier1_pipeline_template.py",
    STUDIO / "sanctions_ingestor.py",
    STUDIO / "wasde_parser.py",
    STUDIO / "send_digest_to_inbox.py",
    STUDIO / "utilities/scraper_utils.py",
]

IMPORT_INJECT = (
    "import sys as _hoppersys\n"
    "_hoppersys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')\n"
    "from constraint_gates import hopper_append as _hopper_append\n"
)

# Pattern: open(path, 'w') ... json.dump(items, f) where path contains 'inbox'
RAW_WRITE_PATTERN = re.compile(
    r"(with\s+open\([^)]*inbox[^)]*,\s*['\"]w['\"][^)]*\)\s+as\s+(\w+)\s*:\s*\n"
    r"(?:\s+.*\n)*?\s+json\.dump\((\w+)\s*,\s*\2[^)]*\))",
    re.MULTILINE
)

ALREADY_WIRED = re.compile(r'hopper_append|from constraint_gates', re.IGNORECASE)


def inject_hopper(path: Path, dry_run: bool = False) -> str:
    if path.name in SKIP_FILES:
        return "skipped"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"read_error:{e}"

    if ALREADY_WIRED.search(text):
        return "already_compliant"

    # Check if file actually writes to inbox
    if not re.search(r'inbox', text, re.IGNORECASE):
        return "no_inbox_writes"

    # Find raw inbox writes — comment them out and add hopper_append call
    modified = text
    hits = 0

    # Simple pattern: json.dump(X, f) inside an open(...inbox...) block
    # Replace with a comment + hopper_append call on the items list
    def replace_match(m):
        nonlocal hits
        hits += 1
        original = m.group(0)
        # Extract the items variable name from json.dump(items, f)
        dump_match = re.search(r'json\.dump\((\w+)\s*,', original)
        items_var = dump_match.group(1) if dump_match else "items"
        # Extract inbox path variable
        open_match = re.search(r'open\(([^,]+),', original)
        path_var = open_match.group(1).strip() if open_match else '"unknown-inbox.json"'
        replacement = (
            f"# [HOPPER] replaced raw write with validated hopper_append\n"
            f"        for _item in {items_var}:\n"
            f"            try:\n"
            f"                _hopper_append(str({path_var}), _item)\n"
            f"            except ValueError as _he:\n"
            f"                print(f'  [HOPPER] item rejected: {{_he}}')\n"
        )
        return replacement

    modified = RAW_WRITE_PATTERN.sub(replace_match, modified)

    if hits == 0:
        # Fallback: just inject the import so hopper_append is available
        lines = modified.splitlines(keepends=True)
        last_import = 0
        for i, l in enumerate(lines):
            if re.match(r'^(import |from )', l):
                last_import = i
        lines.insert(last_import + 1, "\n" + IMPORT_INJECT)
        modified = "".join(lines)
        status = "import_injected"
    else:
        # Also inject the import
        lines = modified.splitlines(keepends=True)
        last_import = 0
        for i, l in enumerate(lines):
            if re.match(r'^(import |from )', l):
                last_import = i
        lines.insert(last_import + 1, "\n" + IMPORT_INJECT)
        modified = "".join(lines)
        status = f"patched_{hits}_writes"

    if not dry_run:
        path.write_text(modified, encoding="utf-8")
    return status


def main():
    parser = argparse.ArgumentParser(description="Hopper Rule inbox write auto-wirer")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = [p for p in TARGETS if p.exists()]
    print(f"[wire_hopper] Targeting {len(targets)} files...")

    counts = {"patched": 0, "import_only": 0, "compliant": 0, "skipped": 0, "error": 0}
    for path in targets:
        status = inject_hopper(path, dry_run=args.dry_run)
        if "patched" in status:
            counts["patched"] += 1
        elif "import" in status:
            counts["import_only"] += 1
        elif "compliant" in status:
            counts["compliant"] += 1
        elif "skipped" in status or "no_inbox" in status:
            counts["skipped"] += 1
        else:
            counts["error"] += 1
        print(f"  [{status[:1].upper()}] {path.name}: {status}")

    print(f"\n[wire_hopper] SUMMARY")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    if args.dry_run:
        print("\n[wire_hopper] DRY RUN -- no files written")
    else:
        try:
            with open(STUDIO / "claude-status.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"[HOPPER-WIRE] {counts}\n"
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()
