# STUDIO SYSTEM AUDIT — 2026-03-31 (v2)
# Living checklist. Check items off as reviewed and confirmed working.
# STATUS: PENDING / OK / NEEDS_FIX / DEPRECATED / MISSING
#
# KEY CHANGES FROM v1:
# - mobile-inbox.json RETIRED — replaced by sidebar mobile (full features + agent inbox access)
# - session-bridge.py FOUND at root (was session_bridge.py typo in v1)
# - agency/ scripts all FOUND (were in agency/ subfolder — inventory path was wrong)
# - CTW/cx_agent.py FOUND in cx_agent/ subdir
# - game_archaeology/ scripts all FOUND in game_archaeology/ subdir
# - skill-improver.md CREATED (restored from uploaded file)
# - peer-review.md CREATED (Agency character reviewer system)

======================================================================
SECTION 1: AGENTS (run via run-agent.py → Claude Code)
======================================================================

[OK     ] supervisor.md              — Supervisor; AgentSupervisorBriefing
[OK     ] whiteboard-agent.md        — Whiteboard Agent+Scorer; AgentWhiteboardAgent+Scorer
[PENDING] stress-tester.md           — Stress Tester; no dedicated task — verify inline use
[OK     ] janitor.md                 — Janitor; AgentJanitor
[OK     ] git-scout.md               — Git Scout; AgentGitScout
[OK     ] git-commit-agent.md        — Git Commit Agent; AgentGitCommitNightly
[OK     ] intel-feed.md              — Intel Feed; AgentIntelFeed
[OK     ] sre-scout.md               — SRE Scout; SupervisorCheck every 30 min
[PENDING] inbox-manager.md           — Inbox Manager; no dedicated overnight task — add one?
[OK     ] product-archaeology.md     — Product Archaeology; AgentProductArchaeology
[OK     ] vintage-agent.md           — Vintage Agent; OvernightVintageAgent
[PENDING] wayback-cdx.md             — Wayback CDX; AgentCommonCrawlTrigger — verify last run
[OK     ] job-source-discovery.md    — Job Source Discovery; MonthlyJobDiscovery
[PENDING] workflow-intelligence.md   — Workflow Intelligence; AgentWorkflowIntelligence — verify
[DEPRECATED] nightly-rollup.md       — SPEC ONLY — replaced by nightly_rollup.py (FIXED)
[OK     ] ai-intel-agent.md          — AI Intel Agent; AgentAIIntel
[DEPRECATED] auto-answer.md          — SPEC ONLY — replaced by auto_answer_gemini.py (FIXED)
[OK     ] orchestrator.md            — Orchestrator; DailyBriefing (Gemini model FIXED today)
[PENDING] translation-layer.md       — Translation Layer; no dedicated task
[PENDING] market-scout.md            — Market Scout; no dedicated task
[PENDING] social-media-agent.md      — Social Media Agent; no dedicated task
[PENDING] company-registry-crawler.md — Company Registry Crawler; no dedicated task
[NEEDS_FIX] ghost-book-division.md   — DEAD since Mar 22; GhostBookRescan task broken
[PENDING] art-department.md          — Art Department; no dedicated task
[DEPRECATED] ai-gateway.md           — Reference doc, not an agent — verify or remove
[PENDING] listing-optimizer.md       — Listing Optimizer Agent; no dedicated task
[PENDING] changelog-agent.md         — Changelog Agent; NightlyCommit
[OK     ] peer-review.md             — CREATED TODAY; AgentPeerReview task exists
[OK     ] skill-improver.md          — RESTORED TODAY; AgentSkillImprover task exists

======================================================================
SECTION 2: SCHEDULED PYTHON SCRIPTS
======================================================================

[OK     ] nightly_rollup.py          — FIXED today. AgentNightlyRollup → nightly-rollup.bat
[OK     ] auto_answer_gemini.py      — FIXED encoding today. OvernightAutoAnswer 3:30 AM
[OK     ] ai_intel_run.py            — Running. AgentAIIntel overnight
[OK     ] ai_services_rankings.py    — Running. Schema 2.0 upgraded today. 5:30 AM daily
[OK     ] whiteboard_score.py        — Running. OvernightWhiteboardScore
[OK     ] inject_sidebar_data.py     — Running. Sidebar inject overnight

======================================================================
SECTION 3: SERVICES (always-on or on-demand)
======================================================================

[OK     ] studio_bridge.py           — Port 11435; SidebarBridge in Task Scheduler
[OK     ] serve_sidebar_server.py    — Port 8765; serve-sidebar.bat
[PENDING] sidebar_http.py            — Alt sidebar server; verify vs serve_sidebar_server.py
[OK     ] session-bridge.py          — FOUND (was listed as session_bridge.py). Verify running.

======================================================================
SECTION 4: UTILITY SCRIPTS
======================================================================

[OK     ] session-startup.py         — Running every session. Vector path clean.
[OK     ] context-vector-store.py    — 595 chunks indexed
[OK     ] run-agent.py               — Task Scheduler dispatcher
[PENDING] run_inbox_sync.py          — Inbox daily sync; verify task wired
[PENDING] check-drift.py             — AgentCheckDrift; verify last run
[OK     ] generate-context.py        — Manual utility
[OK     ] update_asset_usage.py      — Asset tracker

======================================================================
SECTION 5: TASK SCHEDULER — KNOWN STATUS
======================================================================

[OK     ] AgentAIIntel               — ai_intel_run.py overnight; running
[PENDING] AgentCheckDrift            — check-drift.py; verify last run time
[PENDING] AgentCommonCrawlTrigger    — wayback-cdx.md; verify last run
[PENDING] AgentGitCommitNightly      — git-commit-agent.md; missed 3 nights (quota). Now OK.
[OK     ] AgentGitScout              — git-scout.md; running
[PENDING] AgentHeartbeatCheck        — verify last run
[PENDING] AgentIntelFeed             — intel-feed.md; verify vs AgentAIIntel (overlap?)
[PENDING] AgentJanitor               — janitor.md; verify last run
[OK     ] AgentNightlyRollup         — FIXED today → nightly_rollup.py via bat
[OK     ] AgentPeerReview            — peer-review.md CREATED today
[OK     ] AgentProductArchaeology    — running; product-archaeology overnight
[OK     ] AgentSkillImprover         — skill-improver.md RESTORED today
[OK     ] AgentSupervisorBriefing    — running
[OK     ] AgentWhiteboardAgent       — running
[OK     ] AgentWhiteboardScorer      — running
[PENDING] AgentWorkflowIntelligence  — verify last run
[PENDING] DailyBriefing              — verify vs AgentSupervisorBriefing (overlap?)
[NEEDS_FIX] GhostBookRescan          — DEAD since Mar 22 — needs new target
[PENDING] MirofishTest               — last run date unknown
[OK     ] MonthlyJobDiscovery        — job-source-discovery.md; monthly
[PENDING] NightlyCommit              — missed quota 3 nights; verify recovery
[OK     ] OvernightAutoAnswer        — FIXED encoding today
[PENDING] OvernightGhostBookPass3    — ghost book pass 3; verify status
[OK     ] OvernightJobDelta          — FIXED PermissionError today
[OK     ] OvernightProductArchaeology — running
[OK     ] OvernightVintageAgent      — running; all decades schema-complete
[OK     ] OvernightWhiteboardScore   — running
[OK     ] SupervisorCheck            — sre-scout.md every 30 min

======================================================================
SECTION 6: OTHER PROJECT SCRIPTS
======================================================================

[OK     ] listing-optimizer/ebay_oauth.py          — Live today; token cached 2h
[OK     ] job-match/job_daily_harvest.py            — PermissionError FIXED today
[PENDING] job-match/job_source_discovery_monthly.py — verify monthly task wired
[OK     ] ghost-book/pass1_find_candidates.py       — OK
[OK     ] ghost-book/pass2_validate.py              — OK
[OK     ] agency/character_creator.py               — in agency/ (inventory path was wrong)
[OK     ] agency/character_batch_builder.py         — in agency/; PermissionError FIXED today
[OK     ] agency/mirofish-grading-interface.py      — in agency/
[OK     ] cx_agent/cx_agent.py                      — in cx_agent/ subdir
[OK     ] game_archaeology/run_game_archaeology_weekly.py     — in game_archaeology/
[OK     ] game_archaeology/game_archaeology_digest_generator.py — in game_archaeology/

======================================================================
SECTION 7: INBOX / NOTIFICATION SYSTEM
======================================================================

RETIRED:
[DEPRECATED] mobile-inbox.json        — RETIRED. Replaced by sidebar mobile.
[DEPRECATED] mobile-inbox.html        — RETIRED. Replaced by sidebar mobile.
[DEPRECATED] mobile-studio.html       — RETIRED. Replaced by sidebar mobile.

ACTIVE NOTIFICATION PATHS:
[PENDING] supervisor-inbox.json       — verify WARN/ALERT items surface on sidebar
[PENDING] sidebar-agent.html          — verify agent inbox tab shows new items
[PENDING] Whiteboard 9+ → inbox       — verify same-night promotion works
[PENDING] Asset creation → asset-log  — verify asset-log.json → sidebar display
[PENDING] SRE DEGRADED → sidebar      — verify DEGRADED status shows in sidebar

======================================================================
SECTION 8: WHITEBOARD BUILD ITEMS (score >= 7)
======================================================================

[PENDING] [9] Higgsfield Backwards Design           — BUILD (P0 — needs GPU/RTX first)
[PENDING] [8] Horror Games 1000+ Review             — PUBLISH (low effort, content play)
[PENDING] [8] eBay Consensus Engine                 — BUILD (moved to build queue today)
[PENDING] [8] AI Services Client Website            — BUILD (high revenue potential)
[PENDING] [8] Traitor Protocol Adversarial Testing  — BUILD (studio security utility)
[PENDING] [8] War Room Decision Protocol            — PITCH
[PENDING] [8] Ghost Book Script Vault               — BUILD (connects to ghost-book pipeline)
[PENDING] [7] Historical Twins Division             — BUILD (Tesla/da Vinci track)
[PENDING] [7] Ancient Tech Grading System           — BUILD (connects to vintage agent)
[PENDING] [7] Creative Review Agent                 — BUILD (studio utility)

======================================================================
SECTION 9: KNOWN ISSUES REMAINING
======================================================================

[!] GhostBookRescan DEAD — old script killed Mar 22. CHECK: new version may exist
    in agency/ from Opera session this afternoon. Verify before re-wiring task.

[RESOLVED] Intel Feed vs AI Intel Agent — DISTINCT, NOT OVERLAP:
    intel-feed.md = broad tech/stress intelligence for stress-tester (deprecations,
    security vulns, API changes, community signals). Writes to stress-intel.md.
    ai-intel-agent.md = daily AI landscape specifically — what models exist, what
    tiers/pricing are available, how to route work to free tiers. Writes to
    ai-intel-daily.json + ai-intel-summary.txt. BOTH needed. Keep both.

[RESOLVED] DailyBriefing vs AgentSupervisorBriefing — DISTINCT, NOT DUPLICATE:
    DailyBriefing (8:00 AM) → runs orchestrator-briefing.bat → loads orchestrator.md
    → writes orchestrator-briefing.json (Top 3 for Joe, agent queue, blockers)
    AgentSupervisorBriefing (8:00 AM) → runs run-agent.py supervisor → loads supervisor.md
    → dispatch engine, greenlight proposals, efficiency-ledger
    SAME TIME but different jobs: orchestrator = what to work on, supervisor = dispatch engine
    VERDICT: both run at 8 AM and are complementary. Keep both. Consider staggering
    by 15 min (orchestrator first at 8:00, supervisor at 8:15) to avoid contention.

[PENDING] sidebar_http.py vs serve_sidebar_server.py — sidebar-agent.html is v2.1
    Current active sidebar: sidebar-agent.html (1278 lines, v2.1 [6642])
    No mobile-inbox.json references in current sidebar — already clean.
    Sidebar has agent inbox concept. Need to verify which server bat is active.
    Action: check serve-sidebar.bat to see which .py it calls.

[RESOLVED] mobile-inbox.json — confirmed RETIRED. sidebar-agent.html has 0 references.
    peer-review.md updated to write to supervisor-inbox.json instead.
    "Surfacing" = writing to supervisor-inbox.json with WARN/ALERT urgency,
    which sidebar Agent Inbox tab reads on refresh and displays as a card.

[PENDING] Zanat integration — queued for evaluation session
[PENDING] AI services rankings buzz detection — not firing, needs redesign
[PENDING] Ghost book scoring rubric calibrated too harshly — avg 2.98, needs rubric review
