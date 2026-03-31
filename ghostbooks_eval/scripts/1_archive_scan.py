#!/usr/bin/env python3
"""
Script 1: Archive.org Scanner
Fetches seed books from archive.org based on theory domain keywords.
Saves metadata to data/books_raw.jsonl

Respects archive.org rate limits (~1 req/sec for anonymous, 30 req/min with account).
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"G:\My Drive\Projects\_studio\ghostbooks_eval")
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Load theory domains config
with open(BASE_DIR / "config" / "theory_domains.json") as f:
    THEORY_DOMAINS = json.load(f)

OUTPUT_FILE = DATA_DIR / "books_raw.jsonl"
LOG_FILE = LOG_DIR / "archive_scan.log"


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def search_archive_org(query, limit=10):
    """
    Search archive.org via their advanced search API.
    Returns list of book metadata dicts.
    """
    url = "https://archive.org/advancedsearch.php"
    params = {
        "q": query,
        "fl": [
            "identifier",
            "title",
            "creator",
            "date",
            "description",
            "language",
            "subject",
        ],
        "output": "json",
        "rows": limit,
        "sort": "date DESC",
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("response", {}).get("docs", [])
        return docs
    except Exception as e:
        log_msg(f"ERROR: Failed to search archive.org: {e}")
        return []


def fetch_book_metadata(identifier):
    """
    Fetch full metadata for a book by identifier.
    Returns dict or None.
    """
    url = f"https://archive.org/metadata/{identifier}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log_msg(f"WARNING: Could not fetch metadata for {identifier}: {e}")
        return None


def scan_domains(books_per_domain=100):
    """
    Scan each theory domain, collect books, write to JSONL.
    """
    log_msg(f"Starting archive.org scan. Target: {books_per_domain} books/domain.")

    all_books = []

    for domain, config in sorted(
        THEORY_DOMAINS.items(), key=lambda x: x[1]["priority"]
    ):
        log_msg(f"\n--- Domain: {domain} ---")
        keywords = config["keywords"]

        # Combine keywords into OR query
        query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # Limit to 5 keywords
        query += " AND mediatype:texts AND language:eng"
        query += " AND (subject:book OR subject:theory)"

        log_msg(f"Query: {query}")

        docs = search_archive_org(query, limit=books_per_domain)
        log_msg(f"Found {len(docs)} results for {domain}")

        for i, doc in enumerate(docs):
            identifier = doc.get("identifier", "")
            title = doc.get("title", "Unknown")

            log_msg(
                f"  [{i+1}/{len(docs)}] Fetching: {title} ({identifier})"
            )

            # Fetch full metadata
            full_meta = fetch_book_metadata(identifier)
            if not full_meta:
                continue

            # Extract key fields
            book_record = {
                "identifier": identifier,
                "title": full_meta.get("metadata", {}).get("title", title),
                "author": full_meta.get("metadata", {}).get("creator", []),
                "year": full_meta.get("metadata", {}).get("date", ""),
                "description": full_meta.get("metadata", {}).get("description", ""),
                "theory_domain": domain,
                "archive_url": f"https://archive.org/details/{identifier}",
                "scan_date": datetime.now().isoformat(),
            }

            all_books.append(book_record)

            # Rate limit: 1 second between requests
            time.sleep(1)

    # Write all books to JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for book in all_books:
            f.write(json.dumps(book) + "\n")

    log_msg(f"\nScan complete. Wrote {len(all_books)} books to {OUTPUT_FILE}")


if __name__ == "__main__":
    scan_domains(books_per_domain=50)  # Start with 50/domain for testing
