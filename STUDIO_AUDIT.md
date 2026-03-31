# STUDIO SYSTEM AUDIT — 2026-03-31
# Living checklist. Check items off as reviewed and confirmed working.
# Format: [STATUS] Item — notes
# STATUS: PENDING / OK / NEEDS_FIX / DEPRECATED / MISSING

======================================================================
SECTION 1: AGENTS (run via run-agent.py → Claude Code)
======================================================================
Each agent needs: .md file exists / Task Scheduler task registered /
last heartbeat within 48h / output file written / notification path verified

[ ] supervisor.md              — Supervisor; runs AgentSupervisorBriefing
[ ] whiteboard-agent.md        — Whiteboard Agent+Scorer; AgentWhiteboardAgent+Scorer
[ ] stress-tester.md           — Stress Tester; no dedicated task (called inline)
[ ] janitor.md                 — Janitor; AgentJanitor
[ ] git-scout.md               — Git Scout; AgentGitScout
[ ] git-commit-agent.md        — Git Commit Agent; AgentGitCommitNightly
[ ] intel-feed.md              — Intel Feed; AgentIntelFeed
[ ] sre-scout.md               — SRE Scout; SupervisorCheck (every 30 min)
[ ] inbox-manager.md           — Inbox Manager; no dedicated overnight task
[ ] product-archaeology.md     — Product Archaeology; AgentProductArchaeology
[ ] vintage-agent.md           — Vintage Agent; OvernightVintageAgent
[ ] wayback-cdx.md             — Wayback CDX; AgentCommonCrawlTrigger
[ ] job-source-discovery.md    — Job Source Discovery; MonthlyJobDiscovery
[ ] workflow-intelligence.md   — Workflow Intelligence; AgentWorkflowIntelligence
[ ] nightly-rollup.md          — SPEC ONLY — replaced by nightly_rollup.py
[ ] ai-intel-agent.md          — AI Intel Agent; AgentAIIntel
[ ] auto-answer.md             — SPEC ONLY — replaced by auto_answer_gemini.py
[ ] orchestrator.md            — Orchestrator; AgentSupervisorBriefing / DailyBriefing
[ ] translation-layer.md       — Translation Layer; no dedicated task
[ ] market-scout.md            — Market Scout; no dedicated task
[ ] social-media-agent.md      — Social Media Agent; no dedicated task
[ ] company-registry-crawler.md — Company Registry Crawler; no dedicated task
[ ] ghost-book-division.md     — Ghost Book Division; GhostBookRescan (DEAD since Mar 22)
[ ] art-department.md          — Art Department; no dedicated task
[ ] ai-gateway.md              — AI Gateway (reference doc, not an agent)
[ ] listing-optimizer.md       — Listing Optimizer Agent; no dedicated task
[ ] changelog-agent.md         — Changelog Agent; NightlyCommit
[ ] MISSING: peer-review.md    — Peer Review; AgentPeerReview task exists but .md MISSING
[ ] MISSING: skill-improver.md — Skill Improver; AgentSkillImprover task exists but .md MISSING

======================================================================
SECTION 2: SCHEDULED PYTHON SCRIPTS
======================================================================
[ ] nightly_rollup.py          — OK: Fixed today. AgentNightlyRollup → nightly-rollup.bat
[ ] auto_answer_gemini.py      — OK: Fixed encoding today. OvernightAutoAnswer 3:30 AM
[ ] ai_intel_run.py            — OK: Running. AgentAIIntel overnight
[ ] ai_services_rankings.py    — OK: Running. 5:30 AM daily
[ ] whiteboard_score.py        — OK: Running. OvernightWhiteboardScore
[ ] inject_sidebar_data.py     — OK: Running. Sidebar inject overnight

======================================================================
SECTION 3: SERVICES (always-on or on-demand)
======================================================================
[ ] studio_bridge.py           — Port 11435; SidebarBridge in Task Scheduler
[ ] serve_sidebar_server.py    — Port 8765; serve-sidebar.bat
[ ] sidebar_http.py            — Sidebar HTTP alt server
[ ] MISSING: session_bridge.py — Listed as SERVICE but file not found at root

======================================================================
SECTION 4: UTILITY SCRIPTS
======================================================================
[ ] session-startup.py         — OK: Running every session. Vector path clean.
[ ] context-vector-store.py    — OK: 595 chunks indexed
[ ] run-agent.py               — OK: Task Scheduler dispatcher
[ ] run_inbox_sync.py          — Inbox daily sync — needs task verification
[ ] check-drift.py             — AgentCheckDrift — verify it runs
[ ] generate-context.py        — Manual utility
[ ] update_asset_usage.py      — Asset tracker

======================================================================
SECTION 5: TASK SCHEDULER — FULL TASK LIST
======================================================================
[ ] AgentAIIntel               — ai_intel_run.py overnight
[ ] AgentCheckDrift            — check-drift.py
[ ] AgentCommonCrawlTrigger    — wayback-cdx.md
[ ] AgentGitCommitNightly      — git-commit-agent.md
[ ] AgentGitScout              — git-scout.md
[ ] AgentHeartbeatCheck        — heartbeat check
[ ] AgentIntelFeed             — intel-feed.md
[ ] AgentJanitor               — janitor.md
[ ] AgentNightlyRollup         — nightly_rollup.py via bat (FIXED TODAY)
[ ] AgentPeerReview            — peer-review.md MISSING
[ ] AgentProductArchaeology    — product-archaeology.md
[ ] AgentSkillImprover         — skill-improver.md MISSING
[ ] AgentSupervisorBriefing    — supervisor.md / orchestrator.md
[ ] AgentWhiteboardAgent       — whiteboard-agent.md
[ ] AgentWhiteboardScorer      — whiteboard-agent.md
[ ] AgentWorkflowIntelligence  — workflow-intelligence.md
[ ] DailyBriefing              — orchestrator/supervisor
[ ] GhostBookRescan            — DEAD since Mar 22
[ ] MirofishTest               — mirofish context test
[ ] MonthlyJobDiscovery        — job-source-discovery.md
[ ] NightlyCommit              — git-commit-agent.md / changelog
[ ] OvernightAutoAnswer        — auto_answer_gemini.py (FIXED TODAY)
[ ] OvernightGhostBookPass3    — ghost book pass 3
[ ] OvernightJobDelta          — job_daily_harvest.py (FIXED TODAY)
[ ] OvernightProductArchaeology — product-archaeology.md
[ ] OvernightVintageAgent      — vintage-agent.md
[ ] OvernightWhiteboardScore   — whiteboard_score.py
[ ] SupervisorCheck            — sre-scout.md every 30 min

======================================================================
SECTION 6: OTHER PROJECT SCRIPTS
======================================================================
[ ] listing-optimizer/ebay_oauth.py         — OK: Live, token cached
[ ] job-match/job_daily_harvest.py          — OK: Fixed PermissionError today
[ ] job-match/job_source_discovery_monthly.py — verify monthly task wired
[ ] ghost-book/pass1_find_candidates.py     — OK
[ ] ghost-book/pass2_validate.py            — OK
[ ] MISSING: agency/character_creator.py   — in _studio root, not agency/
[ ] MISSING: agency/character_batch_builder.py — in _studio root, not agency/
[ ] MISSING: agency/mirofish-grading-interface.py — in agency/ but subdir
[ ] MISSING: CTW/cx_agent.py               — in cx_agent/ subdir
[ ] MISSING: game_archaeology scripts      — in game_archaeology/ subdir

======================================================================
SECTION 7: WHITEBOARD — ACTION ITEMS (score >= 7)
======================================================================
BUILD/PUBLISH items to prioritize:
[ ] [9] Higgsfield Backwards Design        — BUILD (P0 with Tesla/da Vinci splats)
[ ] [8] Horror Games 1000+ Review          — PUBLISH (content, low effort)
[ ] [8] eBay Consensus Engine              — BUILD (moved to build queue today)
[ ] [8] AI Services Client Website         — BUILD (whiteboard 8/10)
[ ] [8] Traitor Protocol Adversarial Test  — BUILD (security/AI tool)
[ ] [8] War Room Decision Protocol         — PITCH
[ ] [8] Ghost Book Script Vault            — BUILD
[ ] [7] Historical Twins Division          — BUILD (Tesla/da Vinci track)
[ ] [7] Ancient Tech Grading System        — BUILD (connects to vintage agent)
[ ] [7] Creative Review Agent              — BUILD (studio utility)

======================================================================
SECTION 8: NOTIFICATION / FEEDBACK GAPS
======================================================================
These need to be confirmed working — you should be getting notified:
[ ] Mobile inbox — new decisions pushed nightly — verify you get alerts
[ ] Supervisor inbox WARN/ALERT items — verify escalation path to you
[ ] Asset creation notifications — asset-log.json → sidebar → you
[ ] Whiteboard 9+ items — verify they reach mobile inbox same night
[ ] SRE DEGRADED status — verify it reaches sidebar + mobile

======================================================================
KNOWN ISSUES TO FIX DURING REVIEW
======================================================================
[!] peer-review.md MISSING — AgentPeerReview task will fail nightly
[!] skill-improver.md MISSING — AgentSkillImprover task will fail nightly
[!] session_bridge.py MISSING at root — may be renamed/moved
[!] GhostBookRescan DEAD — needs replacement pointing at new scraper
[!] agency/ scripts show MISSING — they're in _studio root, path mismatch
[!] CTW/cx_agent.py in cx_agent/ subdir — inventory path was wrong
