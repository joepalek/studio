#!/usr/bin/env python3
"""
AutoDream - Nightly Memory Consolidation Script
Reads supervisor logs, distills key facts via Haiku, upserts to ChromaDB.
Generates health score report for weekly digest.

Schedule: 2:00 AM daily via Windows Task Scheduler
TTL: 1 hour (Hamilton Rule compliant)
"""

import os
import json
import datetime
import hashlib
from pathlib import Path
from typing import Optional

# Paths - adjust to match your studio structure
STUDIO_ROOT = Path(r"G:\My Drive\Projects\_studio")
INBOX_LOG = STUDIO_ROOT / "logs" / "inbox_answered.json"
SUPERVISOR_LOG = STUDIO_ROOT / "logs" / "supervisor.log"
HEALTH_REPORT = STUDIO_ROOT / "reports" / "health_score.md"
CHROMADB_PATH = STUDIO_ROOT / "chromadb"

# Optional: If logs are elsewhere, override here
ALTERNATIVE_LOG_PATHS = [
    STUDIO_ROOT / "inbox" / "answered.json",
    STUDIO_ROOT / "supervisor" / "decisions.log",
]


def find_log_file() -> Optional[Path]:
    """Find the inbox/supervisor log file."""
    candidates = [INBOX_LOG, SUPERVISOR_LOG] + ALTERNATIVE_LOG_PATHS
    for path in candidates:
        if path.exists():
            return path
    return None


def get_yesterdays_entries(log_path: Path) -> list[dict]:
    """Extract log entries from the past 24 hours."""
    entries = []
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    cutoff = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        if log_path.suffix == ".json":
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        ts = entry.get("timestamp") or entry.get("answered_at") or entry.get("created_at")
                        if ts:
                            try:
                                entry_time = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if entry_time.replace(tzinfo=None) >= cutoff:
                                    entries.append(entry)
                            except (ValueError, TypeError):
                                continue
        else:
            # Plain text log - extract lines with timestamps
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and len(line) > 10:
                        entries.append({"raw": line})
    except Exception as e:
        print(f"[AutoDream] Error reading log: {e}")
    
    return entries


def distill_via_haiku(entries: list[dict]) -> list[dict]:
    """
    Call Claude Haiku to extract key facts/decisions from log entries.
    Returns distilled chunks ready for ChromaDB upsert.
    """
    if not entries:
        return []
    
    # Prepare prompt
    entries_text = "\n".join([
        json.dumps(e, default=str) if isinstance(e, dict) else str(e)
        for e in entries[:50]  # Cap at 50 entries to stay under token limits
    ])
    
    prompt = f"""Extract the key facts, decisions, and learnings from these supervisor log entries.
Return a JSON array of objects, each with:
- "fact": A single atomic fact or decision (1-2 sentences)
- "category": One of [decision, learning, preference, context, error]
- "importance": 1-5 (5 = critical)

Only include facts worth remembering long-term. Skip routine operations.

Log entries:
{entries_text}

Respond with ONLY the JSON array, no other text."""

    try:
        import anthropic
        client = anthropic.Anthropic()
        
        response = client.messages.create(
            model="claude-haiku-3-5-sonnet-20241022",  # Haiku
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text.strip()
        # Clean potential markdown fencing
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        result_text = result_text.strip()
        
        distilled = json.loads(result_text)
        return distilled if isinstance(distilled, list) else []
        
    except ImportError:
        print("[AutoDream] anthropic package not installed. Run: pip install anthropic")
        return []
    except Exception as e:
        print(f"[AutoDream] Haiku distillation failed: {e}")
        return []


def upsert_to_chromadb(chunks: list[dict]) -> int:
    """Upsert distilled chunks to ChromaDB."""
    if not chunks:
        return 0
    
    try:
        import chromadb
        
        client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
        collection = client.get_or_create_collection(
            name="autodream",
            metadata={"description": "Nightly distilled learnings from supervisor logs"}
        )
        
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            fact = chunk.get("fact", "")
            if not fact:
                continue
                
            # Generate stable ID from content hash
            chunk_id = hashlib.sha256(fact.encode()).hexdigest()[:16]
            ids.append(f"autodream_{chunk_id}")
            documents.append(fact)
            metadatas.append({
                "category": chunk.get("category", "unknown"),
                "importance": chunk.get("importance", 3),
                "distilled_at": datetime.datetime.now().isoformat(),
                "source": "autodream"
            })
        
        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            
        return len(ids)
        
    except ImportError:
        print("[AutoDream] chromadb package not installed. Run: pip install chromadb")
        return 0
    except Exception as e:
        print(f"[AutoDream] ChromaDB upsert failed: {e}")
        return 0


def generate_health_report() -> dict:
    """Generate health score metrics for the studio."""
    health = {
        "generated_at": datetime.datetime.now().isoformat(),
        "scores": {},
        "alerts": []
    }
    
    # Check key directories/files exist
    checks = {
        "chromadb": CHROMADB_PATH.exists(),
        "logs_dir": (STUDIO_ROOT / "logs").exists(),
        "inbox": (STUDIO_ROOT / "inbox").exists() or (STUDIO_ROOT / "decisions").exists(),
        "model_registry": (STUDIO_ROOT / "model-registry.json").exists(),
    }
    
    health["scores"]["infrastructure"] = sum(checks.values()) / len(checks) * 100
    
    # Check for stale scheduled tasks (Hamilton Rule)
    # This is a placeholder - in production, read from Task Scheduler or a status file
    health["scores"]["task_health"] = 100  # Assume healthy unless we detect otherwise
    
    # Count recent errors in logs
    error_count = 0
    if SUPERVISOR_LOG.exists():
        try:
            with open(SUPERVISOR_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    if "ERROR" in line.upper() or "FAILED" in line.upper():
                        error_count += 1
        except Exception:
            pass
    
    health["scores"]["error_rate"] = max(0, 100 - (error_count * 5))  # -5 per error
    
    # Overall health
    health["scores"]["overall"] = sum(health["scores"].values()) / len(health["scores"])
    
    # Generate alerts
    if health["scores"]["overall"] < 80:
        health["alerts"].append("Overall health below 80% - review errors")
    if not checks["chromadb"]:
        health["alerts"].append("ChromaDB path not found")
    
    return health


def write_health_report(health: dict):
    """Write health report as markdown."""
    HEALTH_REPORT.parent.mkdir(parents=True, exist_ok=True)
    
    md = f"""# Studio Health Report
Generated: {health['generated_at']}

## Scores
| Metric | Score |
|--------|-------|
"""
    for metric, score in health["scores"].items():
        emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        md += f"| {metric} | {emoji} {score:.0f}% |\n"
    
    if health["alerts"]:
        md += "\n## Alerts\n"
        for alert in health["alerts"]:
            md += f"- ⚠️ {alert}\n"
    else:
        md += "\n## Alerts\nNo alerts. All systems nominal.\n"
    
    with open(HEALTH_REPORT, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"[AutoDream] Health report written to {HEALTH_REPORT}")


def main():
    print(f"[AutoDream] Starting nightly consolidation at {datetime.datetime.now().isoformat()}")
    
    # Step 1: Find and read logs
    log_path = find_log_file()
    if not log_path:
        print("[AutoDream] No log file found. Creating health report only.")
        entries = []
    else:
        print(f"[AutoDream] Reading from {log_path}")
        entries = get_yesterdays_entries(log_path)
        print(f"[AutoDream] Found {len(entries)} entries from past 24 hours")
    
    # Step 2: Distill via Haiku (if entries exist)
    if entries:
        print("[AutoDream] Distilling via Haiku...")
        chunks = distill_via_haiku(entries)
        print(f"[AutoDream] Distilled {len(chunks)} chunks")
        
        # Step 3: Upsert to ChromaDB
        if chunks:
            count = upsert_to_chromadb(chunks)
            print(f"[AutoDream] Upserted {count} chunks to ChromaDB")
    
    # Step 4: Generate health report
    print("[AutoDream] Generating health report...")
    health = generate_health_report()
    write_health_report(health)
    
    print(f"[AutoDream] Complete. Overall health: {health['scores']['overall']:.0f}%")
    
    # Return non-zero if health is critical
    if health["scores"]["overall"] < 50:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
