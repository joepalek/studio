#!/usr/bin/env python3
"""
Script 5: Export Ghostwriting Leads
Filters high-signal, high-grade books and prepares them for the Ghost Book vault.
Adds evaluated books to salvage-log.json (existing vault) or creates new lead list.
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"G:\My Drive\Projects\_studio\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
GHOST_BOOK_VAULT = Path(r"G:\My Drive\Projects\_studio\ghost_book")
LOG_FILE = BASE_DIR / "logs" / "export.log"

INPUT_FILE = DATA_DIR / "high_signal_leads.jsonl"
EXPORT_FILE = OUTPUT_DIR / "ghostwriting_candidates.jsonl"
VAULT_LOG = GHOST_BOOK_VAULT / "salvage-log.json"


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def export_leads():
    """Export high-signal leads to ghostwriting candidates."""
    log_msg(f"Loading high-signal leads from {INPUT_FILE}...")

    candidates = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            book = json.loads(line)

            # Prepare for ghostwriting
            candidate = {
                "title": book.get("book_title", ""),
                "author": book.get("book_author", ""),
                "year": book.get("book_year", ""),
                "theory_domain": book.get("theory_domain", ""),
                "source": "archive_org_auto_eval",
                "evaluation_date": book.get("evaluation_date", ""),
                "composite_score": book.get("scores", {}).get("composite", 0),
                "salvage_grade": book.get("salvage_grade", "C"),
                "ghostwrite_assigned": False,
                "status": "lead",
                "evaluators": book.get("evaluators", []),
            }

            candidates.append(candidate)

    # Write export file
    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        for cand in candidates:
            f.write(json.dumps(cand) + "\n")

    log_msg(f"Exported {len(candidates)} ghostwriting candidates to {EXPORT_FILE}")

    # Try to add to existing vault salvage-log
    if VAULT_LOG.exists():
        log_msg(f"Found existing vault log at {VAULT_LOG}")
        with open(VAULT_LOG, "r", encoding="utf-8") as f:
            vault_data = json.load(f)
        if not isinstance(vault_data, dict):
            vault_data = {"entries": []}

        vault_data.setdefault("entries", []).extend(candidates)

        with open(VAULT_LOG, "w", encoding="utf-8") as f:
            json.dump(vault_data, f, indent=2)
        log_msg(f"Added {len(candidates)} entries to vault salvage-log")
    else:
        log_msg(
            f"Vault log not found at {VAULT_LOG}. Create it manually or check path."
        )

    log_msg("Export complete!")


if __name__ == "__main__":
    export_leads()
