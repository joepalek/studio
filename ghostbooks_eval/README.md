# Ghostbooks Evaluation System

## Overview
This system scans archive.org for books across 8 theory domains, evaluates them using expert AI characters, and identifies high-value opportunities for ghostwriting.

**Output**: Ranked list of theory books with depth-scored evaluations, flagged for potential synthesis/improvement into new Ghost Book publication.

---

## Folder Structure
```
ghostbooks_eval/
├── config/
│   ├── theory_domains.json         # 8 domains + keyword heuristics
│   ├── scoring_rubric.json         # Evaluation dimensions + weights
│   └── character_prompts.json      # Expert AI character system prompts
├── data/
│   ├── books_raw.jsonl             # Raw books fetched from archive.org
│   ├── books_scored.jsonl          # Evaluated books with scores + feedback
│   ├── domain_summary.json         # Rollup: domain avg scores
│   └── high_signal_leads.jsonl     # Books scoring > 6.5, grade A/B
├── scripts/
│   ├── 1_archive_scan.py           # Fetch books from archive.org
│   ├── 2_vectorize_characters.py   # Embed expert prompts into ChromaDB
│   ├── 3_evaluate_parallel.py      # Run scoring (expert + mirofish)
│   ├── 4_aggregate_scores.py       # Rollup by domain, identify tunnels
│   └── 5_export_ghostwriting_leads.py # Filter for Ghost Book vault
├── chroma_db/                       # Vector store (expert knowledge)
├── logs/                            # Execution logs
├── output/                          # Final exports
└── README.md                        # This file
```

---

## Execution Flow

### Prerequisites
```bash
pip install requests chromadb sentence-transformers
```

### Phase 1: Rapid Triage (2–3 days)

**Day 1 Evening**: Kick off archive.org scan
```bash
python scripts/1_archive_scan.py
```
- Fetches ~50 books per theory domain (8 domains = ~400 books)
- Respects rate limits (1 req/sec)
- Output: `data/books_raw.jsonl`
- Runs ~6–8 hours (can schedule overnight)

**Day 2 Morning**: Vectorize expert characters
```bash
python scripts/2_vectorize_characters.py
```
- Embeds 6 expert character prompts into ChromaDB
- Creates vector store for mirofish RAG priming
- Output: `chroma_db/` (persistent)
- Runs ~2 minutes

**Day 2 Afternoon**: Run parallel evaluation
```bash
python scripts/3_evaluate_parallel.py
```
- Scores each book using expert characters + mirofish
- Each book evaluated by domain-specific experts
- Outputs: individual scores (T, D, G, A, M, S), composite, feedback
- Output: `data/books_scored.jsonl`
- Runs ~2–4 hours (parallelizable)

**Day 3 Morning**: Aggregate results
```bash
python scripts/4_aggregate_scores.py
```
- Rolls up scores by theory domain
- Identifies HIGH/MEDIUM/LOW signal domains
- Filters high-signal books (composite > 6.5, grade A/B)
- Outputs: `data/domain_summary.json`, `data/high_signal_leads.jsonl`
- Runs ~1 minute

**Day 3 Afternoon**: Export to Ghost Book vault
```bash
python scripts/5_export_ghostwriting_leads.py
```
- Filters Grade A/B books
- Adds to `G:\My Drive\Projects\_studio\ghost_book\salvage-log.json`
- Output: `output/ghostwriting_candidates.jsonl`
- Runs ~1 minute

---

## Scoring Rubric

Each book scored 1–10 on:

| Score | Dimension | Evaluators |
|-------|-----------|-----------|
| **T-Score** | Theoretical Soundness | Domain theorist (e.g., Dr. Kauffman) |
| **D-Score** | Temporal Drift | Historian + contemporary expert |
| **G-Score** | Data Groundability | Methodologist + data scientist |
| **A-Score** | Advancement Potential | Systems integrator + cross-disciplinarian |
| **M-Score** | Market Value | Analyst (who needs this NOW?) |
| **S-Score** | Content Saturation | Scout (is it unique or retreading?) |

**Composite** = Weighted average of above

**Salvage Grade**:
- **A**: Composite > 7.5, high groundability, unique advancement vector
- **B**: Composite 6.5–7.5, solid but may need narrower focus
- **C**: Composite < 6.5 or outdated/saturated

---

## Expert Characters

Each theory domain has dedicated AI experts:

- **Systems & Complexity**: Dr. Kauffman, Dr. Wolfram, Dr. Simon
- **Information & Computation**: Dr. Shannon, Dr. Chaitin, Dr. Hofstadter
- **Economics & Game Theory**: Dr. von Neumann, Dr. Nash, Dr. Thaler
- (And more...)

Each character has a system prompt embedding their framework, era, and critical approach. They evaluate independently and flag disagreements.

---

## Phase 2: Deep Dive (Conditional)

If Phase 1 identifies HIGH-signal domains (avg > 6.5):
- Expand archive.org crawl to 200+ books/domain
- Add sub-specialists (character roster grows)
- Analyze synthesis opportunities (Book A + Book B + new data = new work)

---

## Phase 3: Ghostwriting Candidates

Books scoring Grade A or B feed into:
1. CTW stress testing (character profiles, edge cases)
2. Outline generation (skeleton for new synthesis)
3. Market positioning (who would buy this?)
4. Writing assignment queue

---

## Configuration

### `theory_domains.json`
Adjust keywords, experts, or priority:
```json
{
  "systems_complexity": {
    "keywords": ["complex adaptive systems", ...],
    "experts": ["Dr. Kauffman", "Dr. Wolfram", "Dr. Simon"],
    "priority": 1
  }
}
```

### `scoring_rubric.json`
Adjust dimension weights (higher = more important):
```json
{
  "a_score": {
    "label": "Advancement Potential",
    "weight": 1.1
  }
}
```

### `character_prompts.json`
Edit system prompts to refine evaluation criteria.

---

## Monitoring & Logs

All scripts write timestamped logs to `logs/`:
- `archive_scan.log` – Fetch progress
- `vectorize.log` – ChromaDB embedding
- `evaluate.log` – Scoring results
- `aggregate.log` – Domain rollup
- `export.log` – Vault integration

Check logs for errors or warnings.

---

## Windows Task Scheduler Integration

To automate nightly scans:

1. Open Task Scheduler
2. Create Basic Task: "Ghostbooks Auto-Scan"
3. Trigger: Daily at 10 PM
4. Action: `python G:\My Drive\Projects\_studio\ghostbooks_eval\scripts\1_archive_scan.py`
5. Add Additional Action (next trigger): 6 AM → `2_vectorize_characters.py`, etc.

---

## Troubleshooting

**Archive.org rate limit errors**: Increase sleep time in `1_archive_scan.py` (line ~XX)

**ChromaDB not found**: `pip install chromadb`

**Evaluation times out**: Reduce books_per_domain in scripts/1_archive_scan.py

**No Ghost Book vault found**: Create `G:\My Drive\Projects\_studio\ghost_book\salvage-log.json` manually

---

## Next Steps

After Phase 1 completes:
1. Review `data/domain_summary.json` – which domains are high-signal?
2. Inspect `data/high_signal_leads.jsonl` – what books made the cut?
3. Pick 2–3 Grade A books → begin outline synthesis
4. Loop: Phase 2 expand + Phase 3 writing queue

---

**Created**: 2026-03-30T22:54:42.557932
