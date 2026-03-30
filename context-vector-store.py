"""
context-vector-store.py — Config G Vector Memory (ChromaDB)
Indexes studio context files into a local ChromaDB collection.
Query function returns top-N relevant chunks under 200 tokens.

Usage:
  python context-vector-store.py              # index if needed
  python context-vector-store.py --reindex    # force full reindex
  python context-vector-store.py --query "what are the active projects"

Nightly reindex: Studio\VectorReindex at 01:15 AM
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

STUDIO        = "G:/My Drive/Projects/_studio"
VECTOR_DIR    = os.path.join(STUDIO, "vector-memory")
CONFIG_PATH   = os.path.join(STUDIO, "studio-config.json")
LOG_PATH      = os.path.join(STUDIO, "scheduler/logs/vector-reindex.log")
HB_PATH       = os.path.join(STUDIO, "heartbeat-log.json")
STATUS_PATH   = os.path.join(STUDIO, "claude-status.txt")
COLLECTION    = "studio_context"

# Files to index — ordered by priority
INDEX_SOURCES = [
    ("CLAUDE.md",           "G:/My Drive/Projects/CLAUDE.md"),
    ("session-handoff.md",  os.path.join(STUDIO, "session-handoff.md")),
    ("decision-log.json",   os.path.join(STUDIO, "decision-log.json")),
    ("whiteboard.json",     os.path.join(STUDIO, "whiteboard.json")),
    ("studio-context.md",   os.path.join(STUDIO, "studio-context.md")),
]

# Also index all state.json files found in project folders
PROJECTS_ROOT = "G:/My Drive/Projects"


def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_heartbeat(status, notes):
    try:
        try:
            with open(HB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"_schema": "1.0", "entries": []}
        if not isinstance(data, dict) or "entries" not in data:
            data = {"_schema": "1.0", "entries": []}
        data["entries"].append({
            "date": datetime.now().isoformat(),
            "agent": "context-vector-store",
            "status": status,
            "notes": notes
        })
        tmp = HB_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, HB_PATH)
    except Exception:
        pass


def write_status(msg):
    try:
        ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(STATUS_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ts} [VECTOR-STORE] {msg}\n")
    except Exception:
        pass


def chunk_text(text, source_name, chunk_size=400):
    """Split text into chunks of ~chunk_size chars. Returns list of (chunk, metadata)."""
    chunks = []
    lines = text.splitlines()
    current = []
    current_len = 0

    for line in lines:
        current.append(line)
        current_len += len(line) + 1
        if current_len >= chunk_size:
            chunk = "\n".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []
            current_len = 0

    # Remaining
    if current:
        chunk = "\n".join(current).strip()
        if chunk:
            chunks.append(chunk)

    return chunks


def collect_documents():
    """Collect all documents to index. Returns list of (doc_id, text, metadata)."""
    docs = []

    # Core files
    for label, path in INDEX_SOURCES:
        if not os.path.exists(path):
            log(f"  SKIP (not found): {label}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            mtime = os.path.getmtime(path)
            chunks = chunk_text(text, label)
            for i, chunk in enumerate(chunks):
                doc_id = f"{label}_chunk{i}"
                docs.append((doc_id, chunk, {"source": label, "chunk": i, "mtime": mtime}))
            log(f"  Indexed: {label} ({len(chunks)} chunks)")
        except Exception as e:
            log(f"  ERROR reading {label}: {e}")

    # State files from project directories
    projects = [d for d in os.listdir(PROJECTS_ROOT)
                if os.path.isdir(os.path.join(PROJECTS_ROOT, d))
                and not d.startswith(".")]
    for project in projects:
        for fname in ["state.json", f"{project}-state.json"]:
            path = os.path.join(PROJECTS_ROOT, project, fname)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                    mtime = os.path.getmtime(path)
                    chunks = chunk_text(text, f"{project}/{fname}")
                    for i, chunk in enumerate(chunks):
                        doc_id = f"state_{project}_chunk{i}"
                        docs.append((doc_id, chunk, {
                            "source": f"{project}/{fname}",
                            "chunk": i,
                            "mtime": mtime,
                            "project": project
                        }))
                    log(f"  Indexed: {project}/state.json ({len(chunks)} chunks)")
                except Exception as e:
                    log(f"  ERROR reading {project}/state.json: {e}")
                break

    return docs


def get_chroma_client():
    """Return ChromaDB persistent client. Raises on failure."""
    import chromadb
    return chromadb.PersistentClient(path=VECTOR_DIR)


def build_index(force=False):
    """Build or rebuild the ChromaDB index."""
    log("Vector store index starting")

    try:
        client = get_chroma_client()
    except Exception as e:
        log(f"ERROR: ChromaDB client failed: {e}")
        write_heartbeat("flagged", f"ChromaDB unavailable: {str(e)[:80]}")
        return False

    try:
        if force:
            try:
                client.delete_collection(COLLECTION)
                log("  Dropped existing collection for reindex")
            except Exception:
                pass

        collection = client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )

        existing_count = collection.count()
        if existing_count > 0 and not force:
            log(f"  Collection exists with {existing_count} docs — skipping (use --reindex to force)")
            return True

        docs = collect_documents()
        if not docs:
            log("  No documents to index")
            return False

        # Upsert in batches
        batch_size = 50
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            ids       = [d[0] for d in batch]
            documents = [d[1] for d in batch]
            metadatas = [d[2] for d in batch]
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        total = collection.count()
        msg = f"Index complete: {total} chunks from {len(docs)} documents"
        log(f"  {msg}")
        write_heartbeat("clean", msg)
        write_status(msg)
        return True

    except Exception as e:
        log(f"ERROR building index: {e}")
        write_heartbeat("flagged", f"Index build failed: {str(e)[:80]}")
        return False


def get_relevant_context(query, n=5):
    """
    Query vector store for top-N relevant chunks.
    Returns string under ~200 tokens (800 chars).
    Falls back to session-handoff.md if ChromaDB unavailable.
    """
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )

        if collection.count() == 0:
            raise ValueError("Collection empty — index not built yet")

        results = collection.query(
            query_texts=[query],
            n_results=min(n, collection.count())
        )

        chunks = results["documents"][0] if results["documents"] else []
        sources = [m.get("source", "?") for m in (results["metadatas"][0] if results["metadatas"] else [])]

        # Assemble under 800 chars (~200 tokens)
        output_lines = []
        char_budget = 800
        for chunk, source in zip(chunks, sources):
            entry = f"[{source}]\n{chunk}"
            if len("\n\n".join(output_lines + [entry])) > char_budget:
                break
            output_lines.append(entry)

        return "\n\n".join(output_lines) if output_lines else "[no relevant context found]"

    except Exception as e:
        # Fallback: read session-handoff.md
        fallback_path = os.path.join(STUDIO, "session-handoff.md")
        try:
            with open(fallback_path, "r", encoding="utf-8") as f:
                content = f.read()[:800]
            return f"[VECTOR_FALLBACK — ChromaDB error: {str(e)[:60]}]\n\n{content}"
        except Exception:
            return f"[VECTOR_FALLBACK — ChromaDB error: {str(e)[:60]}]\n[session-handoff.md also unavailable]"


def main():
    parser = argparse.ArgumentParser(description="Studio context vector store")
    parser.add_argument("--reindex", action="store_true", help="Force full reindex")
    parser.add_argument("--query",   type=str, default=None, help="Query the index")
    args = parser.parse_args()

    if args.query:
        result = get_relevant_context(args.query)
        print("\n=== QUERY RESULT ===")
        print(result)
        print(f"\n[{len(result)} chars / ~{len(result)//4} tokens]")
        return

    build_index(force=args.reindex)


if __name__ == "__main__":
    main()
