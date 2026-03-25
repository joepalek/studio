"""
generate-context.py
Regenerates studio-context.md from project state files, agent .md files,
standing-rules.json, and whiteboard.json.
Runs at every Claude Code session start via SessionStart hook.
No truncation. Complete data only.
"""

import json
import os
import re
from datetime import datetime

STUDIO = "G:/My Drive/Projects/_studio"
PROJECTS_ROOT = "G:/My Drive/Projects"
OUTPUT = os.path.join(STUDIO, "studio-context.md")

PROJECTS = [
    "acuscan-ar",
    "arbitrage-pulse",
    "CTW",
    "hibid-analyzer",
    "job-match",
    "listing-optimizer",
    "nutrimind",
    "sentinel-core",
    "sentinel-performer",
    "sentinel-viewer",
    "squeeze-empire",
    "whatnot-apps",
]

# Agent .md files to include descriptions from (in _studio root)
AGENT_MDS = [
    "orchestrator.md",
    "supervisor.md",
    "ai-gateway.md",
    "sre-scout.md",
    "janitor.md",
    "whiteboard-agent.md",
    "ghost-book-division.md",
    "product-archaeology.md",
    "market-scout.md",
    "intel-feed.md",
    "job-source-discovery.md",
    "job-source-crawler.md",
    "company-registry-crawler.md",
    "art-department.md",
    "vintage-agent.md",
    "translation-layer.md",
    "wayback-cdx.md",
    "git-commit-agent.md",
    "changelog-agent.md",
    "cost-monitor.md",
    "workflow-intelligence.md",
    "inbox-manager.md",
    "session-activity-bridge.md",
    "auto-answer.md",
    "stress-tester.md",
]


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"_load_error": str(e)}


def load_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def extract_agent_description(md_text):
    """Extract the Role section or first substantive paragraph from an agent .md file."""
    if not md_text:
        return "(could not read file)"

    lines = md_text.splitlines()
    result = []
    in_role = False

    for line in lines:
        # Capture the ## Role section if it exists
        if re.match(r"^#{1,3}\s*(Role|Description|Overview|What I Do)", line, re.IGNORECASE):
            in_role = True
            result.append(line)
            continue
        # Stop at the next section heading after Role
        if in_role and re.match(r"^#{1,3}\s+", line) and result:
            break
        if in_role:
            result.append(line)

    if result:
        return "\n".join(result).strip()

    # Fallback: first non-empty paragraph after the title
    body = []
    past_title = False
    for line in lines:
        if not past_title:
            if re.match(r"^#", line):
                past_title = True
            continue
        if line.strip() == "" and body:
            break
        if line.strip():
            body.append(line)

    return "\n".join(body).strip() if body else lines[0] if lines else "(empty)"


def fmt_state_full(project, state):
    """Render all fields from a state.json with no truncation."""
    if state is None:
        return f"### {project}\n  (no state file found)\n"

    lines = [f"### {project}"]

    if "_load_error" in state:
        lines.append(f"  ERROR loading state: {state['_load_error']}")
        # Try CONTEXT.md fallback
        ctx = load_text(os.path.join(PROJECTS_ROOT, project, "CONTEXT.md"))
        if ctx:
            lines.append("")
            lines.append("  CONTEXT.md:")
            for l in ctx.splitlines():
                lines.append(f"  {l}")
        return "\n".join(lines)

    if "_raw_context" in state:
        lines.append("  (state.json not found — CONTEXT.md content follows)")
        lines.append("")
        for l in state["_raw_context"].splitlines():
            lines.append(f"  {l}")
        return "\n".join(lines)

    # Dump every key-value pair
    def render_value(v, indent=4):
        pad = " " * indent
        if isinstance(v, dict):
            out = []
            for k2, v2 in v.items():
                out.append(f"{pad}{k2}: {render_value(v2, indent + 2)}")
            return "\n" + "\n".join(out)
        elif isinstance(v, list):
            if not v:
                return "[]"
            out = []
            for item in v:
                out.append(f"{pad}- {render_value(item, indent + 2)}")
            return "\n" + "\n".join(out)
        else:
            return str(v)

    for key, val in state.items():
        lines.append(f"  {key}: {render_value(val)}")

    return "\n".join(lines)


def read_state(project):
    base = os.path.join(PROJECTS_ROOT, project)
    for name in ["state.json", f"{project}-state.json"]:
        path = os.path.join(base, name)
        if os.path.exists(path):
            return load_json(path)
    # Fall back to full CONTEXT.md
    ctx = load_text(os.path.join(base, "CONTEXT.md"))
    if ctx:
        return {"_raw_context": ctx}
    return None


def build_context():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines.append("# STUDIO SYSTEM CONTEXT")
    lines.append(f"Generated: {now} | Auto-built by generate-context.py")
    lines.append("")

    # ── WHO IS JOE ────────────────────────────────────────────────────────────
    lines.append("## WHO IS JOE")
    lines.append("")
    lines.append(
        "Joe is a solo developer, active eBay reseller (~572 listings), and job seeker targeting "
        "remote Trust & Safety / Fraud Analyst roles. He runs an autonomous AI-assisted project "
        "studio from a Windows machine using Claude Code CLI, Google Drive, and a mix of free-tier "
        "AI APIs. He works in sessions (1-3 hours) and relies on persistent state files and an "
        "orchestration layer to pick up exactly where he left off."
    )
    lines.append("")
    lines.append(
        "Background: eBay seller for years, deep knowledge of resale markets and auction platforms "
        "(HiBid, Whatnot). Applying to Whatnot for Fraud Agent / Trust & Safety / CX Overnight roles. "
        "Has a character AI project (CTW) used for behavior validation. Building a job scraper to "
        "replace income."
    )
    lines.append("")
    lines.append(
        "Work style: Concise responses. No filler. Approve a plan before executing. Session-oriented — "
        "context preserved in CONTEXT.md per project. Uses Claude Code CLI not Claude.ai."
    )
    lines.append("")
    lines.append(
        "Financial context: Income replacement is the #1 priority. LLC formation ($300 Tennessee "
        "filing fee) is blocking the highest-upside project (Sentinel). Daily eBay revenue is the "
        "current income floor."
    )
    lines.append("")

    # ── ARCHITECTURE ──────────────────────────────────────────────────────────
    lines.append("## ARCHITECTURE")
    lines.append("")
    lines.append("Stack: Windows 11, Claude Code CLI, Python 3.13, Node v24, Git/GitHub Pages,")
    lines.append("Supabase (mobile inbox), Google Drive sync, Ollama (local LLM, gemma3:4b),")
    lines.append("Gemini Flash free tier, OpenRouter (DeepSeek coder), GitHub Pages")
    lines.append("(studio.html dashboard + sidebar-agent.html Gemini assistant).")
    lines.append("")
    lines.append("Session flow: Claude Code CLI → CLAUDE.md rules → SRE Scout health check →")
    lines.append("generate-context.py refreshes studio-context.md → work begins.")
    lines.append("")
    lines.append("Scheduler (Windows Task Scheduler):")
    lines.append("  nightly-commit     — commits all dirty projects nightly")
    lines.append("  supervisor-check   — runs supervisor.md health review")
    lines.append("  orchestrator-briefing — updates orchestrator-briefing.json")
    lines.append("")

    # ── AGENT DESCRIPTIONS ────────────────────────────────────────────────────
    lines.append("## AGENTS")
    lines.append("")
    for fname in AGENT_MDS:
        path = os.path.join(STUDIO, fname)
        text = load_text(path)
        agent_name = fname.replace(".md", "")
        lines.append(f"### {agent_name}")
        if text:
            desc = extract_agent_description(text)
            lines.append(desc)
        else:
            lines.append("  (file not found)")
        lines.append("")

    # ── PROJECT STATUS ────────────────────────────────────────────────────────
    lines.append("## PROJECT STATUS")
    lines.append("")
    for project in PROJECTS:
        state = read_state(project)
        lines.append(fmt_state_full(project, state))
        lines.append("")

    # ── STANDING RULES ────────────────────────────────────────────────────────
    lines.append("## STANDING RULES")
    lines.append("")
    rules_data = load_json(os.path.join(STUDIO, "standing-rules.json"))
    if "_load_error" in rules_data:
        lines.append(f"  ERROR: {rules_data['_load_error']}")
    elif "rules" in rules_data:
        rules = rules_data["rules"]
        lines.append(f"Total: {len(rules)} rules")
        lines.append("")
        for r in rules:
            lines.append(f"  {r.get('id', '?')}")
            lines.append(f"    trigger:     {r.get('trigger', '')}")
            lines.append(f"    action:      {r.get('action', '')}")
            applies = r.get("applies_to", [])
            if applies:
                lines.append(f"    applies_to:  {', '.join(applies) if isinstance(applies, list) else applies}")
            lines.append(f"    created:     {r.get('created', '')}")
            lines.append(f"    approved_by: {r.get('approved_by', '')}")
            lines.append(f"    times_applied: {r.get('times_applied', 0)}")
            notes = r.get("notes") or r.get("note")
            if notes:
                lines.append(f"    notes:       {notes}")
            lines.append("")
    else:
        lines.append("  (no rules found in file)")
    lines.append("")

    # ── WHITEBOARD ────────────────────────────────────────────────────────────
    lines.append("## WHITEBOARD")
    lines.append("")
    wb_data = load_json(os.path.join(STUDIO, "whiteboard.json"))
    if "_load_error" in wb_data:
        lines.append(f"  ERROR: {wb_data['_load_error']}")
    elif "items" in wb_data:
        items = wb_data["items"]
        updated = wb_data.get("updated", "")
        if updated:
            lines.append(f"Last updated: {updated}")

        def score_key(x):
            gs = x.get("gemini_score", {})
            return gs.get("total_score", 0) if isinstance(gs, dict) else 0

        sorted_items = sorted(items, key=score_key, reverse=True)
        lines.append(f"Total items: {len(sorted_items)}")
        lines.append("")
        for item in sorted_items:
            title = item.get("title", "(no title)")
            score = score_key(item)
            status = item.get("status", "")
            source = item.get("source", "")
            lines.append(f"  [{score}/10] {title}")
            lines.append(f"    id:      {item.get('id', '')}")
            lines.append(f"    type:    {item.get('type', '')}")
            lines.append(f"    status:  {status}")
            lines.append(f"    source:  {source}")
            desc = item.get("description", "")
            if desc:
                lines.append(f"    description: {desc}")
            gs = item.get("gemini_score", {})
            if isinstance(gs, dict) and gs:
                lines.append(f"    score_breakdown:")
                for k, v in gs.items():
                    lines.append(f"      {k}: {v}")
            tags = item.get("tags", [])
            if tags:
                lines.append(f"    tags:    {', '.join(tags)}")
            lines.append(f"    added:   {item.get('added', '')}")
            url = item.get("source_url", "")
            if url:
                lines.append(f"    url:     {url}")
            lines.append("")
    else:
        lines.append("  (no items found in whiteboard.json)")
    lines.append("")

    # ── STUDIO CURRENT STATE ──────────────────────────────────────────────────
    lines.append("## STUDIO CURRENT STATE")
    lines.append("")
    studio_state = load_json(os.path.join(STUDIO, "state.json"))
    if "_load_error" in studio_state:
        lines.append(f"  ERROR: {studio_state['_load_error']}")
    elif studio_state:
        for key, val in studio_state.items():
            if isinstance(val, (dict, list)):
                lines.append(f"  {key}: {json.dumps(val, indent=4)}")
            else:
                lines.append(f"  {key}: {val}")
    else:
        lines.append("  No studio state.json found.")
    lines.append("")

    lines.append("---")
    lines.append(f"End of context. Generated: {now}")

    return "\n".join(lines)


if __name__ == "__main__":
    content = build_context()
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(content)
    word_count = len(content.split())
    char_count = len(content)
    print(f"[generate-context] studio-context.md regenerated — {word_count} words, {char_count} chars")
