
MAX_CONSECUTIVE_FAILURES = 3  # Bezos Rule
import json, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO = Path("G:/My Drive/Projects/_studio")
PROJECTS = Path("G:/My Drive/Projects")

# Agent .md files (run via run-agent.py)
AGENT_MAP = {
    "supervisor.md": "Supervisor",
    "whiteboard-agent.md": "Whiteboard Agent + Scorer",
    "stress-tester.md": "Stress Tester",
    "janitor.md": "Janitor",
    "git-scout.md": "Git Scout",
    "git-commit-agent.md": "Git Commit Agent",
    "intel-feed.md": "Intel Feed",
    "sre-scout.md": "SRE Scout",
    "inbox-manager.md": "Inbox Manager / Reconciler",
    "product-archaeology.md": "Product Archaeology",
    "vintage-agent.md": "Vintage Agent",
    "wayback-cdx.md": "Wayback CDX",
    "job-source-discovery.md": "Job Source Discovery",
    "workflow-intelligence.md": "Workflow Intelligence",
    "nightly-rollup.md": "Nightly Rollup (spec only — replaced by nightly_rollup.py)",
    "ai-intel-agent.md": "AI Intel Agent",
    "auto-answer.md": "Auto Answer (spec only — replaced by auto_answer_gemini.py)",
    "orchestrator.md": "Orchestrator",
    "translation-layer.md": "Translation Layer",
    "market-scout.md": "Market Scout",
    "social-media-agent.md": "Social Media Agent",
    "company-registry-crawler.md": "Company Registry Crawler",
    "ghost-book-division.md": "Ghost Book Division",
    "art-department.md": "Art Department",
    "ai-gateway.md": "AI Gateway",
    "listing-optimizer.md": "Listing Optimizer Agent",
    "changelog-agent.md": "Changelog Agent",
    "peer-review.md": "Peer Review",
    "skill-improver.md": "Skill Improver",
}

# Python scripts — scheduled or utility
PY_SCRIPTS = {
    "nightly_rollup.py": ("SCHEDULED", "1:00 AM daily — writes daily-digest.json"),
    "auto_answer_gemini.py": ("SCHEDULED", "3:30 AM — Gemini inbox triage"),
    "ai_intel_run.py": ("SCHEDULED", "overnight — AI news aggregation"),
    "ai_services_rankings.py": ("SCHEDULED", "5:30 AM — update service rankings"),
    "whiteboard_score.py": ("SCHEDULED", "overnight — score whiteboard items"),
    "session-startup.py": ("UTILITY", "Session context loader — ChromaDB vector query"),
    "context-vector-store.py": ("UTILITY", "ChromaDB vector store manager"),
    "check-drift.py": ("UTILITY", "Check project drift"),
    "run-agent.py": ("DISPATCHER", "Task Scheduler → Claude Code agent launcher"),
    "run_inbox_sync.py": ("UTILITY", "Inbox daily sync across all projects"),
    "inject_sidebar_data.py": ("SCHEDULED", "Sidebar data injector"),
    "update_asset_usage.py": ("UTILITY", "Asset usage tracker"),
    "session_bridge.py": ("SERVICE", "Session bridge for sidebar chat → ChromaDB"),
    "studio_bridge.py": ("SERVICE", "Studio bridge on port 11435"),
    "serve_sidebar_server.py": ("SERVICE", "HTTP server for sidebar on port 8765"),
    "sidebar_http.py": ("SERVICE", "Sidebar HTTP server"),
    "generate-context.py": ("UTILITY", "Generate studio context file"),
    "check_ghostbook.py": ("UTILITY", "Ghost book eval diagnostic"),
    "fix_ghostbook_titles.py": ("UTILITY", "Ghost book title join fix"),
    "upgrade_rankings.py": ("UTILITY", "Rankings schema upgrade tool"),
    "write_answers.py": ("UTILITY", "Decision answer writer"),
    "check_ebay_token.py": ("UTILITY", "eBay token verification"),
    "show_pending.py": ("UTILITY", "Show pending decisions across projects"),
}

# Scheduled tasks
TASKS = {}
sched_dir = STUDIO / "scheduler"
if sched_dir.exists():
    for f in sched_dir.glob("*.xml"):
        TASKS[f.name] = f.stem

# Non-studio project scripts
OTHER_PROJECTS = {
    "listing-optimizer": ["ebay_oauth.py", "listing-optimizer-state.json"],
    "job-match": ["job_daily_harvest.py", "job_source_discovery_monthly.py", "state.json"],
    "ghost-book": ["pass1_find_candidates.py", "pass2_validate.py"],
    "agency": ["character_creator.py", "character_batch_builder.py", "mirofish-grading-interface.py"],
    "CTW": ["cx_agent.py"],
    "game_archaeology": ["run_game_archaeology_weekly.py", "game_archaeology_digest_generator.py"],
}

print("=" * 70)
print("STUDIO SYSTEM INVENTORY — 2026-03-31")
print("=" * 70)

print(f"\n{'─'*70}")
print("AGENTS (Claude Code via run-agent.py)")
print(f"{'─'*70}")
for fname, desc in sorted(AGENT_MAP.items()):
    exists = (STUDIO / fname).exists()
    status = "✓" if exists else "MISSING"
    print(f"  [{status}] {fname:<40} {desc}")

print(f"\n{'─'*70}")
print("PYTHON SCRIPTS")
print(f"{'─'*70}")
for fname, (stype, desc) in sorted(PY_SCRIPTS.items()):
    exists = (STUDIO / fname).exists()
    status = "✓" if exists else "MISSING"
    print(f"  [{status}] [{stype:<12}] {fname:<40} {desc}")

print(f"\n{'─'*70}")
print("TASK SCHEDULER TASKS")
print(f"{'─'*70}")
for xml, name in sorted(TASKS.items()):
    print(f"  {name}")

print(f"\n{'─'*70}")
print("OTHER PROJECT SCRIPTS")
print(f"{'─'*70}")
for proj, files in OTHER_PROJECTS.items():
    print(f"\n  {proj}:")
    for f in files:
        path = PROJECTS / proj / f
        exists = path.exists()
        status = "✓" if exists else "MISSING"
        print(f"    [{status}] {f}")

print(f"\n{'─'*70}")
print("WHITEBOARD — Agent/System items (score >= 7)")
print(f"{'─'*70}")
try:
    wb = json.load(open(STUDIO / "whiteboard.json", encoding='utf-8', errors='replace'))
    items = wb.get('items', [])
    agent_items = [i for i in items if i.get('gemini_score', {}).get('total_score', 0) >= 7]
    agent_items.sort(key=lambda x: x['gemini_score']['total_score'], reverse=True)
    _consecutive_failures = 0
    for i in agent_items[:20]:
        score = i['gemini_score']['total_score']
        action = i['gemini_score'].get('recommended_action', '?')
        title = i.get('title', '')[:65]
        print(f"  [{score}/10 {action:<8}] {title}")
except Exception as e:
    print(f"  ERROR: {e}")
