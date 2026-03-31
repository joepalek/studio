#!/usr/bin/env python3
"""
Script 4: Aggregate Scores
Rolls up scored books by theory domain.
Identifies high-signal tunnels and low-signal domains.
Outputs domain_summary.json and high_signal_leads.jsonl
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(r"G:\My Drive\Projects\_studio\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
LOG_FILE = BASE_DIR / "logs" / "aggregate.log"

INPUT_FILE = DATA_DIR / "books_scored.jsonl"
SUMMARY_FILE = DATA_DIR / "domain_summary.json"
LEADS_FILE = DATA_DIR / "high_signal_leads.jsonl"


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def aggregate():
    """Load scored books, rollup by domain, identify tunnels."""
    log_msg(f"Loading scored books from {INPUT_FILE}...")

    # Collect scores by domain
    domain_stats = defaultdict(
        lambda: {"books": [], "total_composite": 0, "count": 0}
    )

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            book = json.loads(line)
            domain = book.get("theory_domain", "unknown")
            composite = book.get("scores", {}).get("composite", 0)

            domain_stats[domain]["books"].append(book)
            domain_stats[domain]["total_composite"] += composite
            domain_stats[domain]["count"] += 1

    # Calculate averages
    summary = {}
    for domain, stats in domain_stats.items():
        avg_composite = (
            stats["total_composite"] / stats["count"] if stats["count"] > 0 else 0
        )
        summary[domain] = {
            "book_count": stats["count"],
            "avg_composite_score": round(avg_composite, 2),
            "signal_strength": "HIGH" if avg_composite > 6.5 else "MEDIUM" if avg_composite > 5.5 else "LOW",
        }

    # Write summary
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log_msg(f"Domain summary written to {SUMMARY_FILE}")

    # Extract high-signal books (composite > 7.0, salvage grade A/B)
    high_signal = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            book = json.loads(line)
            composite = book.get("scores", {}).get("composite", 0)
            grade = book.get("salvage_grade", "C")
            if composite > 6.5 and grade in ["A", "B"]:
                high_signal.append(book)

    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        for book in high_signal:
            f.write(json.dumps(book) + "\n")

    log_msg(f"Wrote {len(high_signal)} high-signal leads to {LEADS_FILE}")
    log_msg("\nDomain Summary:")
    for domain, stats in sorted(summary.items()):
        log_msg(
            f"  {domain}: {stats['book_count']} books, avg {stats['avg_composite_score']}, {stats['signal_strength']}"
        )


if __name__ == "__main__":
    aggregate()
