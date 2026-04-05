"""
autodream.py — Nightly Memory Consolidation (Item #2)
Studio Rule: Shannon Rule compliant (outputs under 200 tokens per chunk)
Schedule: Windows Task Scheduler — 2:00 AM daily
Path: G:\My Drive\Projects\_studio\scripts\autodream.py

Reads yesterday's supervisor logs + inbox answers.
Calls Claude Haiku to distill key facts/decisions.
Upserts synthesized chunks into ChromaDB studio collection.
"""

import os
import json
import glob
import datetime
import chromadb
import anthropic

# ── Config ──────────────────────────────────────────────────────────────────
STUDIO_ROOT     = r"G:\My Drive\Projects\_studio"
LOG_DIR         = os.path.join(STUDIO_ROOT, "logs")
INBOX_LOG       = os.path.join(STUDIO_ROOT, "inbox", "answered_log.jsonl")
CHROMA_PATH     = os.path.join(STUDIO_ROOT, "chromadb")
CHROMA_COL      = "studio"                  # existing collection
DREAM_LOG       = os.path.join(STUDIO_ROOT, "logs", "autodream.log")
MAX_CHUNK_TOKENS = 180                       # Shannon Rule: stay under 200

client_ai   = anthropic.Anthropic()          # uses ANTHROPIC_API_KEY env var
client_db   = chromadb.PersistentClient(path=CHROMA_PATH)
collection  = client_db.get_or_create_collection(CHROMA_COL)

# ── Helpers ──────────────────────────────────────────────────────────────────
def yesterday_str():
    return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

def load_supervisor_logs(date_str: str) -> str:
    """Grab all supervisor log lines from yesterday."""
    pattern = os.path.join(LOG_DIR, f"*{date_str}*.log")
    lines = []
    for f in glob.glob(pattern):
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            lines.extend(fh.readlines())
    return "".join(lines[-300:])  # cap at 300 lines to control token cost

def load_inbox_answers(date_str: str) -> str:
    """Pull answered inbox decisions from yesterday."""
    if not os.path.exists(INBOX_LOG):
        return ""
    entries = []
    with open(INBOX_LOG, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
                if rec.get("date", "").startswith(date_str):
                    entries.append(f"[{rec.get('id','?')}] Q: {rec.get('question','')} A: {rec.get('answer','')}")
            except Exception:
                continue
    return "\n".join(entries)

def distill(raw_text: str, source_label: str) -> list[str]:
    """
    Call Haiku to extract discrete facts/decisions as a JSON list of strings.
    Each string must be under MAX_CHUNK_TOKENS tokens (enforced by prompt).
    """
    if not raw_text.strip():
        return []

    prompt = f"""You are a memory consolidation agent for an autonomous AI studio.
Extract ONLY concrete facts, decisions, or status changes from the text below.
Output a JSON array of strings. Each string must be one self-contained fact,
under 40 words, starting with the subject (e.g. "eBay agent:", "Game Arch:").
Discard noise, errors, retries, and repetition. Return ONLY the JSON array.

SOURCE: {source_label}
DATE: {yesterday_str()}

TEXT:
{raw_text[:6000]}
"""
    resp = client_ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = resp.content[0].text.strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        facts = json.loads(raw)
        return [f for f in facts if isinstance(f, str) and len(f) > 10]
    except Exception:
        return []

def upsert_to_chromadb(facts: list[str], source: str):
    """Upsert distilled facts into ChromaDB with date + source metadata."""
    if not facts:
        return 0
    date_str = yesterday_str()
    ids, docs, metas = [], [], []
    for i, fact in enumerate(facts):
        chunk_id = f"dream_{date_str}_{source}_{i:03d}"
        ids.append(chunk_id)
        docs.append(fact)
        metas.append({"source": source, "date": date_str, "type": "autodream"})
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(facts)

def log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(DREAM_LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

# ── Health Score Helper (Item #6) ─────────────────────────────────────────────
def compute_project_health() -> dict:
    """
    Scan studio project directories for simple health signals.
    Returns a dict of project -> score (0-100).
    """
    health = {}
    projects_dir = os.path.join(STUDIO_ROOT, "projects")
    if not os.path.isdir(projects_dir):
        return health
    for proj in os.listdir(projects_dir):
        proj_path = os.path.join(projects_dir, proj)
        if not os.path.isdir(proj_path):
            continue
        todos = 0
        py_files = 0
        for root, _, files in os.walk(proj_path):
            for f in files:
                if f.endswith(".py"):
                    py_files += 1
                    try:
                        content = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
                        todos += content.upper().count("TODO") + content.upper().count("FIXME")
                    except Exception:
                        pass
        # Simple score: start at 100, -5 per TODO, floor 0
        score = max(0, 100 - (todos * 5))
        health[proj] = {"score": score, "todos": todos, "py_files": py_files}
    return health

def write_health_report(health: dict):
    """Write health scores to a markdown file for Supervisor weekly digest."""
    report_path = os.path.join(STUDIO_ROOT, "logs", f"health_{yesterday_str()}.md")
    lines = [f"# Studio Health Report — {yesterday_str()}\n"]
    lines.append("| Project | Score | TODOs | Files |\n|---|---|---|---|")
    for proj, data in sorted(health.items(), key=lambda x: x[1]["score"]):
        emoji = "🟢" if data["score"] >= 80 else ("🟡" if data["score"] >= 50 else "🔴")
        lines.append(f"| {proj} | {emoji} {data['score']} | {data['todos']} | {data['py_files']} |")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    log(f"Health report written: {report_path}")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    date_str = yesterday_str()
    log(f"=== AutoDream starting for {date_str} ===")
    total_upserted = 0

    # 1. Supervisor logs
    sup_raw = load_supervisor_logs(date_str)
    sup_facts = distill(sup_raw, "supervisor_logs")
    n = upsert_to_chromadb(sup_facts, "supervisor_logs")
    log(f"Supervisor logs → {n} facts upserted")
    total_upserted += n

    # 2. Inbox answers
    inbox_raw = load_inbox_answers(date_str)
    inbox_facts = distill(inbox_raw, "inbox_answers")
    n = upsert_to_chromadb(inbox_facts, "inbox_answers")
    log(f"Inbox answers → {n} facts upserted")
    total_upserted += n

    # 3. Health scores (Item #6)
    health = compute_project_health()
    write_health_report(health)

    log(f"=== AutoDream complete. Total chunks upserted: {total_upserted} ===")

if __name__ == "__main__":
    main()
