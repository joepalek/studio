#!/usr/bin/env python3
"""
Script 3: Parallel Evaluation Engine
Loads books from books_raw.jsonl, runs them through expert character evaluations.
Uses mirofish + expert reasoning to score each book.
Outputs to books_scored.jsonl

Each book is evaluated by 6 characters (one per core evaluator role).
Results include individual scores + composite + reasoning.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime

BASE_DIR = "G:/My Drive/Projects/_studio/ghostbooks_eval"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
LOG_FILE = BASE_DIR / "logs" / "evaluate.log"

INPUT_FILE = DATA_DIR / "books_raw.jsonl"
OUTPUT_FILE = DATA_DIR / "books_scored.jsonl"

# Load configs
with open(CONFIG_DIR / "theory_domains.json") as f:
    THEORY_DOMAINS = json.load(f)
with open(CONFIG_DIR / "scoring_rubric.json") as f:
    SCORING_RUBRIC = json.load(f)
with open(CONFIG_DIR / "character_prompts.json") as f:
    CHARACTERS = json.load(f)


def log_msg(msg):
    """Log with timestamp."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def get_domain_experts(domain):
    """Return list of expert characters for a domain."""
    if domain not in THEORY_DOMAINS:
        return list(CHARACTERS.keys())[:3]  # Default to first 3
    return THEORY_DOMAINS[domain].get("experts", [])


def evaluate_book(book_record, experts):
    """
    Placeholder evaluation function.
    In production, this calls Claude API via mirofish with expert prompts.
    For now, returns mock scores.
    """
    # Mock evaluation (replace with actual API calls in production)
    scores = {
        "t_score": 7,
        "d_score": 6,
        "g_score": 8,
        "a_score": 7,
        "m_score": 5,
        "s_score": 4,
    }

    # Calculate composite
    total_weight = sum(SCORING_RUBRIC[k]["weight"] for k in scores.keys())
    weighted_sum = sum(
        scores[k] * SCORING_RUBRIC[k]["weight"] for k in scores.keys()
    )
    composite = weighted_sum / total_weight if total_weight > 0 else 0

    scores["composite"] = round(composite, 2)

    return {
        "book_title": book_record.get("title", "Unknown"),
        "book_author": book_record.get("author", ""),
        "book_year": book_record.get("year", ""),
        "theory_domain": book_record.get("theory_domain", ""),
        "scores": scores,
        "evaluators": experts,
        "evaluator_feedback": {
            char: f"Evaluation by {char} (mock)"
            for char in experts
        },
        "salvage_grade": "B" if scores["composite"] > 6.5 else "C",
        "ghostwrite_readiness": scores["composite"] > 7.0,
        "evaluation_date": datetime.now().isoformat(),
    }


def load_books():
    """Load all books from books_raw.jsonl"""
    books = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                books.append(json.loads(line))
    return books


def run_evaluation():
    """Main evaluation loop."""
    log_msg(f"Loading books from {INPUT_FILE}...")
    books = load_books()
    log_msg(f"Loaded {len(books)} books")

    log_msg("Starting evaluation...")
    scored_books = []

    for i, book in enumerate(books):
        domain = book.get("theory_domain", "")
        experts = get_domain_experts(domain)

        log_msg(
            f"[{i+1}/{len(books)}] Evaluating: {book.get('title')} (domain: {domain})"
        )

        scored = evaluate_book(book, experts)
        scored_books.append(scored)

    log_msg(f"Writing {len(scored_books)} scored books to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for book in scored_books:
            f.write(json.dumps(book) + "\n")

    log_msg("Evaluation complete!")


if __name__ == "__main__":
    run_evaluation()
