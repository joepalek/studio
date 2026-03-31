"""
session-startup.py — Config G Session Context Loader
Called at the start of every Claude Code session.

Queries ChromaDB vector store for relevant context.
Returns under 200 tokens. Logs which path was used.

Primary path:  ChromaDB vector query (Config G)
Fallback path: session-handoff.md only (Config B fallback)
               Used when ChromaDB or Ollama unavailable.

Usage:
  python session-startup.py
  python session-startup.py --verbose
"""

import argparse
import json
import os
import sys
from datetime import datetime

STUDIO      = "G:/My Drive/Projects/_studio"
HANDOFF     = os.path.join(STUDIO, "session-handoff.md")
STATUS_PATH = os.path.join(STUDIO, "claude-status.txt")
LOG_PATH    = os.path.join(STUDIO, "scheduler/logs/session-startup.log")

STARTUP_QUERY = (
    "current system state active projects last decisions "
    "next priorities recent completions open blockers"
)


def log(msg, verbose=False):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    if verbose:
        print(line, file=sys.stderr)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except PermissionError:
        fallback = LOG_PATH.replace(".log", "-fallback.log")
        with open(fallback, "a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")


def write_status(msg):
    try:
        ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(STATUS_PATH, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"{ts} [SESSION-STARTUP] {msg}\n")
    except Exception:
        pass


def config_b_fallback(reason):
    """
    Config B fallback: read CLAUDE.md + session-handoff.md locally.
    Hamilton's fault tolerance requirement — never start blind.
    """
    lines = [f"[OLLAMA_DOWN — running in fallback mode: {reason}]", ""]
    claude_md = "G:/My Drive/Projects/CLAUDE.md"

    # session-handoff.md
    if os.path.exists(HANDOFF):
        try:
            with open(HANDOFF, "r", encoding="utf-8") as f:
                handoff = f.read().strip()
            if handoff:
                lines.append("=== SESSION HANDOFF ===")
                lines.append(handoff[:600])
        except Exception:
            lines.append("[session-handoff.md: read error]")
    else:
        lines.append("[session-handoff.md: not found]")

    result = "\n".join(lines)
    log(f"FALLBACK used — reason: {reason}")
    write_status(f"FALLBACK mode — {reason}")
    return result


def run_vector_query(verbose=False):
    """
    Query ChromaDB vector store via context-vector-store.py get_relevant_context().
    Returns context string or raises on failure.
    """
    # Add _studio to path so we can import context-vector-store
    sys.path.insert(0, STUDIO)
    try:
        import context_vector_store  # noqa: context-vector-store.py → import as module
        context = context_vector_store.get_relevant_context(STARTUP_QUERY, n=5)
        return context
    except ImportError:
        # Try direct file import with underscore name
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "context_vector_store",
            os.path.join(STUDIO, "context-vector-store.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.get_relevant_context(STARTUP_QUERY, n=5)


def main():
    parser = argparse.ArgumentParser(description="Session context loader (Config G)")
    parser.add_argument("--verbose", action="store_true", help="Log to stderr")
    args = parser.parse_args()

    path_used = "vector"
    context   = None

    # Primary path — ChromaDB vector query
    try:
        context = run_vector_query(verbose=args.verbose)

        # Check if we got a fallback indicator from the vector store itself
        if context.startswith("[VECTOR_FALLBACK"):
            path_used = "vector_internal_fallback"
        else:
            path_used = "vector"

        log(f"OK — path={path_used} chars={len(context)}", verbose=args.verbose)
        write_status(f"context loaded via {path_used} ({len(context)} chars)")

    except Exception as e:
        # Hamilton's fallback: Config B — never start blind
        err = str(e)[:80]
        log(f"Vector store failed ({err}) — switching to Config B fallback", verbose=args.verbose)
        context = config_b_fallback(err)
        path_used = "config_b_fallback"

    # Output context to stdout — this is what Claude Code reads
    print(context)
    print(f"\n[session-startup: path={path_used}, {len(context)} chars / ~{len(context)//4} tokens]")


if __name__ == "__main__":
    main()
