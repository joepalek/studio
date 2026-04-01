# STUDIO SYSTEM — MASTER AGENT & TOOL LIST
Last updated: 2026-04-01

Legend:
  [RUNNING]  = live, executing on schedule, producing output
  [BUILT]    = script exists and works, not yet scheduled
  [UPDATE]   = running but needs spec change per latest vision
  [BUILD]    = needs to be built
  [PARKED]   = exists, deliberately paused
  [DISABLED] = task exists, turned off, ready to re-enable
  [DELETE]   = remove from system

Priority:
  P0 = this session — blocking or high daily impact
  P1 = this week
  P2 = this month
  P3 = when dependency is met

---

## NIGHTLY SCHEDULE — CURRENT STATE

| Time  | Task                    | Script                          | Status   | Output |
|-------|-------------------------|---------------------------------|----------|--------|
| 12:30 | VectorReindex           | vector_reindex.py               | RUNNING  | 595 chunks ChromaDB |
| 1:00  | NightlyRollup           | nightly_rollup.py               | RUNNING  | daily-digest.json — YELLOW 57/100 |
| 2:00  | ProductArchaeology      | product_archaeology_run.py      | RUNNING  | 434 results |
| 2:30  | InboxManager            | run_inbox_sync.py               | RUNNING  | 56 items synced |
| 3:00  | JobDelta                | job_daily_harvest.py            | RUNNING  | job board diffs |
| 3:30  | AutoAnswer              | auto_answer_gemini.py           | RUNNING  | Gemini triage, 8 auto-resolved |
| 4:00  | WhiteboardScore         | whiteboard_score.py             | RUNNING  | 46/46 scored |
| 5:00  | AIIntel                 | ai_intel_run.py                 | RUNNING  | 3 HIGH / 194 logged |
| 5:30  | AgencyCharacterBuild    | agency/character_batch_builder.py| RUNNING | schema only — no real chars yet |
| 5:30  | AIServicesRankings      | ai_services_rankings.py         | RUNNING  | rankings + routing guide |
| 6:00  | SidebarInject           | rebuild_sidebar.py              | RUNNING  | sidebar rebuilt daily |
| 6:30  | CheckDrift              | check-drift.py                  | RUNNING  | 0/12 drift |
| 7:00  | Janitor                 | janitor_run.py                  | RUNNING  | cleanup, weekly deep review TBD |
| 8:00  | DailyBriefing           | orchestrator-briefing.bat       | RUNNING  | Claude briefing + plan populated |
| 11:00 | GitCommitNightly        | git_commit.py                   | RUNNING  | Gemini commit msgs |
| 23:30 | MonthlyJobDiscovery     | job_source_discovery_monthly.py | RUNNING  | monthly source crawl |
| /30m  | SupervisorCheck         | supervisor_check.py             | RUNNING  | dispatches 3 tasks, work_queue=7 |

---

## AGENT UPDATES — BY NUMBER (from April 1 review)

---

### 1 — NIGHTLY ROLLUP + HEALTH SCORING
**Current:** YELLOW 57/100 — score is misleading because EXPECTED_AGENTS list
references old Claude-based agent names (stress-tester, janitor, git-scout, sre-scout)
that no longer check in under those names.

**Updates needed:**
- [ ] Fix EXPECTED_AGENTS in nightly_rollup.py to match actual running agents
- [ ] Score agents by AI service quality: query ai-services-rankings.json,
      check each agent's last model used vs current best-rated model for its task type
- [ ] Wire ALL agents to write heartbeat entries on run completion
- [ ] Add system check: scan scheduler/logs/ to detect any agent that ran but
      has no corresponding heartbeat — flag as "unregistered agent"
- [ ] Health score formula update: weight by agent importance, not just count

**Status:** UPDATE — P0

---

### 2 — OVERNIGHT AUTO ANSWER
**Current:** Gemini auto-resolves rules-based items. Working well.
**Updates needed:** None beyond #1 heartbeat wiring.
**Status:** RUNNING ✅

---

### 3 — JOB ACQUISITION STRUCTURE
**Current:** job_daily_harvest.py crawls registered boards, diffs listings.
MonthlyJobDiscovery adds new sources. Job-match project has 5 unanswered architecture
decisions blocking all agent work.

**Updates needed:**
- [ ] Review job-match state.json — answer the 5 pending decisions
- [ ] Check current capture rate: how many new listings per day, what boards
- [ ] Expand scope: identify gaps in current source registry
- [ ] Consider: Whatnot-specific job feeds, remote-first boards, creator economy jobs
- [ ] Check if LinkedIn, Indeed, remote.co, wellfound are in registry

**Status:** REVIEW SESSION NEEDED — P0 (Blackdot ends May 2026)

---

### 4 — PRODUCT ARCHAEOLOGY
**Current:** 434 results from KilledByGoogle, Reddit discontinued subs, Wayback.
Gemini scoring fails at 2AM (404). Top items not moving to whiteboard automatically.

**Updates needed:**
- [ ] Shift Gemini scoring to 9AM (after Gemini wakes up) — separate scoring pass
- [ ] Auto-promote: items scored 7+ by Gemini → push to whiteboard.json automatically
      (currently whiteboard_score.py scores whiteboard items; product_arch should FEED it)
- [ ] Expand sources: Product Hunt graveyard, AngelList dead startups, Patent DB
      abandoned patents, App Store removed apps, Steam delisted games
- [ ] On Gemini 404/503: immediately query supervisor for best available free alt
      (Ollama Gemma, if available) — fallback chain, not just silent fail
- [ ] Use connectors/utilities: Tavily MCP available — use for live validation
      of market voids against current landscape
- [ ] Results review: need to know what categories are dominating the 434 results

**Status:** UPDATE — P1

---

### 5 — VINTAGE AGENT / DECADE TRAINING DATA
**Current:** 10 decade profiles built (1920s-2010s). 34 sleepers. 0 hot items, 0 gaps
(Gemini not populating those arrays properly).

**Updates needed:**
- [ ] Fix Gemini prompt to force-populate ebay_hot_now, failed_products, modern_gap arrays
- [ ] MAJOR SCOPE EXPANSION: This is character memory training data, not just eBay intel.
      Add to each decade profile:
      - lexicon_and_slang: common phrases, regional variants, rural vs urban splits
      - news_events: major events by year within decade, how they shaped thinking
      - age_cohort_reasoning: how a 20yr old vs 60yr old in this decade thought differently
      - ethnic_regional_variants: urban/rural/ethnic community differences in all above
      - memory_formation_model: how memories form at different life stages
        (early childhood = haze/fragments, teen/young adult = sharp, middle age = selective,
        elderly = declining recall with distraction patterns — NOTE: test carefully,
        getting distracted in conversation risks being annoying for users trying to get info)
- [ ] CHARACTER MEMORY WIRING: When building Agency character born in 1950,
      system should pull: 1950s (birth/infancy), 1960s (childhood), 1970s (teen),
      1980s (young adult), 1990s (adult), 2000s (middle age), 2010s (late career/senior)
      and weight memory sharpness by decade position in their life arc
- [ ] BACKWARDS EXTENSION: Add 1900s, 1910s for historical figures. Going forward,
      update 2010s and begin 2020s profile.
- [ ] Feed this data into Agency character builder as memory_profile field

**Status:** UPDATE — P1 (blocks Agency quality)

---

### 6 — AI INTEL
**Current:** 3 HIGH / 71 WORTH / 194 LOGGED / 13 YouTube. Generated field null in JSON.

**Updates needed:**
- [ ] Fix generated field null bug in ai_intel_run.py
- [ ] PANEL OF CHARACTERS: Assign 3-5 Agency characters as the "AI Intel Panel"
      Each has a different angle (tech critic, builder, business analyst, skeptic, hype detector)
      Panel reads all scraped news and produces:
      - Actionable ideas: "we could do X with this"
      - System update suggestions: "our Y agent should now use Z"
      - Whiteboard candidates: auto-submit anything scored 7+ by panel
      - No length limit — some days a paragraph, some days a book
- [ ] Panel output goes to: daily-digest.json + sidebar AI Intel card + whiteboard queue
- [ ] Keyword/scope panel: characters also analyze scrape keywords,
      suggest expanding or narrowing search terms based on what's producing signal
- [ ] Send to whiteboard: panel explicitly votes on whiteboard submission per item

**Status:** UPDATE — P1

---

### 7 — AGENCY CHARACTER BUILD
**Current:** Running nightly but only has schema + sample spec. No real characters built.
Tesla and da Vinci were P0 — not built. CX Agent quota not set.

**Updates needed:**
- [ ] BUILD Tesla and da Vinci immediately — these are P0, block Gaussian Splat deployment
- [ ] Increase generation rate: make character building fully agentic
      - Set daily quota: X characters per day based on available Gemini free tier calls
      - Pull from whiteboard top-rated character concepts automatically
      - Historical figures: pull from product archaeology + whiteboard
      - Each character auto-gets: memory_profile (from decade data), voice, image gen request
- [ ] CX AGENT QUOTA: CX Agent knows all active projects, sets daily quota for:
      - Character images (match to how many chars produced that day)
      - Character model renders
      - Video clips
      - Quota tied to free gen capacity in image/video art dept
- [ ] COORDINATOR ROLE — new agent needed: "Studio Coordinator" / Casting Director
      - Reads all active projects, characters, scripts
      - Casts characters to scripts
      - Requests projects to be assembled (asks Joe for approval first)
      - Once approved: spins up character image gen, sends group for approval
        with scripts and video vision
      - Handles: bands (name + art + images + music gen requests),
        football players, historical figures, any actionable Agency asset
- [ ] DAILY BRAINSTORM: casting + social media + art dept + legal + supervisor
      run a daily session, output = action plan
      Goal: art dept free gen capacity used fully every day
- [ ] Characters get: memory_profile, voice_profile, image_prompt, decade_weights

**Status:** BUILD — P0 (Tesla/da Vinci), P1 (coordinator + quota system)

---

### 8 — AI SERVICES RANKINGS (sidebar display)
**Current:** Rankings updating nightly. Sidebar doesn't show service metrics.

**Updates needed:**
- [ ] Add metrics display to sidebar SERVICES/DATA tab:
      - Per service: daily limit, images/day, videos/day, requests/min
      - Example: "Ideogram: 50 images/day free" "Runway: 5 videos/day"
      - Show current usage vs quota where trackable
      - Color code: green (plenty left), amber (50%+ used), red (near limit)
- [ ] Wire to CX Agent quota system (#7 above)

**Status:** UPDATE — P1

---

### 9 — SIDEBAR INJECT
**Current:** Rebuilds sidebar daily with fresh data. Working well.
Same feedback as #8 — metrics display needed.
**Status:** RUNNING ✅ — metrics panel to be added with #8

---

### 10 — DAILY BRIEFING / ORCHESTRATOR
**Current:** Claude produces briefing, populate_orchestrator_plan.py builds task plan.
**Status:** RUNNING ✅

---

### 11 — SUPERVISOR CHECK
**Current:** Checks Ollama + Gemini only. Dispatches from plan. Working.

**Updates needed:**
- [ ] EXPAND PROVIDER AWARENESS: Don't just check Ollama + Gemini.
      Query ai-services-rankings.json for ALL available free-tier providers.
      Build live availability map at each run cycle.
- [ ] AGENT ACTIVITY PROJECTION: At each cycle, read all scheduled tasks + their
      estimated run times, build projected activity chart for upcoming 24h
      Output to supervisor-report.json as "projected_activity" array
- [ ] AGENT UPDATE SUGGESTIONS: For each agent that ran since last cycle,
      check: model used vs best available, output quality metrics, service 404/503 count.
      Flag any agent using a degraded service → suggest switching.
      Flag any agent whose last 3 runs produced 0 results → escalate to inbox.
- [ ] ASSET UPDATE SUGGESTIONS: Flag assets (characters, rankings, profiles)
      not updated in 7+ days → queue for refresh
- [ ] AI INTEL CROSS-REFERENCE: Read latest ai-intel summary → flag any
      newly deprecated models our agents are using → immediate update suggestion
- [ ] Note: AIIntel does similar discovery — supervisor should consume intel
      output rather than duplicate scraping

**Status:** UPDATE — P1

---

### 12 — VECTOR REINDEX
**Current:** Rebuilds ChromaDB from studio files nightly. 595 chunks.

**What it is / why:** ChromaDB is the vector memory store. Every file in the studio
gets chunked and embedded so agents can do semantic search — "what decisions were made
about job-match?" pulls relevant context from all files. session-startup.py uses this
to give agents a relevant context window without loading everything.
595 chunks = all project state files, agent .md files, decision logs, CLAUDE.md files.

**Status:** RUNNING ✅

---

### 13 — CHECK DRIFT
**Current:** Scans 12 project state.json files for 14+ day staleness. 0/12 HIGH.
**Status:** RUNNING ✅

---

### 14 — JANITOR
**Current:** Daily cleanup. Truncates logs, removes pycache, flags orphaned bats.

**Updates needed:**
- [ ] WEEKLY DEEP REVIEW: Once per week (Sundays), Janitor reads all agent logs
      from the past 7 days and produces:
      - Workflow flaw report: steps that consistently fail, retry patterns
      - Efficiency suggestions: "agent X takes 45min but produces 3 results — consider reducing scope"
      - Utility candidates: "this same pattern appears in 3 agents — extract to utility"
      - Suggested bat/task updates
      Output to janitor-report.json with date + weekly flag

**Status:** UPDATE — P2

---

### 15 — AI INTEL (expanded — see also #6)
**Current:** Scrapes YouTube, Reddit, HN, Anthropic, OpenAI, GitHub, arXiv.
**See #6 for full update spec.**
**Status:** UPDATE — P1

---

### 16 — GIT COMMIT NIGHTLY
**Current:** Gemini generates commit messages. Commits all dirty repos. Working.

**Updates needed:**
- [ ] Check Supervisor for best available model at commit time (not hardcoded Gemini)
- [ ] Scan GitHub Trending for top 20 repos relevant to studio activity
      (based on agent types, scrape keywords, active project tech stacks)
      → push matches to whiteboard as BUILD/RESEARCH candidates
- [ ] Cross-reference trending repos against: current utilities, agent gaps,
      scraper tools, data connectors we don't have yet

**Status:** UPDATE — P2

---

### 17 — MONTHLY JOB DISCOVERY
**Current:** Monthly source crawl running. Need to verify capture quality.

**Updates needed:**
- [ ] Check and report: how many sources in registry, how many validated,
      what categories are covered vs missing
- [ ] Review for Whatnot-specific sources, creator economy job boards

**Status:** REVIEW — P1 (see #3)

---

## DISABLED — INTENTIONAL

| Task | Reason | Re-enable when |
|---|---|---|
| WhiteboardAgent | Waiting on Agency chars | Agency has 5+ real characters |
| SkillImprover | Waiting on Agency chars | Agency has 5+ real characters |
| PeerReview | Waiting on Agency chars | Agency has 5+ real characters |
| GitScout | Parked — Claude-dependent | Rewrite as Python if needed |
| HeartbeatCheck | Redundant — rollup+supervisor write heartbeats | Never re-enable |
| WorkflowIntelligence | Parked | Rewrite as Python if needed |
| IntelFeed | Stress tester inactive | When stress testing resumes |
| VedicScan | NFL data not ready | When sports arbitrage activates |
| MirofishTest | Manual use only | N/A — run manually |
| SupervisorBriefing | Replaced by supervisor_check.py | Never |
| SidebarBridge | Runs manually | Fix auto-start task |

---

## DELETE — CLEAN THESE OUT

| Task / File | Action |
|---|---|
| GhostBookRescan | DELETE task — old pipeline dead Mar 22 |
| OvernightGhostBookPass3 | DELETE task — old pipeline |
| WhiteboardScorer (AgentWhiteboardScorer.xml) | DELETE — duplicate, bat version is correct |
| CommonCrawlTrigger | REVIEW — why was C2C analysis stopped? Clarify before deleting |

---

## C2C ANALYSIS — OPEN QUESTION
CommonCrawlTrigger is parked. C2C (Common Crawl) analysis was running
(cdx-c2c-results.json has data). Reason for pause unclear.
ACTION: Clarify intent — is this still needed? What was it feeding?

---

## NEW BUILDS — FROM APRIL 1 REVIEW

### COORDINATOR AGENT (Casting Director) — BUILD P0
- Reads all active projects, characters in progress, scripts
- Casts characters to scripts, requests project assembly
- Asks Joe for approval before any production starts
- On approval: queues character image gen, sends group for review
  with script + video vision document
- Handles: bands, football rosters, historical figures, any Agency asset
- Daily brainstorm trigger: pulls casting + social + art + legal + supervisor
- Output: action_plan.json written to studio inbox

### CX AGENT QUOTA SYSTEM — BUILD P1
- CX Agent knows all projects and their daily character/asset output
- Sets daily quota per service (images, video, voice)
- Ties quota to free gen capacity from ai-services-rankings.json
- Reports quota usage to supervisor + sidebar

### SCRAPE MANAGER — REVIEW SESSION NEEDED
After this list is reviewed: audit all scrapes, searches, crawls
across the entire studio — map what exists, where data goes,
whether it's being reviewed, and what's missing.
Goal: a Scrape Manager view in the sidebar.

---

## KNOWN ISSUES — PRIORITY ORDER

| # | Issue | Impact | Owner | Priority |
|---|-------|--------|-------|----------|
| 1 | NightlyRollup EXPECTED_AGENTS outdated | False RED/YELLOW score | nightly_rollup.py | P0 |
| 2 | Vintage Agent eBay arrays empty | Missing intel | vintage_agent.py | P1 |
| 3 | Agency has no real characters | Blocks 3 downstream agents | agency session | P0 |
| 4 | ProductArch Gemini scoring at 2AM = 0 items | No scores | product_archaeology_run.py | P1 |
| 5 | Janitor orphaned bat report noise | Report clutter | janitor_run.py | P2 |
| 6 | SidebarBridge no auto-start | Manual restart needed | task scheduler | P2 |
| 7 | AI Intel generated field null | Sidebar date missing | ai_intel_run.py | P1 |
| 8 | Supervisor only checks Ollama+Gemini | Missing free providers | supervisor_check.py | P1 |
| 9 | Job-match 5 pending decisions | All job agent work blocked | session | P0 |
| 10 | Coordinator agent not built | Agency has no director | new build | P0 |
