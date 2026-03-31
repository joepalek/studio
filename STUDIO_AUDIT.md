# STUDIO SYSTEM AUDIT — 2026-03-31 (v3 — ACTIVE REVIEW)
# Legend: [OK] verified good | [PENDING] needs work | [DEPRECATED] retire it
#         [NEEDS_FIX] broken, fix queued | [RESOLVED] closed

======================================================================
SECTION 1: AGENTS
======================================================================
# Task Scheduler last runs (from live check 2026-03-31):
# SupervisorCheck=today, DailyBriefing=today, SupervisorBriefing=today
# GitScout=today, Janitor=today, IntelFeed=today, AIIntel=today
# VectorReindex=today, SidebarInject=today, OvernightAutoAnswer=today
# OvernightJobDelta=today, OvernightVintageAgent=today
# OvernightProductArchaeology=today, AIServicesRankings=today
# AgencyCharacterBuild=today, WorkflowIntelligence=today
# WhiteboardAgent=never, WhiteboardScorer=never, SkillImprover=never
# PeerReview=never, GitCommitNightly=today, HeartbeatCheck=today
# GhostBookRescan=last Nov (DEAD), OvernightGhostBookPass3=last Nov (DEAD)
# MonthlyJobDiscovery=never, CommonCrawlTrigger=never
# GameArchaeologyWeekly=never, MirofishTest=never

[OK     ] supervisor.md              — Running. SupervisorCheck every 30 min.
[OK     ] whiteboard-agent.md        — WhiteboardAgent task exists. Never run yet. OK — will run tonight.
[OK     ] stress-tester.md           — Called inline by Intel Feed. No dedicated task needed.
[OK     ] janitor.md                 — Janitor task. Running today.
[OK     ] git-scout.md               — GitScout. Running today.
[OK     ] git-commit-agent.md        — GitCommitNightly. Running today. Quota issues resolved.
[OK     ] intel-feed.md              — IntelFeed. Running. DISTINCT from ai-intel-agent (see Section 9).
[OK     ] sre-scout.md               — SupervisorCheck every 30 min. Running.
[PENDING] inbox-manager.md           — No dedicated task. Add nightly task or fold into supervisor dispatch.
[OK     ] product-archaeology.md     — OvernightProductArchaeology. Running.
[OK     ] vintage-agent.md           — OvernightVintageAgent. Running. All decades complete.
[PENDING] wayback-cdx.md             — CommonCrawlTrigger exists but never run. Verify intent.
[OK     ] job-source-discovery.md    — MonthlyJobDiscovery. Never run yet — monthly, expected.
[OK     ] workflow-intelligence.md   — WorkflowIntelligence. Running today.
[DEPRECATED] nightly-rollup.md       — Spec only. Replaced by nightly_rollup.py. FIXED today.
[OK     ] ai-intel-agent.md          — AIIntel. Running today.
[DEPRECATED] auto-answer.md          — Spec only. Replaced by auto_answer_gemini.py. FIXED today.
[OK     ] orchestrator.md            — DailyBriefing. Running. Gemini model FIXED today.
[OK     ] translation-layer.md       — Reference/utility. Used by agents internally.
[PENDING] market-scout.md            — No dedicated task. Review if needed or fold into intel-feed.
[PENDING] social-media-agent.md      — No dedicated task. Review scope — is Meta app review done?
[PENDING] company-registry-crawler.md — No dedicated task. Low priority, deferred.
[NEEDS_FIX] ghost-book-division.md   — GhostBookRescan points to OLD pass1_find_candidates.py.
                                        NEW ghost book pipeline from Opera session this afternoon.
                                        ACTION: Check agency/ for new version, update bat target.
[PENDING] art-department.md          — No dedicated task. Runs on demand.
[DEPRECATED] ai-gateway.md           — Reference doc only. Not dispatched as agent. Keep as reference.
[PENDING] listing-optimizer.md       — No dedicated task yet. eBay OAuth live. Build queue item.
[PENDING] changelog-agent.md         — NightlyCommit. Missed 3 nights quota. Now recovered.
[OK     ] peer-review.md             — CREATED today. PeerReview task exists (never run = expected).
[OK     ] skill-improver.md          — RESTORED today. SkillImprover task exists (never run = expected).

======================================================================
SECTION 2: SCHEDULED PYTHON SCRIPTS
======================================================================

[OK     ] nightly_rollup.py          — FIXED today. First real run tonight 1 AM.
[OK     ] auto_answer_gemini.py      — FIXED encoding. Running nightly.
[OK     ] ai_intel_run.py            — Running. 4 HIGH items yesterday.
[OK     ] ai_services_rankings.py    — Running. Schema 2.0 with pricing today.
[OK     ] whiteboard_score.py        — Running. Top 10 stable.
[OK     ] inject_sidebar_data.py     — Running. 46 inbox + 10 whiteboard + 8 assets injected.

======================================================================
SECTION 3: SERVICES
======================================================================

[OK     ] studio_bridge.py           — Port 11435. SidebarBridge task running today.
[OK     ] serve_sidebar_server.py    — Port 8765. Active via serve-sidebar.bat. Confirmed in bat.
[DEPRECATED] sidebar_http.py         — Zero refs in sidebar-agent.html or any bat/script.
                                        Old attempt. Safe to archive. Move to _archive/.
[OK     ] session-bridge.py          — Found at root. Running.

======================================================================
SECTION 4: UTILITY SCRIPTS
======================================================================

[OK     ] session-startup.py         — Running every session. Vector path clean all day.
[OK     ] context-vector-store.py    — 595 chunks indexed.
[OK     ] run-agent.py               — Task Scheduler dispatcher. Working.
[PENDING] run_inbox_sync.py          — No task visible in scheduler. Verify if wired or manual only.
[OK     ] check-drift.py             — CheckDrift task running today.
[OK     ] generate-context.py        — Manual utility.
[OK     ] update_asset_usage.py      — Asset tracker. Running.

======================================================================
SECTION 5: TASK SCHEDULER — VERIFIED STATUS
======================================================================

[OK     ] SupervisorCheck            — Running every 30 min today.
[OK     ] DailyBriefing              — Running today at 8 AM.
[OK     ] SupervisorBriefing         — Running today at 8 AM.
[OK     ] WorkflowIntelligence       — Running today.
[OK     ] AIIntel                    — Running today.
[OK     ] AIServicesRankings         — Running today.
[OK     ] SidebarInject              — Running today.
[OK     ] AgencyCharacterBuild       — Running today. 507 chars.
[OK     ] OvernightAutoAnswer        — FIXED today.
[OK     ] OvernightJobDelta          — FIXED today.
[OK     ] OvernightVintageAgent      — Running. All decades complete.
[OK     ] OvernightProductArchaeology — Running.
[OK     ] OvernightWhiteboardScore   — Running.
[OK     ] VectorReindex              — Running today. 595 chunks.
[OK     ] GitCommitNightly           — Running today.
[OK     ] GitScout                   — Running today.
[OK     ] Janitor                    — Running today.
[OK     ] IntelFeed                  — Running today.
[OK     ] HeartbeatCheck             — Running today.
[OK     ] SidebarBridge              — Running today.
[OK     ] CheckDrift                 — Running today.
[OK     ] NightlyRollup              — FIXED today → nightly_rollup.py. First run tonight.
[OK     ] WhiteboardAgent            — Task exists. Never run = expected (new registration).
[OK     ] WhiteboardScorer           — Task exists. Never run = expected.
[OK     ] SkillImprover              — Task exists. Never run = expected (just restored).
[OK     ] PeerReview                 — Task exists. Never run = expected (just created).
[OK     ] MonthlyJobDiscovery        — Never run = expected (monthly, not yet due).
[OK     ] GameArchaeologyWeekly      — Never run = expected (weekly, not yet due).
[OK     ] MirofishTest               — Never run. Manual/on-demand. OK.
[PENDING] CommonCrawlTrigger         — Never run. Verify if wayback-cdx.md is active or deferred.
[NEEDS_FIX] GhostBookRescan          — Last Nov. Points to old pipeline. Needs new target.
[NEEDS_FIX] OvernightGhostBookPass3  — Last Nov. Part of old pipeline. Check if superseded.
[DEPRECATED] VedicScan / VedicSync   — Vedic Math module closed/deferred. Tasks can be disabled.

======================================================================
SECTION 6: OTHER PROJECT SCRIPTS
======================================================================

[OK     ] listing-optimizer/ebay_oauth.py          — Live. Token cached.
[OK     ] job-match/job_daily_harvest.py            — PermissionError FIXED today.
[PENDING] job-match/job_source_discovery_monthly.py — Monthly. Not yet due. Verify task wired.
[OK     ] ghost-book/pass1_find_candidates.py       — Exists. Used by OLD GhostBookRescan bat.
[OK     ] ghost-book/pass2_validate.py              — Exists.
[OK     ] agency/character_creator.py               — In agency/ subfolder. Running.
[OK     ] agency/character_batch_builder.py         — PermissionError FIXED today.
[OK     ] agency/mirofish-grading-interface.py      — In agency/.
[OK     ] cx_agent/cx_agent.py                      — In cx_agent/ subdir.
[OK     ] game_archaeology/run_game_archaeology_weekly.py  — GameArchaeologyWeekly task. Not yet run.
[OK     ] game_archaeology/game_archaeology_digest_generator.py — In place.

======================================================================
SECTION 7: INBOX / NOTIFICATION SYSTEM
======================================================================

[DEPRECATED] mobile-inbox.json       — RETIRED. Zero refs in current sidebar-agent.html.
[DEPRECATED] mobile-inbox.html       — RETIRED.
[DEPRECATED] mobile-studio.html      — RETIRED. Replaced by sidebar mobile.
[DEPRECATED] sidebar_http.py         — Old server. Zero refs. Archive it.

ACTIVE NOTIFICATION PATHS (verified):
[OK     ] supervisor-inbox.json      — Active. WARN/ALERT urgency → sidebar Agent Inbox tab.
[OK     ] sidebar-agent.html v2.1    — Current sidebar. 1278 lines. Zero mobile-inbox refs.
[PENDING] Sidebar Agent Inbox tab    — Verify it reads supervisor-inbox.json on refresh.
[PENDING] Whiteboard 9+ → inbox      — Verify same-night promotion to supervisor inbox works.
[PENDING] Asset creation → asset-log → sidebar — Verify asset-log.json displays in sidebar.
[PENDING] SRE DEGRADED → sidebar     — Verify DEGRADED status card appears in sidebar.

"SURFACING" DEFINITION (for future reference):
Writing to supervisor-inbox.json with urgency WARN or ALERT.
The sidebar Agent Inbox tab reads it on refresh and shows it as a card.
This IS the notification path — no mobile app, no email, no push.
If you need to know something happened: check sidebar Agent Inbox tab.

======================================================================
SECTION 8: WHITEBOARD BUILD ITEMS (score >= 7)
======================================================================

[PENDING] [9] Higgsfield Backwards Design           — BUILD. Blocked on GPU/RTX hardware.
[PENDING] [8] Horror Games 1000+ Review             — PUBLISH. Low effort. Content play.
[BUILD  ] [8] eBay Consensus Engine                 — Moved to build queue today. OAuth live.
[BUILD  ] [8] eBay Image Listing App                — Moved to build queue today. OAuth live.
[PENDING] [8] AI Services Client Website            — BUILD. High revenue potential.
[PENDING] [8] Traitor Protocol Adversarial Testing  — BUILD. Studio security utility.
[PENDING] [8] War Room Decision Protocol            — PITCH.
[PENDING] [8] Ghost Book Script Vault               — BUILD. Connects to ghost-book pipeline.
[PENDING] [7] Historical Twins Division             — BUILD. Tesla/da Vinci track.
[PENDING] [7] Ancient Tech Grading System           — BUILD. Connects to vintage agent.
[PENDING] [7] Creative Review Agent                 — BUILD. Studio utility.

======================================================================
SECTION 9: RESOLVED / KNOWN ISSUES
======================================================================

[RESOLVED] Intel Feed vs AI Intel Agent:
  intel-feed.md = stress intelligence (deprecations, vulns, API changes) → stress-intel.md
  ai-intel-agent.md = daily AI landscape (models/tiers/pricing/routing) → ai-intel-daily.json
  DISTINCT. Both needed. Keep both.

[RESOLVED] DailyBriefing vs AgentSupervisorBriefing:
  DailyBriefing = orchestrator.md → what to work on today → orchestrator-briefing.json
  AgentSupervisorBriefing = supervisor.md → dispatch engine → efficiency-ledger
  DISTINCT. Both run 8 AM. Recommend stagger: orchestrator 8:00, supervisor 8:15.

[RESOLVED] mobile-inbox retired. sidebar-agent.html v2.1 is active. Zero mobile-inbox refs.

[RESOLVED] sidebar_http.py = old attempt. Zero refs anywhere. Archive to _archive/.

[RESOLVED] session_bridge.py typo — file is session-bridge.py at root. Found and OK.

[RESOLVED] Agency scripts path — all in agency/ subfolder where expected.

[NEEDS_FIX] GhostBookRescan + OvernightGhostBookPass3:
  Both point to ghost-book/pass1_find_candidates.py (old pipeline).
  New ghost book pipeline built in Opera session today. Verify location then update bat.

[NEEDS_FIX] VedicScan/VedicSync tasks: Vedic Math closed/deferred. Disable these tasks.

[PENDING] Stagger DailyBriefing/SupervisorBriefing by 15 min.
[PENDING] Sidebar Agent Inbox tab verification (end-to-end notification test).
[PENDING] Zanat integration session.
[PENDING] AI rankings buzz detection redesign.
[PENDING] Ghost book scoring rubric recalibration (avg 2.98, too harsh).
