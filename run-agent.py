"""
run-agent.py — Studio Agent Dispatcher
Invoked by Windows Task Scheduler. Takes agent name as argument,
launches a Claude Code session with that agent's prompt,
logs start/end time to heartbeat-log.json automatically.

Usage:
  python run-agent.py <agent-name> [--mode <mode>]
  python run-agent.py supervisor
  python run-agent.py supervisor heartbeat-only
  python run-agent.py whiteboard-agent

Requires: claude CLI installed and authenticated
  Install: npm install -g @anthropic-ai/claude-code
"""

import sys
import os
import json
import subprocess
import traceback
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────
STUDIO_ROOT = "G:/My Drive/Projects/_studio"
HEARTBEAT_FILE = os.path.join(STUDIO_ROOT, "heartbeat-log.json")
AGENT_MD_DIR = STUDIO_ROOT

# Agents and their .md file names
AGENT_MAP = {
    "supervisor":             "supervisor.md",
    "whiteboard-agent":       "whiteboard-agent.md",
    "stress-tester":          "stress-tester.md",
    "janitor":                "janitor.md",
    "git-scout":              "git-scout.md",
    "git-commit-agent":       "git-commit-agent.md",
    "intel-feed":             "intel-feed.md",
    "sre-scout":              "sre-scout.md",
    "reconciler":             "inbox-manager.md",
    "inbox-manager":          "inbox-manager.md",
    "product-archaeology":    "product-archaeology.md",
    "vintage-agent":          "vintage-agent.md",
    "wayback-cdx":            "wayback-cdx.md",
    "job-source-discovery":   "job-source-discovery.md",
    "workflow-intelligence":  "workflow-intelligence.md",
    "skill-improver":         "skill-improver.md",
    "peer-review":            "inbox-manager.md",
    "whiteboard-scorer":      "whiteboard-agent.md",
    "company-registry":       "company-registry-crawler.md",
    "market-scout":           "market-scout.md",
    "social-media-agent":     "social-media-agent.md",
    "nightly-rollup":         "nightly-rollup.md",
}

# ── Heartbeat helpers ───────────────────────────────────────────────────────

def write_heartbeat(agent: str, status: str, notes: str = ""):
    """Append one heartbeat entry to heartbeat-log.json."""
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "agent": agent,
        "status": status,
        "notes": notes
    }
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"_schema": "1.0", "_description": "Daily agent checkin log", "entries": []}

        data["entries"].append(entry)

        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[run-agent] WARNING: could not write heartbeat: {e}", file=sys.stderr)


def write_stress_log(agent: str, result: str, notes: str = ""):
    """Append a run entry to stress-log.json."""
    stress_file = os.path.join(STUDIO_ROOT, "stress-log.json")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "gate": "post-write",
        "file": f"{agent}.md",
        "findings_count": 0,
        "categories": [],
        "result": result,
        "action_taken": notes
    }
    try:
        if os.path.exists(stress_file):
            with open(stress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"_schema": "1.0", "_description": "Stress tester run log", "runs": []}

        data["runs"].append(entry)

        with open(stress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[run-agent] WARNING: could not write stress log: {e}", file=sys.stderr)


# ── Claude launcher ─────────────────────────────────────────────────────────

def get_agent_prompt(agent_name: str, mode: str = "") -> str:
    """Build the prompt to pass to claude CLI."""
    md_file = AGENT_MAP.get(agent_name)
    if not md_file:
        raise ValueError(f"Unknown agent: {agent_name}")

    md_path = os.path.join(AGENT_MD_DIR, md_file).replace("/", "\\")

    prompt = (
        f'Read the file at "{md_path}" completely. '
        f"That file defines your role as the {agent_name} agent. "
        f"Execute your defined role now. "
        f"Today's date is {datetime.now().strftime('%Y-%m-%d')}. "
        f"Studio root: {STUDIO_ROOT}. "
    )

    if mode == "heartbeat-only":
        prompt += (
            "Run only the heartbeat check: read heartbeat-log.json, "
            "identify any agents that missed their last check-in window, "
            "write a brief supervisor heartbeat entry noting any dead agents."
        )
    elif mode:
        prompt += f"Run in {mode} mode."

    return prompt


def launch_claude(agent_name: str, mode: str = "") -> tuple[bool, str]:
    """
    Launch a claude CLI session for the given agent.
    Returns (success, message).
    """
    try:
        prompt = get_agent_prompt(agent_name, mode)

        # Try claude CLI — must be installed via: npm install -g @anthropic-ai/claude-code
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max
            cwd=STUDIO_ROOT
        )

        if result.returncode == 0:
            output_preview = result.stdout[:200] if result.stdout else "(no output)"
            return True, f"exit 0 — {output_preview}"
        else:
            err = result.stderr[:300] if result.stderr else "(no stderr)"
            return False, f"exit {result.returncode} — {err}"

    except FileNotFoundError:
        return False, (
            "claude CLI not found. "
            "Install with: npm install -g @anthropic-ai/claude-code "
            "then run: claude auth login"
        )
    except subprocess.TimeoutExpired:
        return False, "Timeout after 3600s"
    except Exception as e:
        return False, f"Exception: {traceback.format_exc()}"


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python run-agent.py <agent-name> [mode]", file=sys.stderr)
        sys.exit(1)

    agent_name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else ""

    if agent_name not in AGENT_MAP:
        known = ", ".join(sorted(AGENT_MAP.keys()))
        print(f"Unknown agent '{agent_name}'. Known: {known}", file=sys.stderr)
        write_heartbeat(agent_name, "flagged", f"unknown agent name — dispatch failed")
        sys.exit(1)

    print(f"[run-agent] Starting {agent_name}" + (f" [{mode}]" if mode else ""))
    start_time = datetime.now()

    success, message = launch_claude(agent_name, mode)
    elapsed = (datetime.now() - start_time).seconds

    status = "clean" if success else "flagged"
    notes = f"{'OK' if success else 'FAIL'} in {elapsed}s — {message[:120]}"

    write_heartbeat(agent_name, status, notes)

    if success:
        print(f"[run-agent] {agent_name} completed in {elapsed}s")
    else:
        print(f"[run-agent] {agent_name} FAILED: {message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
