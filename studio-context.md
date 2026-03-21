# STUDIO SYSTEM CONTEXT
Generated: 2026-03-21 | Auto-built from state files, standing-rules.json, MASTER-LIST.md, orchestrator-briefing.json, whiteboard.json

---

## WHO IS JOE

Joe is a solo developer, active eBay reseller (~572 listings), and job seeker targeting remote Trust & Safety / Fraud Analyst roles. He runs an autonomous AI-assisted project studio from a Windows machine using Claude Code CLI, Google Drive, and a mix of free-tier AI APIs. He works in sessions (1-3 hours) and relies on persistent state files and an orchestration layer to pick up exactly where he left off.

**Background:** eBay seller for years, deep knowledge of resale markets and auction platforms (HiBid, Whatnot). Applying to Whatnot for Fraud Agent / Trust & Safety / CX Overnight roles. Has a character AI project (CTW) used for behavior validation. Building a job scraper to replace income.

**Work style:** Prefers concise responses. No filler. Approve a plan before executing. Session-oriented — context is preserved in CONTEXT.md per project. Uses Claude Code CLI not Claude.ai.

**Financial context:** Income replacement is the #1 priority. LLC formation ($300 Tennessee filing fee) is blocking the highest-upside project (Sentinel). Daily eBay revenue is the current income floor.

---

## ARCHITECTURE

```
Claude Code (Tier 2 — premium quota)
  └── Used for: architecture, strategy, multi-file changes, quality review

Gemini Flash free tier (Tier 1 — cheap)
  └── Used for: long doc analysis, scoring, summarization, data synthesis

Ollama local (Tier 0 — free)
  └── Model: gemma3:4b
  └── Used for: overnight batches, reformatting, extraction, translation

Supabase (storage/sync)
  └── Tables: session_status, mobile_answers
  └── Used for: status sync, art requests, task queue, sidebar logs

GitHub Pages
  └── Repo: joepalek/studio (master branch)
  └── Hosts: studio.html, sidebar-agent.html, status.json, studio-context.md

Google Drive
  └── G:/My Drive/Projects/_studio/  — all agent files, status, logs
  └── Each project lives in G:/My Drive/Projects/{project}/
```

**Key files:**
- `status.json` — live session state (v-incremented each update)
- `claude-status.txt` — append-only Drive status log, written by session_logger.py
- `task-queue.json` — tasks queued for Claude Code during quota downtime
- `mobile-inbox.json` — 45 studio inbox items needing decisions
- `standing-rules.json` — 11 pre-approved auto-resolve rules
- `whiteboard.json` — scored product/business ideas (30 items, Gemini-scored)
- `orchestrator-briefing.json` — daily AI-generated briefing

---

## PROJECTS

### 🔴 ACTIVE — HIGH PRIORITY

**job-match** (55% complete)
- What: AI-powered job matching platform. Two sides: job seekers get a narrative interview → behavioral profile → ranked job matches. Employers browse candidates with AI alignment scoring. Scraping engine: monthly broad discovery + daily delta fetch with dead-link validation.
- Status: Company registry pass1 just fixed (EDGAR EFTS + SBIR API sources). Needs daily scraper built.
- Next: Run fixed pass1 to populate company registry, then build daily job scraper
- Blockers: OpenCorporates needs free API key (opencorporates.com/api_accounts/new), IRS EO BMF URL may have moved
- Pending decisions: 5 (Replit migration confirmed?, scraper architecture, etc.)
- Priority: #1 — income replacement target

**CTW — Character Test Workbench** (40% complete)
- What: Single-file HTML app for testing/calibrating AI character profiles. Dev tool, not a product. Characters built by a "talent agency" pipeline load here for behavioral validation before deployment to Sentinel.
- Status: Phase 2 complete (stress test battery, wellbeing bars, character library, provider dropdown). Céleste character validated.
- Next: Generate real portrait images (Perchance), then Phase 3 day structure + time engine
- Blockers: Portrait images not generated (SVG placeholders in use), trait activation detector needs calibration, comfort bar overcorrects downward under pressure

**whatnot-apps** (50% complete)
- What: Job application materials for Whatnot remote roles: Fraud Agent, Trust & Safety Agent, CX Agent Overnight.
- Target: Whatnot hiring manager reviewing 50+ apps, skims in 30 seconds. Wants: platform knowledge, trust/safety instincts, resale market credibility.
- Status: Active, 1 pending decision

**ghost-book** (pass3 complete)
- What: AI-assisted book publishing pipeline. Finds public domain + AI-authored book opportunities.
- Status: Pass3 complete — 3 concat opportunities identified: (1) Vedic Math + CS → "The Algorithmic Legacy", (2) Hemp Fiber → engineering reference, (3) Microbiome + Gut-Brain Axis → clinical reference. 161 viable candidates from pass2 still to review.
- Next: Review 3 concat opportunities, assign Art Dept cover concepts (already queued)

### 🟡 ACTIVE — LOWER PRIORITY

**squeeze-empire** (85% complete)
- What: Single-file browser lemonade stand business simulation with multi-system economics, mini-games, seasonal progression. Casual idle/incremental game.
- Status: Near-complete. 1 pending decision.

**acuscan-ar** (20% complete)
- What: Web-based AR wellness guide overlaying acupressure point markers on live hand/wrist camera feed. Phone-based, 2-minute UX for desk pain relief.
- Status: Early stage. 1 pending decision.

**listing-optimizer** (0% — new)
- What: Bulk eBay listing optimization engine. Ingests raw inventory CSV → generates keyword-dense titles, fills missing fields → outputs eBay File Exchange ready CSV.
- Target: Joe with 572 active listings. Drop CSV in, get better CSV out.
- Status: Not started. 2 pending decisions.

**arbitrage-pulse** (0% — new)
- What: Automated monitor scraping Facebook Marketplace for mispriced items, cross-references eBay sold listings for margin analysis, delivers daily digest of top flip opportunities.
- Status: Not started. 2 pending decisions.

### 🔵 PAUSED

**hibid-analyzer** (60% complete)
- What: Browser tool analyzing auction lot images via Gemini API, estimates resale value, saves notes to HiBid watchlist.
- Status: Paused. 1 pending decision.

**nutrimind** (75% complete)
- What: React-based AI meal planning app — multi-week plans, budget tiers, meal approval workflows, ingredient overlap detection.
- Status: Paused. 1 pending decision.

### 🔒 BLOCKED — LLC REQUIRED

**sentinel-core / sentinel-performer / sentinel-viewer**
- What: Three-app system. Core = behavior engine + character AI backend. Performer = character delivery API. Viewer = end-user interface.
- Blocked: Tennessee LLC formation required ($300 filing fee). Highest-upside project in the portfolio.
- Status: CONTEXT.md + state stubs exist. No code started.

### 🌱 INITIALIZED

**sysguard** — system monitoring agent (stub)
**watchdog** — event/alert watchdog (stub)

---

## AGENT SYSTEM

| Agent | File | Status | Purpose |
|---|---|---|---|
| SRE Scout | sre-scout.md | Built | Session-start health check: tool versions, API pings, project state audit, file integrity, mobile answers |
| AI Gateway | ai-gateway.md | Built | Routes tasks to cheapest model. Tier 0=Ollama, Tier 1=Gemini/OpenRouter, Tier 2=Claude |
| Supervisor | supervisor.md | Built | Autonomous dispatch, greenlight engine, quota-aware mode, daily summary to sidebar |
| Auto-Answer | auto-answer.md | Built | Triages 45 inbox items to <10 using standing-rules + answers-memory + state recommendations |
| Janitor | janitor.md | Built | Cleans stale state, flags drift, generates inbox stubs for paused projects |
| Stress Tester | stress-tester.md | Built | 5 modes of adversarial testing for agents and outputs |
| Intel Feed | intel-feed.md | Built | Weekly web vuln/deprecation scan |
| Inbox Manager | inbox-manager.md | Built | Syncs mobile-inbox.json, applies answers, deduplicates |
| Orchestrator | orchestrator.md | Built | Cross-project planning, generates daily briefing via Gemini |
| Workflow Intelligence | workflow-intelligence.md | Built | Standing rules engine, answer memory |
| Sidebar Agent | sidebar-agent.html | Built | Opera sidebar — status, Gemini chat, task queue |

**Not yet built (highest priority):** Market Scout (eBay comps), daily job scraper, eBay agent

---

## STANDING RULES (pre-approved, auto-apply)

1. **rule-001** — Scraper 403 ×3: mark source Tier 3, add to supervisor-inbox, skip and continue
2. **rule-002** — Scraper 429: exponential backoff 10s/20s/40s, then Tier 3
3. **rule-003** — Scoring task <500 tokens: always route to Gemini Flash, never Claude
4. **rule-004** — Session end: commit all dirty projects, update changelogs, update status.json
5. **rule-005** — Same error in 2+ agents: build shared utility in _studio/utilities/
6. **rule-006** — Overnight batch: Ollama only, no exceptions
7. **rule-007** — Career page is JS-rendered shell: classify Tier 2 (Playwright), add to scraper-config-tier2.json
8. **rule-008** — CDX query returns 0 for Lever/Greenhouse/Ashby: skip CDX, use direct HTTP
9. **rule-009** — Mobile inbox >10 items: auto-expire items pending >7 days
10. **rule-010** — Agent prints user-sourced text: always wrap in safe_str() from unicode_safe.py
11. **rule-011** — Any JSON file open on Windows: always use safe_json_load() or open with encoding='utf-8' — never plain open()

---

## CURRENT PRIORITIES (as of 2026-03-21)

1. **Fix company registry sources + rerun pass1** — EDGAR/IRS/SBIR were all broken, now fixed
2. **Build daily job scraper** — core of the income-replacement plan
3. **Review ghost-book 3 concat opportunities** — covers queued, needs Joe review
4. **CTW portrait images** — unblock Phase 3 via Perchance generation
5. **Review CDX C2C analysis** — 18 entries in cdx-c2c-analysis.json
6. **Run scheduler as Administrator** — register_tasks.py needs elevated terminal
7. **OpenCorporates API key** — opencorporates.com/api_accounts/new (free)

**Blockers:**
- Sentinel blocked until $300 Tennessee LLC fee paid
- OpenCorporates needs free API key signup
- Scheduler needs Administrator terminal

---

## WHITEBOARD TOP 10 (Gemini-scored product ideas)

| Score | Action | Title | Effort | Revenue |
|---|---|---|---|---|
| 8/10 | PUBLISH | Horror games curator guide (1000+ games reviewed) | months | NICHE |
| 8/10 | RESEARCH | DuPont Corfam revival opportunity | months | LARGE |
| 8/10 | BUILD | SoBe Elixir drink line brand revival | months | SMALL |
| 7/10 | BUILD | Wing Commander IV 30th anniversary retrospective | weeks | NICHE |
| 7/10 | RESEARCH | Dymaxion Car design revival | months | MEDIUM |
| 7/10 | PITCH | DeLorean DMC-12 modern revival | months | NICHE |
| 7/10 | BUILD | 90s Green Day chaos era retrospective | months | NICHE |
| 7/10 | PUBLISH | "Remember when you didn't have to give personal info online" | months | NICHE |
| 7/10 | PUBLISH | When actors looked like everyday people | months | NICHE |
| 7/10 | PITCH | Summer sleepover trampoline nostalgia | weeks | SMALL |

---

## KEY DECISIONS ALREADY MADE

- **No Claude for batch/overnight work** — Ollama only (rule-006)
- **No Claude for scoring tasks** — Gemini Flash (rule-003)
- **Single-file solutions preferred** when possible (studio aesthetic)
- **Windows + Google Drive** is the dev environment — always handle cp1252 encoding (rule-011)
- **Supabase anon key is public** — already in art-request-form.html and sidebar-agent.html, safe to embed
- **GitHub Pages = joepalek.github.io/studio** — status.json, studio-context.md, sidebar-agent.html all hosted there
- **Sentinel deferred** until LLC is funded — do not suggest Sentinel work
- **Job Match is #1** — every session should make progress on income replacement
- **CONTEXT.md per project** — always read it at session start, update at session end
