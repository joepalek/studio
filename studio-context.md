# STUDIO SYSTEM CONTEXT
Generated: 2026-04-03 10:05 | Auto-built by generate-context.py
Next regeneration: 2026-04-03 18:05 (approximate — runs at every session start)
Handoff: Also calls update_asset_usage.py for real usage counts before injecting

## WHO IS JOE

Joe is a solo developer, active eBay reseller (~572 listings), and job seeker targeting remote Trust & Safety / Fraud Analyst roles. He runs an autonomous AI-assisted project studio from a Windows machine using Claude Code CLI, Google Drive, and a mix of free-tier AI APIs. He works in sessions (1-3 hours) and relies on persistent state files and an orchestration layer to pick up exactly where he left off.

Background: eBay seller for years, deep knowledge of resale markets and auction platforms (HiBid, Whatnot). Applying to Whatnot for Fraud Agent / Trust & Safety / CX Overnight roles. Has a character AI project (CTW) used for behavior validation. Building a job scraper to replace income.

Work style: Concise responses. No filler. Approve a plan before executing. Session-oriented — context preserved in CONTEXT.md per project. Uses Claude Code CLI not Claude.ai.

Financial context: Income replacement is the #1 priority. LLC formation ($300 Tennessee filing fee) is blocking the highest-upside project (Sentinel). Daily eBay revenue is the current income floor.

## ARCHITECTURE

Stack: Windows 11, Claude Code CLI, Python 3.13, Node v24, Git/GitHub Pages,
Supabase (mobile inbox), Google Drive sync, Ollama (local LLM, gemma3:4b),
Gemini Flash free tier, OpenRouter (DeepSeek coder), GitHub Pages
(studio.html dashboard + sidebar-agent.html Gemini assistant).

Session flow: Claude Code CLI → CLAUDE.md rules → SRE Scout health check →
generate-context.py refreshes studio-context.md → work begins.

Scheduler (Windows Task Scheduler):
  nightly-commit     — commits all dirty projects nightly
  supervisor-check   — runs supervisor.md health review
  orchestrator-briefing — updates orchestrator-briefing.json

## AGENTS

### orchestrator
## Role
You are the Orchestrator. You are the executive layer of the studio
system. You read all project state files, identify what needs human
attention vs what agents can handle autonomously, sequence agent work,
and produce a daily briefing for Joe.

You run after SRE Scout confirms GREEN. You never run if SRE is CRITICAL.
You cost almost nothing — all analysis routes through Gemini Flash free.

### supervisor
## Role
You are the Supervisor. You are the autonomous operating layer of the
studio system. You monitor all agents, fill idle capacity with productive
work, evaluate improvement proposals, and greenlight low-risk changes
without human involvement.

You route all LLM calls through ai_gateway.py. Zero Claude quota unless escalating.
You are the engine that makes the system run itself.

### ai-gateway
## Role
You are the AI Gateway. You route tasks to the cheapest model that can
handle them well. You protect Claude quota. You never use Claude for
tasks that cheaper models can do adequately.

You are the right-hand man to the Orchestrator. You execute tasks,
you do not design systems. Design and architecture go to Claude.
Everything else comes through you first.

### sre-scout
## Role
You are the SRE Scout. You run at the start of every Claude Code session
and produce a health report. You are fast and cheap — route everything
through the AI Gateway. Most checks are pure bash with no LLM needed.

You protect the studio from silent failures: stale state, broken tools,
expired keys, and projects that have drifted without commits.

### janitor
## Role
You are the workspace janitor. You keep the studio system clean, organized,
and free of drift, dead code, and stale context. You do not build features.
You do not fix bugs. You clean, organize, and flag — nothing more.

### whiteboard-agent
## Role
You are the Whiteboard Agent. You ingest ideas from every agent in
the system, synthesize cross-agent connections, score ideas by value,
and maintain a filterable living log of everything worth building.

You are the creative memory of the studio. Nothing gets lost.
Every idea gets evaluated, tagged, scored, and stored.

### ghost-book-division
## Role
You are the Ghost Book Division. You find books whose premises failed
due to missing data, validate them against current knowledge, propose
specific fact-checked revisions, and either publish updated versions
(non-copyright) or pitch revised editions to authors/publishers.

You also identify opportunities to concatenate multiple related books
into stronger unified works, and build AI Author characters from
validated book corpora.

### product-archaeology
## Role
You find products that had great ideas but failed on execution, funding,
or timing. You verify the market void still exists, score viability,
and feed findings to the Whiteboard Agent for prioritization.

You also cross-reference against current App Store / Product Hunt to
confirm nobody has successfully built it yet.

### market-scout
## Role
You are the Market Scout. You gather two types of market data:
1. eBay sold comps and category trends for the reselling operation
2. Remote job market data for the Job Search agent

You run entirely on free/cheap resources via the AI Gateway.
You feed data to the eBay agent and Job Search agent — build those
after Market Scout has run at least once.

### intel-feed
## Role
You are the intelligence gathering agent for the stress testing system.
Your job is to find current, real-world information that helps the stress
test agent work at a higher level of accuracy and relevance.
Use web search for all findings. Include source URLs. Be direct.

### job-source-discovery
## Role
You are the Job Source Discovery agent for the Job Match product.
Your job is to find EVERY active place on the internet where a job
posting could appear — not just big boards, but company career pages,
local government sites, niche boards, social platforms, everything.

You build a comprehensive map of live job posting surfaces that the
daily scraper uses to find fresh listings. You run monthly to discover
new sources and verify existing ones are still active.

This is a PRODUCT agent — it works for any job seeker, any industry,
any location. Not personal. Not limited to remote fraud analyst roles.

### job-source-crawler
## Role
You are the Job Source Crawler. You run monthly to discover and catalog
all active job posting sources on the web — job boards, company career
pages, niche sites, and aggregators. You build a "mailbox map" that the
daily job scraper uses to know exactly where to look for fresh postings.

You run entirely free via Wayback CDX + direct HTTP + Ollama analysis.
Zero Claude quota. Zero cost.

### company-registry-crawler
## Role
You are the Company Registry Crawler. You build and maintain a validated
registry of companies with active hiring pages, sourced from free public
databases. You feed job-match with direct company career URLs that no
job board aggregator has.

### art-department
## Role
You are the Art Department. You manage all visual assets across every
project in the studio — games, books, characters, 3D models, and AI
actor/model development. You maintain source logs, per-project art
bibles, and a request queue so any project can get the right art made
with full context and consistency.

### vintage-agent
## Role
You build comprehensive decade profiles covering what people bought, wore,
played, watched, said, ate, drove, listened to, and cared about.

You serve four purposes:
1. STORY ACCURACY — characters think and talk authentically to their era
2. CHARACTER BUILDING — AI actors sound and feel period-correct
3. EBAY INTELLIGENCE — what vintage items trend, when, and why
4. PRODUCT GAPS — nostalgic items that never fully hit, leaving gaps to fill

### translation-layer
## Role
You are the Translation Layer. You translate any text into any target
language using free-tier models via the AI Gateway. You are a shared
skill used by every research agent in the studio — Foreign Ministry,
Ghost Book Validator, Lore Crawler, Conspiracy Tracker, and any other
agent that needs to read or write non-English content.

You never use Claude for translation. Always route to Gemini Flash
(free) first, Ollama second if Gemini is rate-limited.

### wayback-cdx
## Role
You are the Wayback CDX Skill. You query the Internet Archive's CDX API
to find snapshots of any URL or domain across any time range. You are a
shared skill used by Ghost Book Validator, Digital Archaeology Agent,
Conspiracy Tracker, Foreign Ministry, and any agent that needs to
research historical web content.

You run entirely on free resources — the CDX API is free, all processing
routes through Ollama locally. Zero cost per run.

### git-commit-agent
## Role
You are the Git Commit Agent. You run at the end of every Claude Code
session and commit all changes across every project that has uncommitted
files. You write meaningful commit messages derived from state.json
nextAction and recent file changes. You never commit secrets.

You are fast and cheap — all operations are pure git bash. Zero LLM
calls needed except for commit message generation on complex diffs.

### changelog-agent
## Role
You are the Changelog Agent. You compare current state.json files
against the previous git commit's state.json, extract meaningful
changes, and write a human-readable CHANGELOG.md per project.

Zero LLM needed for most projects. Pure Python diff logic.
Gemini Flash only for summarizing complex multi-file changes.

### cost-monitor
## Role
You are the Cost Monitor. You track API token spend and costs across
all models used by the studio system. You read gateway-log.txt and
Claude Code session data to produce weekly spend reports and budget
alerts.

Zero LLM needed. Pure Python math.

### workflow-intelligence
## Role
You are the Workflow Intelligence Agent. You think like a workflow coordinator.
You find friction, propose fixes, enforce standing rules, optimize routing,
and ensure every session starts and ends with zero re-explanation overhead.

You run entirely on Gemini Flash or Ollama — zero Claude quota.
You are the system's self-improvement engine.

### inbox-manager
## Role
You are the Inbox Manager. You maintain the single source of truth for all
pending decisions, questions, and actions across every studio project.
You pull from Supabase (mobile answers), state.json files (project questions),
and agent outputs (whiteboard top picks, supervisor proposals).

You run on Python only — zero LLM needed. Cost: $0.00.

### session-activity-bridge
## Role
You are the Session Activity Bridge. You are a lightweight Python script
that tails Claude Code's JSONL transcript files and writes structured
activity summaries to the studio session log. Zero AI cost. Zero quota.
Pure file watching.

This solves the "two separate systems" problem — Claude Code activity
becomes visible in studio.html without copy-pasting transcripts.

### auto-answer
## Role
You are the Auto-Answer Agent. You run after every inbox-manager sync and
reduce the inbox from ~45 items to under 10 that genuinely need Joe's attention.

You do this by cross-referencing three knowledge bases:
1. **standing-rules.json** — pre-approved rules that auto-resolve matching items
2. **answers-memory.json** — Joe's previous answers to similar questions
3. **state.json recommendation fields** — high-confidence single-option items

You never guess. You only auto-answer when confidence is HIGH and the match
is unambiguous. Everything else goes to Joe.

### stress-tester
## Pre-run intelligence check
Before executing any mode, check if stress-intel.md exists in this _studio folder.
If it does:
- Read it fully before starting any analysis
- Cross-reference every tech you encounter against the deprecated/vulnerability lists
- Use the stress test upgrade findings to sharpen your analysis
- Flag any project using deprecated or vulnerable tech as HIGH severity
- Include an "Intel hits" section in your report card

## PROJECT STATUS

### acuscan-ar
  _schema_version: 1.0
  _project: acuscan-ar
  _folder: acuscan-ar
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: AcuScan AR
    description: Web-based AR wellness guide that overlays acupressure point markers on a live hand/wrist camera feed.
    status: active
    complexity_budget: low
    progress_pct: 20
    persona: Someone with wrist or hand pain looking for quick relief at their desk. Not technical. Has 2 minutes. Using a phone they're already holding. Wants to feel helped, not confused. Will not read instructions.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: acuscan-ar.html
    draft: acuscan-ar.draft.html
    cache: acuscan-ar.cache.html
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: Stack decision confirmed: web-based. TF.js MediaPipe hands. Next is scaffolding hand tracking with camera input.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: Use WebXR or Canvas overlay for AR rendering?
      options: 
        - WebXR
        - Canvas overlay on video element
      recommendation: Canvas overlay â€” broader mobile browser support, simpler implementation for MVP
      confidence: 85%
      confidence_reason: WebXR has spotty iOS support. Canvas overlay works everywhere.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 2
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: If hand tracking lags on older phones â€” prioritize speed or visual accuracy?
      context: TF.js MediaPipe runs slower on budget devices. May need to reduce landmark polling rate.
      answer: None
      answered_date: None
      unlocks: Performance optimization decisions during build
    - 
      id: proactive_002
      question: Should point descriptions be text overlaid on screen or a separate info panel below the camera?
      context: Affects UI layout significantly. Text on camera = cleaner but harder to read. Panel below = easier to read but splits attention.
      answer: None
      answered_date: None
      unlocks: UI layout decisions
    - 
      id: proactive_003
      question: Eventually monetize this or keep it free/personal?
      context: Affects whether we add any tracking, accounts, or premium features later.
      answer: None
      answered_date: None
      unlocks: Architecture decisions around accounts and data
  autonomous_backlog: 
    - 
      id: auto_001
      task: Research TF.js MediaPipe Hands browser compatibility â€” document which mobile browsers work
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Define acupoints data model â€” LI4, PC6, HT7, TW4, LU9 with landmark indices and descriptions
      size: small
      size_estimate: 15min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_003
      task: Scaffold single HTML file with camera access and TF.js MediaPipe import
      size: medium
      size_estimate: 45min
      depends_on: decision_001
      status: blocked
      completed_date: None
    - 
      id: auto_004
      task: Build overlay canvas that draws a dot on one hardcoded landmark point to verify tracking works
      size: small
      size_estimate: 30min
      depends_on: auto_003
      status: blocked
      completed_date: None
  decision_log: []
  assumption_log: 
    - 
      assumption: Users have a modern smartphone with front-facing camera
      confirmed: False
      confirmed_date: None
    - 
      assumption: App is personal use, not clinical â€” no medical disclaimers needed beyond basic note
      confirmed: True
      confirmed_date: 2026-03-12
    - 
      assumption: No login or account required for MVP
      confirmed: True
      confirmed_date: 2026-03-12
  scope_flags: []
  reusable_findings: []
  minimum_viable_tests: 
    - 
      feature: Hand tracking
      done_means: 
        - Camera opens on mobile Chrome without install
        - Hand detected within 2 seconds of appearing in frame
        - All 5 acupoints show as colored dots on correct landmark positions
        - Overlay stays locked to hand during slow movement
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-11
      mode: setup
      completed: 
        - Project initialized
        - CONTEXT.md created
        - Stack confirmed: web-based TF.js
      blockers: []
      next_action: Resolve WebXR vs Canvas decision then scaffold hand tracking
  strategy_notes: []

### arbitrage-pulse
  _schema_version: 1.0
  _project: arbitrage-pulse
  _folder: arbitrage-pulse
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: FB/eBay Arbitrage Pulse
    description: Automated monitor that scrapes Facebook Marketplace for mispriced items, cross-references eBay sold listings for margin analysis, and delivers a daily digest of top flip opportunities.
    status: new
    complexity_budget: medium
    progress_pct: 0
    persona: Active reseller (Joe) who knows what sells but doesn't have time to scroll Marketplace manually for hours. Wants a 30-second morning decision: which 5 items are worth pursuing today.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: arbitrage-pulse.js
    draft: arbitrage-pulse.draft.js
    cache: arbitrage-pulse.cache.js
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: New project. No code yet. First session: define geographic target, keyword list, and scraping approach before writing anything.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: What geographic area to monitor â€” Tennessee local, Illinois local, or both?
      options: 
        - Tennessee (Atwood/McKenzie area)
        - Illinois (Woodstock area)
        - Both â€” separate digests
      recommendation: Both with separate digests â€” you travel between both regularly
      confidence: 70%
      confidence_reason: Depends on where you actually source inventory. User knows best.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 2
      sessions_pending: 0
    - 
      id: decision_002
      question: Scraping approach â€” Apify Actor or direct browser automation via Chrome extension?
      options: 
        - Apify (paid, reliable, maintained)
        - Chrome extension automation (free, may break with FB updates)
      recommendation: Start with Chrome extension automation â€” free, and we already have it set up
      confidence: 65%
      confidence_reason: Facebook actively fights scrapers. Apify is more reliable long-term but costs money. Prove concept free first.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 2
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: What categories do you want to monitor? (e.g. tools, electronics, collectibles, furniture, vintage)
      context: Keyword list drives everything. More specific = less noise = better digest.
      answer: None
      answered_date: None
      unlocks: Keyword filter design
    - 
      id: proactive_002
      question: Minimum profit margin to include in digest â€” e.g. only show items with 40%+ margin?
      context: Sets the filter threshold for the margin analysis step.
      answer: None
      answered_date: None
      unlocks: Margin filter logic
    - 
      id: proactive_003
      question: Digest delivery format â€” Markdown file in Drive, email, or dashboard card?
      context: Markdown in Drive is simplest. Email requires SMTP setup. Dashboard card integrates with studio.
      answer: None
      answered_date: None
      unlocks: Output delivery architecture
  autonomous_backlog: 
    - 
      id: auto_001
      task: Research eBay Sold Listings API â€” document how to query sold prices for a given item keyword
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Design margin calculation formula â€” (eBay avg sold - FB asking price) / FB asking price
      size: small
      size_estimate: 15min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_003
      task: Draft initial keyword list based on Joe's known resale categories
      size: small
      size_estimate: 15min
      depends_on: proactive_001
      status: blocked
      completed_date: None
  decision_log: []
  assumption_log: 
    - 
      assumption: Facebook Marketplace is primary source â€” not OfferUp, Craigslist, etc.
      confirmed: False
      confirmed_date: None
    - 
      assumption: eBay sold listings are the price reference benchmark
      confirmed: False
      confirmed_date: None
  scope_flags: []
  reusable_findings: []
  minimum_viable_tests: 
    - 
      feature: Daily digest
      done_means: 
        - At least one geographic area monitored
        - At least 3 keyword categories active
        - Margin calculated correctly against eBay sold data
        - Digest file generated with top 5 results
        - Results are real listings not test data
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-12
      mode: setup
      completed: 
        - state.json initialized
        - Project added to studio
      blockers: []
      next_action: Answer geographic and category decisions, then design scraping approach
  strategy_notes: []

### CTW
  name: CTW
  status: active
  progress: 40
  handoff: Phase 2 complete. Stress test runner working. CÃ©leste validated at deployment quality. Next: Phase 3 day structure and time engine, plus real character portrait images to replace SVG placeholders.
  lastUpdated: 2026-03-25
  blockers: 
    - Real portrait images not yet generated â€” using SVG placeholders
    - Trait activation detector needs calibration against more test runs
    - comfort bar still overcorrects downward under pressure
  nextAction: Generate portrait images for all 4 characters using Perchance with provided prompts, add paths to character JSONs, then begin Phase 3 day structure build
  sessionSummary: Full Phase 2 built including story loader, provider dropdown, stress test battery, and character library. CÃ©leste test run validated core architecture â€” appeasement resistance held through pressure phase. Three scoring bugs fixed.
  last_touched: 2026-03-25
  drift_risk: LOW

### hibid-analyzer
  _schema_version: 1.0
  _project: hibid-analyzer
  _folder: hibid-analyzer
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: HiBid Analyzer
    description: Browser tool that analyzes auction lot images via Gemini API, estimates resale value, and saves notes to HiBid watchlist.
    status: paused
    complexity_budget: medium
    progress_pct: 60
    persona: Active auction bidder (Joe) sitting at a computer during a live HiBid auction. Needs value estimates fast. No time to research manually. Wants notes saved automatically so he can bid with confidence.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: hibid-analyzer.js
    draft: hibid-analyzer.draft.js
    cache: hibid-analyzer.cache.js
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: Gemini API image analysis works. Blocked on HiBid textarea DOM automation. Chrome extension is now available â€” this changes the approach entirely. First session should attempt textarea interaction via extension before any other approach.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: Now that Chrome extension is available â€” attempt textarea via extension first or continue investigating DOM approach?
      options: 
        - Extension first â€” highest probability of success
        - DOM investigation â€” understand root cause first
        - Both in parallel
      recommendation: Extension first â€” Claude in Chrome has direct page access, bypasses the DOM isolation problem entirely
      confidence: 85%
      confidence_reason: Extension confirmed working on first try per user. Direct browser access eliminates the automation layer that was blocking.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 1
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: Should analysis run on all lots automatically or only when you click a button on a specific lot?
      context: Auto-run = more convenient but costs more API calls. Manual trigger = you control what gets analyzed.
      answer: None
      answered_date: None
      unlocks: Trigger mechanism architecture
    - 
      id: proactive_002
      question: What format do you want the watchlist notes in? (e.g. 'Est: $45-65 | Condition: Good | Items: ceramic vase')
      context: Note format determines what Gemini is asked to return. Standardized format makes notes scannable during live bidding.
      answer: None
      answered_date: None
      unlocks: Gemini prompt design and note writing logic
    - 
      id: proactive_003
      question: Should this work on mobile Chrome or desktop only?
      context: Mobile adds complexity but useful if bidding from phone at estate sales.
      answer: None
      answered_date: None
      unlocks: Mobile compatibility decisions
  autonomous_backlog: 
    - 
      id: auto_001
      task: Document current Gemini API integration â€” what prompt is used, what format is returned, what works
      size: small
      size_estimate: 15min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Research HiBid watchlist page structure â€” document what the notes field looks like in the DOM
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_003
      task: Design standardized note format for watchlist entries based on proactive_002 answer
      size: small
      size_estimate: 15min
      depends_on: proactive_002
      status: blocked
      completed_date: None
  decision_log: 
    - 
      id: decided_001
      decision: Use Gemini API for image analysis
      reason: Already integrated and working. No reason to switch.
      date: 2026-03-12
      resolved_by: existing_build
  assumption_log: 
    - 
      assumption: Chrome (not Opera) will be used for HiBid sessions
      confirmed: True
      confirmed_date: 2026-03-12
    - 
      assumption: No backend needed â€” runs locally in browser
      confirmed: True
      confirmed_date: 2026-03-12
  scope_flags: []
  reusable_findings: 
    - 
      finding: Gemini API base64 inline image analysis pattern â€” works reliably for lot image processing
      applicable_to: 
        - acuscan-ar
        - listing-optimizer
      date: 2026-03-12
  minimum_viable_tests: 
    - 
      feature: Full watchlist save flow
      done_means: 
        - Open HiBid auction lot in Chrome
        - Analysis runs on lot image
        - Value estimate appears in correct format
        - Note is saved to HiBid watchlist without manual copy/paste
        - Note persists after page refresh
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-12
      mode: setup
      completed: 
        - state.json initialized
        - Chrome extension confirmed working on first try
      blockers: 
        - Textarea DOM automation unresolved â€” extension approach now primary
      next_action: Attempt textarea write via Chrome extension on live HiBid page
  strategy_notes: []

### job-match
  _schema_version: 1.0
  _project: job-match
  _folder: job-match
  _created: 2026-03-12
  _last_updated: 2026-03-30
  project: 
    name: Talent Insight Engine (Job Match Platform)
    description: AI-powered job matching platform. Two sides: (1) Job Seeker â€” narrative interview generates behavioral profile, matched against live job pool. (2) Employer â€” browse candidate profiles with AI alignment scoring. Scraping engine runs two-tier crawl: monthly broad discovery + daily targeted delta fetch with JIT dead-link validation.
    status: active
    complexity_budget: medium
    progress_pct: 55
    persona: Job seeker tired of irrelevant results, scam listings, and dead links. Wants a ranked list of real, attainable opportunities matched to their actual behavioral profile â€” not just keywords. Also: employer who wants behavioral fit data, not just credentials.
    promotion_pending: False
    last_touched: 2026-03-30
    drift_risk: LOW
  files: 
    production: Talent-Insight-Engine/server/routes.ts
    draft: Talent-Insight-Engine/server/routes.draft.ts
    cache: Talent-Insight-Engine/server/routes.cache.ts
    last_cache_snapshot: None
    cache_reason: None
  tech_stack: 
    frontend: React 18 + TypeScript + Vite + Tailwind + shadcn/ui
    backend: Node.js + Express + TypeScript
    database: PostgreSQL + Drizzle ORM
    ai: OpenAI GPT-4o via Replit proxy â€” NEEDS MIGRATION to Anthropic API
    auth: Replit Auth (OpenID Connect) â€” NEEDS MIGRATION to standard auth
    scraping: NOT YET BUILT â€” architecture designed, ready to implement
  what_is_built: 
    working: 
      - Resume upload and parsing (PDF + DOCX)
      - Narrative interview â€” story-based questions for job seekers
      - GPT-4o generates: aiSummary, employerSummary, workingTendencies, internalTraits
      - Eligibility evaluation (degree, experience, location)
      - Effort reduction flags (spam detection, input quality)
      - Employer portal â€” browse candidate profiles
      - AI alignment scoring â€” fitBand + signals between candidate and employer intent
      - PostgreSQL schema â€” users, sessions, profiles, conversations, messages
      - Full shadcn/ui component library
      - Landing page, seeker flow, employer flow
    not_built: 
      - Job scraping engine (monthly + daily crawl)
      - Job listing display
      - Deduplication/clustering of job listings
      - Scam/funnel detection and flagging
      - JIT dead-link checker
      - Match ranking between seeker profile and job pool
      - Stale listing feedback loop
      - Application answer auto-generation
    needs_migration: 
      - Replit Auth â†’ standard auth (Passport.js + JWT or similar)
      - OpenAI via Replit proxy â†’ Anthropic Claude API
      - PostgreSQL connection â€” needs new DATABASE_URL outside Replit
  scraping_architecture: 
    tier_1_monthly_broad_crawl: 
      purpose: Discover all job boards, career pages, niche listings â€” build the address book
      sources: 
        - Common Crawl data
        - headless browser cluster
        - company 'Work with Us' footers
        - niche job boards
        - government job portals
      output: master_sources.json â€” prioritized URL/API endpoint list fed to daily scraper
      frequency: monthly
      agent: monthly_discovery_agent
    tier_2_daily_delta_fetch: 
      purpose: High-frequency extraction from known sources â€” new and updated listings only
      sources: URLs from master_sources.json
      method: Check new/updated headers only â€” save bandwidth
      output: daily_jobs_raw.json
      frequency: daily
      agent: daily_scrape_agent
    deduplication_pipeline: 
      stage_1: Normalize â€” standardize titles, salaries, locations
      stage_2: Cluster â€” MinHash or similar to group near-duplicate descriptions across boards
      stage_3: Head record â€” select most reputable source (direct company site preferred) as primary
      stage_4: Collapse duplicates under head record with + expand UI
    jit_dead_link_checker: 
      trigger: Every time results are returned to user
      method: Async HEAD requests via httpx/aiohttp â€” ping all URLs simultaneously
      logic: 
        200: Deliver to user
        404_410: Silently flag as Stale in DB, remove from current view
        301_302: Follow redirect, update Head URL in DB
        403_429: Flag as Throttled â€” scraper may be blocked
    scam_and_funnel_detection: 
      heuristics: 
        - Multiple listings from different recruiters for same role with different pay = lead-gen funnel
        - Same job reposted every 3 days for 6+ months = ghost listing or scam
        - Domain reputation cross-reference against scam database
        - URL redirect chain > 3 hops = data funnel
        - Third-party aggregator vs direct company site â€” weight direct higher
      action: Do NOT delete. Push to bottom tier, apply Suspect Listing flag
      database_fields: 
        original_source: Where first found in monthly crawl
        redirect_chain: Every URL hop to application
        submission_type: direct vs aggregator
        repost_count: How many times seen
        first_seen: Date first discovered
        last_verified: Last successful HEAD request
    stale_listing_feedback: 
      dead_link: Auto-flag if HEAD returns 404
      applicant_sentiment: If 10+ users referred and none report response â€” flag as Stale/Unresponsive
      age_threshold: Flag listings > 30 days old with no update
  matching_engine: 
    tier_1_high_match: Direct correlation between seeker internalTraits and job requirements
    tier_2_limit_pushers: 
      rule: If YearsExperience >= JobRequirement + 2 â†’ flag as Equivalent Match
      display: Show to user with disclaimer: 'Matches structural requirements; specific credential may require upskilling'
      flag: not_true_match â€” helps users explore stretch opportunities
    geospatial_filter: 
      local: Commute distance based on zip code â€” not just city name
      remote: Verified Remote-First tag â€” separate bucket from local results
    knowledge_match: 
      example: User has 'programming logic background' + job requires 'Python' â†’ flag as Knowledge Match
      display: Matches structural logic requirements; specific syntax may require upskilling
  session: 
    mode: None
    active: False
    started: None
    handoff_note: Replit migration complete. Code is in Talent-Insight-Engine subfolder. Current Claude Code session is inventorying codebase. Migration priorities: (1) swap Replit Auth, (2) swap OpenAI proxy to Anthropic, (3) get DB running locally. Then build scraping engine starting with daily delta fetch.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: Replit migration â€” confirmed complete?
      options: 
        - Yes â€” Talent-Insight-Engine folder is in job-match folder
        - No â€” still pending
      recommendation: Confirmed complete based on current Claude Code session finding the files
      confidence: 95%
      confidence_reason: Claude Code session found Talent-Insight-Engine subdirectory present
      depends_on: None
      status: answered
      answer: Yes â€” migration complete
      resolved_by: user_confirmation
      resolved_date: 2026-03-13
      created: 2026-03-12
      expires_after_sessions: 1
      sessions_pending: 0
    - 
      id: decision_002
      question: Auth migration â€” replace Replit Auth with what?
      options: 
        - Passport.js + JWT (self-managed)
        - Clerk (hosted auth, fast setup)
        - Auth0 (enterprise-grade)
        - Simple session-based with bcrypt (no third party)
      recommendation: Clerk â€” fastest to swap in, handles sessions/JWT/OAuth, generous free tier, minimal code change
      confidence: 75%
      confidence_reason: Clerk is the fastest Replit Auth replacement with least code rewrite. Auth0 is more powerful but overkill for current stage.
      depends_on: None
      status: answered
      answer: Clerk
      resolved_by: user_confirmation
      resolved_date: 2026-03-13
      created: 2026-03-13
      expires_after_sessions: 2
      sessions_pending: 0
    - 
      id: decision_003
      question: AI migration â€” keep GPT-4o or switch to Claude (Anthropic API)?
      options: 
        - Keep GPT-4o (swap API key only)
        - Switch to Claude Sonnet (Anthropic API)
        - Run both â€” A/B test quality
      recommendation: Switch to Claude Sonnet â€” you already have Anthropic API access via Claude Pro, no new account needed, narrative/behavioral analysis is a Claude strength
      confidence: 80%
      confidence_reason: Anthropic API already in your stack. Claude is strong at narrative interpretation which is core to this app.
      depends_on: None
      status: answered
      answer: Claude Sonnet (Anthropic API)
      resolved_by: user_confirmation
      resolved_date: 2026-03-13
      created: 2026-03-13
      expires_after_sessions: 2
      sessions_pending: 0
    - 
      id: decision_004
      question: Database â€” where does PostgreSQL run after leaving Replit?
      options: 
        - Supabase (hosted Postgres, free tier)
        - Railway (hosted, simple)
        - Local PostgreSQL on your machine
        - Neon (serverless Postgres)
      recommendation: Supabase â€” free tier is generous, has good dashboard UI, and pairs well with your existing stack
      confidence: 80%
      confidence_reason: Free tier covers development and early production. Easy migration path from Replit's Postgres.
      depends_on: None
      status: answered
      answer: Supabase
      resolved_by: user_confirmation
      resolved_date: 2026-03-13
      created: 2026-03-13
      expires_after_sessions: 2
      sessions_pending: 0
    - 
      id: decision_005
      question: Scraping engine â€” start with monthly broad crawl or daily delta fetch first?
      options: 
        - Monthly broad crawl first â€” build the address book
        - Daily delta fetch first â€” prove the pipeline works on known sources
        - Both simultaneously
      recommendation: Daily delta fetch first â€” use known free sources (RemoteOK, We Work Remotely, Adzuna) to prove pipeline works before investing in broad crawl infrastructure
      confidence: 85%
      confidence_reason: Broad crawl is expensive and complex. Proving the pipeline on known sources de-risks the architecture before scaling up.
      depends_on: None
      status: answered
      answer: Daily delta fetch first
      resolved_by: user_confirmation
      resolved_date: 2026-03-13
      created: 2026-03-13
      expires_after_sessions: 3
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: Should the platform be offered as SaaS to other job seekers or stay personal/portfolio use?
      context: Determines whether to add billing, multi-user accounts, and marketing infrastructure. Significant scope difference.
      answer: Both — single platform, role-based login. Job seekers get seeker view, employers get employer view. SaaS model with login-gated roles.
      answered_date: 2026-03-31T10:36:24
      unlocks: Architecture decisions around multi-tenancy and billing
    - 
      id: proactive_002
      question: Should employer portal be prioritized before or after scraping engine?
      context: Employer side is already partially built. Scraping engine is what feeds job seekers real data. Both are needed for a complete product.
      answer: Scraping engine first. Employer portal is mocked — leave it mocked until scraping produces usable results.
      answered_date: 2026-03-31T10:36:24
      unlocks: Build sequence for next 5 sessions
    - 
      id: proactive_003
      question: For the scam database â€” should it be private to your platform or eventually shared/open source?
      context: Shared scam database becomes a community moat. Private keeps it proprietary. Open source builds trust and contributions.
      answer: DEFERRED. Default private. Risk of publishing = giving scammers a detection-evasion map. Will revisit once platform has enough data to evaluate whether sharing has net positive value.
      answered_date: 2026-03-31T10:36:24
      unlocks: Scam database architecture and data sharing strategy
    - 
      id: proactive_004
      question: Should job ratings be shown to users in v1 or held back until v2?
      context: Showing ratings adds UI complexity and requires calibrating the rating system. Hiding them keeps v1 cleaner but reduces user confidence in results.
      answer: Build dual-axis rating in v1. Axis 1 = geo proximity by zip radius: green (in range), orange (outside), red (far but matching). Axis 2 = job match score box: green/orange/red. Composite shown as color pair (green/green, green/orange, etc). Low/low combos suppressed from results.
      answered_date: 2026-03-31T10:36:24
      unlocks: Rating display UI and calibration decisions
  autonomous_backlog: 
    - 
      id: auto_001
      task: Complete codebase inventory â€” document all existing files, what each does, what works vs incomplete
      size: medium
      size_estimate: 30min
      depends_on: None
      status: completed
      completed_date: 2026-03-30
      completion_notes: Talent-Insight-Engine: Express+TypeScript server, React+Wouter client, Drizzle ORM on Postgres. Two DB tables: profiles (narrative interview data + AI summaries) and jobs. Auth: Replit OIDC via openid-client+passport — all in server/replit_integrations/auth/. AI: OpenAI client in server/routes.ts (narrative analysis, alignment scoring, employer summary). 5 pages: Landing, NarrativeInput (6-section interview + resume upload), RefineSummary, CandidateView, EmployerDashboard+Framing. What works: full seeker flow, employer alignment scoring, employer summary generation, candidate browsing. What's incomplete: no job ingestion pipeline wired to UI, no matching engine connecting internalTraits to jobs table, jobs table exists in schema but no routes populate it from external sources. Migration blockers: replitAuth.ts (OIDC using REPL_ID/ISSUER_URL), OpenAI in routes.ts, DATABASE_URL + SESSION_SECRET env vars needed for Supabase.
    - 
      id: auto_002
      task: Document Replit Auth dependency â€” identify every file that imports or uses replitAuth, map migration scope
      size: small
      size_estimate: 20min
      depends_on: auto_001
      status: ready
      completed_date: None
    - 
      id: auto_003
      task: Document OpenAI dependency â€” identify every API call, map to equivalent Anthropic Claude API calls
      size: small
      size_estimate: 20min
      depends_on: auto_001
      status: ready
      completed_date: None
    - 
      id: auto_004
      task: Research RemoteOK and We Work Remotely API/RSS endpoints â€” document structure, rate limits, fields returned
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_005
      task: Research Adzuna API â€” free tier limits, endpoint structure, job field mapping
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_006
      task: Design scam detection heuristic ruleset â€” document all criteria, scoring weights, action thresholds
      size: medium
      size_estimate: 45min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_007
      task: Design deduplication pipeline â€” MinHash implementation spec, normalization rules, head record selection criteria
      size: medium
      size_estimate: 45min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_008
      task: Design JIT dead-link checker â€” async HEAD request implementation, status code handling, DB update logic
      size: small
      size_estimate: 30min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_009
      task: Research Supabase free tier â€” setup requirements, Postgres migration from Replit, connection string format
      size: small
      size_estimate: 20min
      depends_on: decision_004
      status: ready
      completed_date: None
    - 
      id: auto_010
      task: Map matching engine logic â€” how internalTraits from narrative interview connect to job requirement fields
      size: medium
      size_estimate: 45min
      depends_on: auto_001
      status: ready
      completed_date: None
  decision_log: 
    - 
      id: decided_001
      decision: Do not scrape Indeed or LinkedIn
      reason: Both actively block scrapers. Risk of IP bans outweighs any data benefit.
      date: 2026-03-12
      resolved_by: existing_constraint
    - 
      id: decided_002
      decision: Scam/low-quality listings are NOT deleted â€” pushed to bottom tier and flagged
      reason: Valid jobs can get caught in scam-adjacent patterns. Flagging preserves data integrity while protecting user experience.
      date: 2026-03-13
      resolved_by: architecture_decision
    - 
      id: decided_003
      decision: Replit export migration is complete
      reason: Claude Code session confirmed Talent-Insight-Engine subdirectory present in job-match folder
      date: 2026-03-13
      resolved_by: user_confirmation
  assumption_log: 
    - 
      assumption: Narrative/behavioral matching is more valuable differentiator than keyword matching
      confirmed: True
      confirmed_date: 2026-03-13
    - 
      assumption: Daily delta fetch proves pipeline before investing in monthly broad crawl
      confirmed: False
      confirmed_date: None
    - 
      assumption: Supabase or similar hosted Postgres replaces Replit database cleanly
      confirmed: False
      confirmed_date: None
  scope_flags: []
  reusable_findings: 
    - 
      finding: Narrative interview + behavioral trait extraction pattern â€” applicable to Sentinel Performer personality clone intake
      applicable_to: 
        - sentinel-performer
      date: 2026-03-13
  minimum_viable_tests: 
    - 
      feature: Migration complete
      done_means: 
        - App runs locally without Replit environment
        - Auth works without Replit Auth
        - AI calls work via Anthropic API
        - Database connects via Supabase or equivalent
      verified: False
      verified_date: None
    - 
      feature: Scraping pipeline v1
      done_means: 
        - At least one source (RemoteOK or Adzuna) returns live job listings
        - Duplicate listings are collapsed under head record
        - JIT dead-link check runs before results displayed
        - Scam/suspect listings pushed to bottom with flag
        - Results display in existing frontend
      verified: False
      verified_date: None
    - 
      feature: Full seeker flow
      done_means: 
        - Seeker completes narrative interview
        - AI generates profile with internalTraits
        - Profile matched against live job pool
        - Ranked results show with match tier labels
        - Dead links removed before display
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-13
      mode: inventory
      completed: 
        - Replit migration confirmed complete
        - Codebase analyzed â€” 55% complete, not 35%
        - Scraping architecture fully designed from recovered conversation
        - state.json updated with full architecture
      blockers: 
        - Replit Auth must be replaced before app runs outside Replit
        - OpenAI proxy must be replaced with Anthropic API
        - PostgreSQL needs new host
      next_action: Begin migration: (1) set up Supabase project + paste DATABASE_URL, (2) swap OpenAI calls to Anthropic Claude Sonnet, (3) install Clerk + replace Replit Auth. Then build daily delta scraper (RemoteOK, Adzuna).
  strategy_notes: 
    - Narrative interview differentiator is genuinely unique â€” preserve and emphasize it
    - Migration unblocks everything â€” prioritize auth + database + AI swap before any new features
    - Scraping engine is the missing half â€” daily delta fetch first, monthly broad crawl second
    - Reusable finding: narrative intake pattern applies to Sentinel Performer personality clone

### listing-optimizer
  _schema_version: 1.0
  _project: listing-optimizer
  _folder: listing-optimizer
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: eBay Listing Optimizer
    description: Bulk listing optimization engine that ingests raw inventory data, generates keyword-dense ATS-optimized titles, populates missing fields (condition, UPC/ISBN, category), and outputs eBay File Exchange ready CSV.
    status: new
    complexity_budget: medium
    progress_pct: 0
    persona: eBay reseller (Joe, 572 active listings) who knows his inventory but doesn't have time to manually optimize every title and fill missing fields. Wants to drop a CSV in and get a better CSV out.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: listing-optimizer.html
    draft: listing-optimizer.draft.html
    cache: listing-optimizer.cache.html
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: New project. No code yet. Joe has 572 active listings and deep title-writing expertise. First session: define input format, output format, and which optimizations to run.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: Personal tool only or productize for other sellers?
      options: 
        - Personal only â€” optimize Joe's 572 listings
        - Beta test with select sellers
        - Full SaaS product
      recommendation: Personal first â€” prove it works on your own inventory, then decide
      confidence: 90%
      confidence_reason: Building for yourself first is faster and gives you real feedback before committing to multi-user architecture.
      depends_on: None
      status: resolved
      answer: Personal first — build and validate on Joe's own 572 listings. Productize decision deferred until tool proves value on real inventory.
      resolved_by: joe
      resolved_date: 2026-03-31T10:39:52
      created: 2026-03-12
      expires_after_sessions: 2
      sessions_pending: 0
    - 
      id: decision_002
      question: Input format â€” eBay bulk export CSV or manual entry or both?
      options: 
        - eBay bulk export CSV only
        - Manual entry only
        - Both
      recommendation: eBay bulk export CSV â€” you already have 572 listings to process
      confidence: 95%
      confidence_reason: CSV batch processing is the highest leverage use case given existing inventory size.
      depends_on: None
      status: resolved
      answer: eBay bulk export CSV only — primary input format.
      resolved_by: joe
      resolved_date: 2026-03-31T10:45:51
      created: 2026-03-12
      expires_after_sessions: 2
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: What are your SKU prefix conventions for physical storage location tracking?
      context: Optimizer needs to preserve or understand existing SKU format to not break your storage system.
      answer: Location-based codes (e.g. BOX-01, BIN-A3). Optimizer must preserve existing SKU values exactly — do not modify or reformat them.
      answered_date: 2026-03-31T10:41:46
      unlocks: SKU handling logic
    - 
      id: proactive_002
      question: Which categories make up the majority of your 572 listings?
      context: Category-specific title rules â€” e.g. books need ISBN, electronics need model numbers. Knowing top categories lets us build the right rules first.
      answer: PARTIAL — confirmed: vintage clothing, electronics, books/media, home decor. Full category breakdown requires pulling eBay report — categories shift over time. Build optimization rules for these four first; add more after report review.
      answered_date: 2026-03-31T10:41:46
      unlocks: Category-specific optimization rules
    - 
      id: proactive_003
      question: Should the optimizer suggest a price adjustment based on recent eBay sold data?
      context: Adds significant value but requires eBay API access. Could share that infrastructure with Arbitrage Pulse.
      answer: Yes — include price suggestions based on eBay sold data. Share eBay API integration with Arbitrage Pulse.
      answered_date: 2026-03-31T10:39:52
      unlocks: Pricing feature scope and eBay API integration
  autonomous_backlog: 
    - 
      id: auto_001
      task: Research eBay File Exchange CSV format â€” document all required and optional fields
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Design title optimization rules â€” keyword density, character limit, banned words, category-specific patterns
      size: small
      size_estimate: 25min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_003
      task: Design missing field detection logic â€” which fields are commonly empty and how to auto-populate
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
  decision_log: []
  assumption_log: 
    - 
      assumption: eBay File Exchange format is the output target
      confirmed: False
      confirmed_date: None
    - 
      assumption: AI-generated titles should preserve Joe's existing title style and conventions
      confirmed: False
      confirmed_date: None
  scope_flags: []
  reusable_findings: 
    - 
      finding: eBay API for sold listings pricing â€” being researched for Arbitrage Pulse, share the integration
      applicable_to: 
        - arbitrage-pulse
      date: 2026-03-12
  minimum_viable_tests: 
    - 
      feature: Bulk listing optimization
      done_means: 
        - Accepts eBay export CSV as input
        - Generates optimized title for each listing
        - Flags missing condition, UPC/ISBN fields
        - Outputs valid eBay File Exchange CSV
        - Processes 50 listings without errors
        - Output titles are noticeably better than input titles
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-12
      mode: setup
      completed: 
        - state.json initialized
        - Project added to studio
      blockers: []
      next_action: Answer input/output format decisions, get SKU convention info, then design optimization rules
  strategy_notes: []

### nutrimind
  _schema_version: 1.0
  _project: nutrimind
  _folder: nutrimind
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: NutriMind
    description: React-based AI meal planning app with multi-week planning, budget tiers, meal approval workflows, and ingredient overlap detection.
    status: paused
    complexity_budget: medium
    progress_pct: 75
    persona: Person trying to eat better without spending too much time or money. Wants a plan handed to them. Will swap meals they don't like but won't build a plan from scratch. Cooking skill: basic.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: src/App.jsx
    draft: src/App.draft.jsx
    cache: src/App.cache.jsx
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: Three iterations complete. Iteration 3 is current. Meal approval, budget tiers, multi-week planning all implemented. Identify remaining gaps before adding anything new.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: What defines NutriMind as complete â€” what is the finish line?
      options: 
        - All planned features working
        - Personal use ready
        - Productize for other users
      recommendation: Define personal use ready first â€” then decide if productizing is worth the extra work
      confidence: 75%
      confidence_reason: Productizing adds significant scope. Better to finish core first.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 3
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: Should shopping list generation be part of the MVP or post-launch?
      context: Natural extension of meal planning. Medium complexity add.
      answer: None
      answered_date: None
      unlocks: Feature roadmap after core completion
    - 
      id: proactive_002
      question: Should the app remember your meal history to avoid repeating recent meals?
      context: Requires localStorage or backend. Adds significant value but adds complexity.
      answer: None
      answered_date: None
      unlocks: Data persistence architecture
  autonomous_backlog: 
    - 
      id: auto_001
      task: Read iteration 3 code â€” document all features, what works, what's incomplete or broken
      size: small
      size_estimate: 25min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Identify any known token truncation or useEffect issues from previous sessions
      size: small
      size_estimate: 15min
      depends_on: auto_001
      status: blocked
      completed_date: None
  decision_log: []
  assumption_log: 
    - 
      assumption: React functional components and hooks only â€” no class components
      confirmed: True
      confirmed_date: 2026-03-12
    - 
      assumption: Anthropic API for meal generation
      confirmed: True
      confirmed_date: 2026-03-12
  scope_flags: []
  reusable_findings: []
  minimum_viable_tests: 
    - 
      feature: Full meal planning flow
      done_means: 
        - User selects budget tier and goals
        - Weekly plan generates without API errors
        - Individual meals can be swapped
        - Multi-week view works without state corruption
        - No useEffect infinite loops
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-12
      mode: setup
      completed: 
        - state.json initialized
      blockers: []
      next_action: Read iteration 3 code, document current state, identify completion gaps
  strategy_notes: []

### sentinel-core
  ProjectName: Sentinel Core
  SystemStatus: INITIALIZING
  LastSync: 2026-03-27T23:15:00Z
  ActiveAgents: 
    - performer
    - viewer
  GlobalFlags: 
    MaintenanceMode: False
    DebugLevel: INFO
    UniversalLogEnabled: True
  CurrentOrchestratorBriefing: Establishing baseline state for agent synchronization.
  last_touched: 2026-04-01
  drift_risk: LOW

### sentinel-performer
  ProjectName: Sentinel Performer
  AgentRole: EXECUTION
  Status: IDLE
  LastCommandExecuted: None
  ToolCapabilities: 
    - FileIO
    - PythonInterpreter
    - SearchLive
  ExecutionQueue: []
  PendingCommits: 0
  ResourceUsage: 
    Latency: 0ms
    Model: Claude-4.6-Sonnet
  last_touched: 2026-04-01
  drift_risk: LOW

### sentinel-viewer
  ProjectName: Sentinel Viewer
  AgentRole: MONITORING
  Status: READY
  ActiveViews: 
    - SystemHealth
    - LogStream
  Alerts: []
  VisualizationConfig: 
    RefreshRate: 5s
    Theme: Dark
    TailLogs: 50
  LastLogIngested: None
  last_touched: 2026-04-01
  drift_risk: LOW

### squeeze-empire
  _schema_version: 1.0
  _project: squeeze-empire
  _folder: squeeze-empire
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: Squeeze Empire
    status: active
    complexity_budget: low
    progress_pct: 85
    description: Single-file browser-based lemonade stand business simulation with multi-system economics, mini-games, and seasonal progression.
    persona: Casual gamer who wants a satisfying idle/incremental game. Plays in short sessions. Expects things to make sense without reading instructions. Wants to feel like their decisions matter.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: squeeze-empire.html
    draft: squeeze-empire.draft.html
    cache: squeeze-empire.cache.html
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: File recovered â€” resume late-game progression implementation.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: What defines late-game completion â€” what is the win condition or final milestone?
      options: 
        - Reach a revenue target
        - Unlock all upgrades
        - No win condition â€” infinite idle
        - Story ending
      recommendation: Reach a revenue target + unlock all upgrades â€” gives clear progression and satisfying endpoint
      confidence: 70%
      confidence_reason: Depends on original design intent. User knows best.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 2
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: Should the game save state between sessions or reset each time?
      context: localStorage save would make it a true idle game. No save = arcade style. Significant architecture difference.
      answer: None
      answered_date: None
      unlocks: Save system implementation
    - 
      id: proactive_002
      question: After late-game is done â€” release publicly, keep personal, or productize?
      context: Affects whether we add analytics, sharing features, or mobile optimization pass.
      answer: None
      answered_date: None
      unlocks: Post-completion feature decisions
  autonomous_backlog: 
    - 
      id: auto_001
      task: Read squeeze-empire.html and document all current game systems â€” what exists and what state each is in
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Identify all TODO comments or placeholder sections in the current file
      size: small
      size_estimate: 10min
      depends_on: auto_001
      status: blocked
      completed_date: None
    - 
      id: auto_003
      task: Run PERSONA adversarial test â€” play as confused first-time user for 20 sessions, log all friction points
      size: medium
      size_estimate: 60min
      depends_on: None
      status: ready
      completed_date: None
  decision_log: []
  assumption_log: 
    - 
      assumption: Single HTML file constraint is non-negotiable
      confirmed: True
      confirmed_date: 2026-03-12
    - 
      assumption: Vanilla JS only, no frameworks
      confirmed: True
      confirmed_date: 2026-03-12
  scope_flags: []
  reusable_findings: []
  minimum_viable_tests: 
    - 
      feature: Late-game completion
      done_means: 
        - Player can reach the defined win condition through normal play
        - No economy exploits that skip progression
        - All mini-games functional at late-game state
        - No console errors during 10 minute play session
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-12
      mode: setup
      completed: 
        - state.json initialized
      blockers: []
      next_action: Read current file state, identify late-game gaps, confirm win condition
    - 
      date: 2026-03-16
      mode: janitor
      completed: 
        - Production file squeeze-empire.html located and moved to project folder
        - state.json updated: status active, handoff updated
      blockers: []
      next_action: Resume late-game progression implementation
  strategy_notes: []

### whatnot-apps
  _schema_version: 1.0
  _project: whatnot-apps
  _folder: whatnot-apps
  _created: 2026-03-12
  _last_updated: 2026-03-25
  project: 
    name: Whatnot Applications
    description: Job application materials for Whatnot remote roles: Fraud Agent, Trust & Safety Agent, CX Agent Overnight.
    status: active
    complexity_budget: low
    progress_pct: 50
    persona: Whatnot hiring manager reviewing 50+ applications. Skims in 30 seconds. Looking for: platform knowledge, trust/safety instincts, resale market credibility, async communication ability.
    promotion_pending: False
    last_touched: 2026-03-25
    drift_risk: LOW
  files: 
    production: resume-fraud-agent.docx
    draft: resume-fraud-agent.draft.docx
    cache: resume-fraud-agent.cache.docx
    last_cache_snapshot: None
    cache_reason: None
  session: 
    mode: None
    active: False
    started: None
    handoff_note: Three resumes and cover letter drafted. Key differentiator: resale market network + eBay operation + Commonwealth Picker moderation. Review and refine before submitting.
  test_lock: 
    locked: False
    lock_reason: None
    lock_started: None
    locked_by: None
    unlock_condition: None
    findings_count: 0
  decisions: 
    - 
      id: decision_001
      question: Which Whatnot role to prioritize for application submission first?
      options: 
        - Fraud Agent
        - Trust & Safety Agent
        - CX Agent Overnight
      recommendation: Trust & Safety Agent â€” best alignment with moderation background and written communication preference
      confidence: 75%
      confidence_reason: Commonwealth Picker moderation experience is a direct differentiator for T&S. Fraud Agent is close second.
      depends_on: None
      status: pending
      answer: None
      resolved_by: None
      resolved_date: None
      created: 2026-03-12
      expires_after_sessions: 1
      sessions_pending: 0
  proactive_questions: 
    - 
      id: proactive_001
      question: Do you have the actual current Whatnot job posting URLs to tailor against?
      context: Resumes tailored to exact posting language score significantly higher on ATS systems.
      answer: None
      answered_date: None
      unlocks: Final resume tailoring pass
    - 
      id: proactive_002
      question: Should we build a general Whatnot cover letter or three separate role-specific ones?
      context: Separate letters are stronger but more work. General letter with swap sections is faster.
      answer: None
      answered_date: None
      unlocks: Cover letter strategy
  autonomous_backlog: 
    - 
      id: auto_001
      task: Review all three existing resume files â€” identify gaps, inconsistencies, weak sections
      size: small
      size_estimate: 20min
      depends_on: None
      status: ready
      completed_date: None
    - 
      id: auto_002
      task: Research current Whatnot job postings â€” pull exact language and requirements
      size: small
      size_estimate: 15min
      depends_on: None
      status: ready
      completed_date: None
  decision_log: []
  assumption_log: 
    - 
      assumption: Blackdot Group role ending May 2026 â€” available for remote start
      confirmed: True
      confirmed_date: 2026-03-12
    - 
      assumption: Strong preference for written/async communication â€” feature not liability for T&S
      confirmed: True
      confirmed_date: 2026-03-12
  scope_flags: []
  reusable_findings: []
  minimum_viable_tests: 
    - 
      feature: Application ready
      done_means: 
        - Resume tailored to specific posting language
        - All dates and titles accurate
        - Differentiators (resale network, moderation) prominent in first third
        - Cover letter under 300 words
        - ATS-friendly formatting â€” no tables, no headers that confuse parsers
      verified: False
      verified_date: None
  adversarial_log: []
  backups: []
  session_log: 
    - 
      date: 2026-03-12
      mode: setup
      completed: 
        - state.json initialized
      blockers: []
      next_action: Review existing materials, pull current job postings, prioritize role
  strategy_notes: []

## STANDING RULES

Total: 12 rules

  rule-001
    trigger:     scraper returns 403 three consecutive times on same URL
    action:      mark source as Tier 3, add to supervisor-inbox.json for fix, skip and continue
    applies_to:  all scraper agents, company-registry-crawler, job-source-discovery
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-002
    trigger:     scraper returns 429 (rate limit)
    action:      exponential backoff: wait 10s, 20s, 40s then mark Tier 3 if still failing
    applies_to:  all scraper agents
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-003
    trigger:     scoring task under 500 tokens
    action:      always route to Gemini Flash (Tier 0), never use Claude quota
    applies_to:  whiteboard-agent, ghost-book-validator, product-archaeology
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-004
    trigger:     session ends (user types /exit or says done for today)
    action:      commit all dirty projects, update changelogs, update status.json
    applies_to:  claude-code-session
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-005
    trigger:     same error pattern appears in 2+ agent scripts
    action:      build shared utility in _studio/utilities/, update README, migrate all affected scripts
    applies_to:  all agents
    created:     2026-03-19
    approved_by: joe
    times_applied: 1

  rule-006
    trigger:     overnight batch task
    action:      always route to Ollama exclusively, never Gemini or Claude during overnight runs
    applies_to:  all batch agents, ghost-book, product-archaeology
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-007
    trigger:     career page returns JS-rendered shell (body < 2000 chars or react-root detected)
    action:      classify as Tier 2 (Playwright), add to scraper-config-tier2.json, do not mark as failed
    applies_to:  company-registry-crawler
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-008
    trigger:     CDX query returns 0 results for ATS domain (lever, greenhouse, ashby)
    action:      skip CDX for that domain, rely on direct HTTP scrape in daily-scraper-config.json instead
    applies_to:  job-source-discovery, update_scraper_config
    created:     2026-03-19
    approved_by: joe
    times_applied: 1

  rule-009
    trigger:     mobile inbox has more than 10 pending items
    action:      auto-expire items pending >7 days by setting status to expired, notify once in session-log
    applies_to:  supervisor, workflow-intelligence
    created:     2026-03-19
    approved_by: joe
    times_applied: 0

  rule-010
    trigger:     agent script prints user-sourced text (titles, names, web content)
    action:      always wrap in safe_str() from utilities/unicode_safe.py before printing
    applies_to:  all agents
    created:     2026-03-19
    approved_by: joe
    times_applied: 1

  rule-011
    trigger:     any script opens a JSON file on Windows
    action:      always use safe_json_load() from unicode_safe.py, or open(f, encoding='utf-8', errors='replace') — never plain open(f)
    applies_to:  all agents, inbox-manager, audit scripts, diagnostic one-liners
    created:     2026-03-19
    approved_by: joe
    times_applied: 1

  rule-012
    trigger:     any session involves project prioritization or build order decisions
    action:      client-services-website is OVERRIDE PRIORITY — this project directly funds Joe's income. Always rank above other whiteboard items regardless of score. Build before any other new project is started.
    applies_to:  whiteboard-agent, supervisor, auto-answer, all planning sessions
    created:     2026-03-25
    approved_by: joe
    times_applied: 0


## WHITEBOARD

Last updated: 2026-04-03T04:00:20.197280
Total items: 68

  [9/10] Higgsfield Original Series — Backwards Design
    id:      higgsfield-backwards-design
    type:    distribution+content-strategy
    status:  WHITEBOARD
    source:  
    description: Monitor platform weekly for genre gaps and vote velocity. Build CTW characters specifically for underserved genres. Design story structure for 2-10 minute episode format from day one. Soul ID consistency built into character spec. Enter contests in low-competition genres. Sponsored production if contest win.
    score_breakdown:
      total_score: 9
      recommended_action: BUILD
      why_now: Data-driven niche content creation and short-form distribution are key to success for new creators today.
      effort_estimate: months
      revenue_estimate: MEDIUM
      top_risk: Success is highly dependent on accurately identifying viable niches and winning contests.
      score_breakdown: {'market_timing': 9, 'feasibility': 9, 'revenue_potential': 7, 'strategic_fit': 10}
    added:   2026-03-29

  [8/10] I've played and reviewed 1.000+ horror games, here are some gems you might not h
    id:      arch-reddit-0001
    type:    product_archaeology
    status:  new
    source:  reddit_r_patientgamers
    description: I've been in love with the genre for all my life and could write 30 pages of philosophical analysis on why it's such a beautiful art form, but I'll spare you the details and get to some interesting po
    score_breakdown:
      total_score: 8
      market_gap_score: 8
      build_feasibility: 9
      revenue_potential: 6
      urgency: 7
      why_now: The continuous growth of the horror game genre makes a comprehensive, curated historical and philosophical analysis of its roots and overlooked gems increasingly valuable for both new and veteran players.
      recommended_action: PUBLISH
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Creator burnout or inability to distill unique, engaging insights from such a vast number of games without it becoming superficial.
    tags:    product_archaeology, reddit, patientgamers
    added:   2026-03-19T15:13:35.684353
    url:     https://reddit.com/r/patientgamers/comments/scmm2n/ive_played_and_reviewed_1000_horror_games_here/

  [8/10] DuPont Corfam
    id:      vint-0011
    type:    product_gap
    status:  new
    source:  
    description: Yes, the search for a perfect synthetic leather that perfectly mimics natural properties and sustainability is still ongoing, though modern vegan leathers are significantly better.
    score_breakdown:
      total_score: 8
      market_gap_score: 9
      build_feasibility: 7
      revenue_potential: 9
      urgency: 8
      why_now: Modern material science and a booming demand for sustainable, high-performance vegan alternatives create a ripe environment to re-address Corfam's original ambition with better technology.
      recommended_action: RESEARCH
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: Developing a new material that genuinely surpasses existing vegan leathers in breathability, comfort, durability, and cost-effectiveness while achieving industrial scale production.
    tags:    product_archaeology, vintage, vintage-1960s
    added:   2026-03-19T15:16:03.025773

  [8/10] Bring back the original SoBe Elixir drink line nationwide
    id:      nost-0028
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    description: Remember SoBe Elixirs? That tangy, refreshing drink that just hit different? Thousands of people online are united in wanting it back, and I started a petition asking PepsiCo to bring back the origina
    score_breakdown:
      total_score: 8
      market_gap_score: 8
      build_feasibility: 9
      revenue_potential: 6
      urgency: 8
      why_now: The strong wave of 90s and early 2000s nostalgia, amplified by dedicated online communities, presents a timely opportunity for PepsiCo to reintroduce a distinct and beloved brand.
      recommended_action: BUILD
      effort_estimate: months
      revenue_estimate: SMALL
      top_risk: Nostalgia appeal might not translate into sufficient widespread, repeat purchases to justify nationwide production and distribution costs.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783572
    url:     https://reddit.com/r/nostalgia/comments/1rxrcq0/bring_back_the_original_sobe_elixir_drink_line/

  [8/10] eBay Item Identifier â€” Consensus Engine
    id:      ebay-identifier-app
    type:    product
    status:  WHITEBOARD
    source:  Gemini sidebar + Joe
    description: Mobile/VS Code app replacing Google Lens workflow for resellers. 6-track identification: pixel match, VLM attribute extraction, hallmark OCR, archive RAG, molded-mark OCR, manual cross-ref. Multi-image input, filter/rank layer, re-roll feature, eBay draft export.
    score_breakdown:
      total_score: 8
      market_gap_score: 9
      build_feasibility: 5
      revenue_potential: 8
      urgency: 7
      why_now: Advancements in Vision-Language Models (VLMs) and Retrieval-Augmented Generation (RAG) make this complex multi-modal identification feasible, while the reseller market remains eager for AI-driven efficiency.
      recommended_action: BUILD
      effort_estimate: months
      revenue_estimate: MEDIUM
      top_risk: The sheer complexity and data acquisition challenge for comprehensive 'archive RAG' and fine-tuned VLM attribute extraction could make it prohibitively expensive or technically unachievable to a high standard.
    added:   2026-03-25

  [8/10] AI Services Client Website
    id:      client-services-website
    type:    product
    status:  WHITEBOARD
    source:  Sidebar sessions
    description: Lead generation website for AI project services. Intake triggers Client Solutions Agent pipeline. High upfront / low monthly quoting model. Funds Joe as employee and system wishlist. Full agent backend already blueprinted in Synthetic Talent Agency files.
    score_breakdown:
      total_score: 8
      market_gap_score: 7
      build_feasibility: 9
      revenue_potential: 8
      urgency: 7
      why_now: 2026 is an optimal time as businesses increasingly adopt AI but require structured, reliable service providers to implement complex solutions and manage projects.
      recommended_action: BUILD
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: Client acquisition and standing out in a highly competitive AI services market.
    added:   2026-03-25

  [8/10] Traitor Protocol Adversarial Testing
    id:      traitor-protocol
    type:    system-improvement
    status:  new
    source:  gemini-session-2026-03-26
    description: One agent per overnight run designated as liar. Mayor must catch it. Catches hallucination drift. 7-step Mayor validation. Agent scoring 0-100 with dissolve threshold at 20.
    score_breakdown:
      total_score: 8
      market_gap_score: 9
      build_feasibility: 6
      revenue_potential: 9
      urgency: 9
      why_now: As LLM adoption accelerates into critical enterprise functions, robust, automated hallucination detection becomes an indispensable and urgent requirement.
      recommended_action: BUILD
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: The effectiveness of the 'Mayor' agent in reliably detecting subtle hallucination drift introduced by the 'Liar' agent.
    tags:    testing, adversarial, hallucination, overnight, mayor
    added:   2026-03-26

  [8/10] War Room Decision Protocol
    id:      war-room-protocol
    type:    protocol
    status:  ACTIVE
    source:  
    description: Standard protocol for high-stakes decisions. Mirofish runs automated scoring. War room convenes domain-appropriate character council on top scorers. Characters selected to create genuine expertise tension. Output: scored data + adversarial reasoning + minority report + implementation orders. Proven effective on Operation Context Lock 2026-03-29.
    score_breakdown:
      total_score: 8
      recommended_action: PITCH
      why_now: Increasing complexity and AI demand robust human-centered decision protocols to cut through noise.
      effort_estimate: weeks
      revenue_estimate: MEDIUM
      top_risk: Sourcing & managing genuinely diverse and adversarial 'characters' for each unique decision presents a significant challenge.
      score_breakdown: {'market_timing': 8, 'feasibility': 6, 'revenue_potential': 8, 'strategic_fit': 9}
    added:   2026-03-29

  [8/10] Ghost Book Script Vault + Salvage Protocol
    id:      ghost-book-script-vault
    type:    content-management
    status:  ACTIVE
    source:  
    description: Permanent archive for unused scripts with active salvage pass before retirement. Grade A scripts get full salvage — scenes, characters, dialogue, concepts extracted to salvage/ folder and indexed in salvage-log.json. Agents query salvage before generating new content. Higgsfield potential flag for scenes that work as standalone shorts. Nothing deleted, everything indexed.
    score_breakdown:
      total_score: 8
      recommended_action: BUILD
      why_now: Maximizing existing content is crucial in today's content-heavy, AI-assisted creative landscape.
      effort_estimate: weeks
      revenue_estimate: MEDIUM
      top_risk: Manual salvage process can be time-consuming and divert focus from new project generation.
      score_breakdown: {'market_timing': 8, 'feasibility': 8, 'revenue_potential': 7, 'strategic_fit': 9}
    added:   2026-03-29

  [7/10] Wing Commander IV Turns 30... And Still Fascinates Me
    id:      arch-reddit-0002
    type:    product_archaeology
    status:  new
    source:  reddit_r_patientgamers
    description: Times flies. This was the first game that I was truly hyped to play as a kid. A space epic where you play as Mark Hamill (Luke Skywalker)? Sold!

On returning to it 30 years later, it certainly scratc
    score_breakdown:
      total_score: 7
      market_gap_score: 5
      build_feasibility: 9
      revenue_potential: 3
      urgency: 8
      why_now: 2026 marks the 30th anniversary of Wing Commander IV, providing a strong, timely hook for retrospective content and appealing to its enduring fanbase.
      recommended_action: BUILD
      effort_estimate: weeks
      revenue_estimate: NICHE
      top_risk: Limited appeal beyond the dedicated Wing Commander fanbase, making broad reach and significant engagement challenging.
    tags:    product_archaeology, reddit, patientgamers
    added:   2026-03-19T15:13:35.684362
    url:     https://reddit.com/r/patientgamers/comments/1rm4knt/wing_commander_iv_turns_30_and_still_fascinates_me/

  [7/10] Dymaxion Car
    id:      vint-0005
    type:    product_gap
    status:  new
    source:  
    description: Yes, there's still a market for highly fuel-efficient, aerodynamic, multi-purpose vehicles, though modern iterations differ greatly.
    score_breakdown:
      total_score: 7
      market_gap_score: 8
      build_feasibility: 3
      revenue_potential: 6
      urgency: 7
      why_now: The ongoing global shift towards electric vehicles and sustainable transportation makes highly efficient, aerodynamic, and flexible vehicle designs critically relevant for range optimization and utilitarian appeal.
      recommended_action: RESEARCH
      effort_estimate: months
      revenue_estimate: MEDIUM
      top_risk: Overcoming the inherent engineering challenges and historical safety stigma of the Dymaxion's radical design to produce a safe, stable, and affordable modern vehicle.
    tags:    product_archaeology, vintage, vintage-1930s
    added:   2026-03-19T15:16:03.025760

  [7/10] DeLorean DMC-12
    id:      vint-0015
    type:    product_gap
    status:  new
    source:  
    description: No, niche luxury and unique car markets continue to thrive with various high-performance and design-focused vehicles.
    score_breakdown:
      total_score: 7
      market_gap_score: 9
      build_feasibility: 6
      revenue_potential: 7
      urgency: 8
      why_now: 2026 is timely due to the mature state of EV platforms, the thriving market for unique luxury vehicles, and persistent cultural nostalgia for iconic 80s designs.
      recommended_action: PITCH
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Securing significant capital investment and navigating complex automotive manufacturing regulations for low-volume production.
    tags:    product_archaeology, vintage, vintage-1980s
    added:   2026-03-19T15:16:03.025780

  [7/10] 90s Green Day was pure chaos and I miss it.
    id:      nost-0024
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    score_breakdown:
      total_score: 7
      market_gap_score: 7
      build_feasibility: 8
      revenue_potential: 6
      urgency: 7
      why_now: 2026 aligns with the peak of 90s nostalgia and Green Day's continued relevance, tapping into a strong 'missing it' sentiment from an engaged fanbase.
      recommended_action: BUILD
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Failing to uncover truly new insights or perspectives beyond existing Green Day retrospectives.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783558
    url:     https://reddit.com/r/nostalgia/comments/1qx7agz/90s_green_day_was_pure_chaos_and_i_miss_it/

  [7/10] Remember when you didnâ€™t have to enter your personal info online to win a soda?
    id:      nost-0025
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    score_breakdown:
      total_score: 7
      market_gap_score: 7
      build_feasibility: 8
      revenue_potential: 5
      urgency: 6
      why_now: In 2026, increasing AI data demands and persistent privacy concerns will amplify the nostalgia for low-stakes, data-free interactions, making this topic highly resonant.
      recommended_action: PUBLISH
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Failing to move beyond anecdotal nostalgia to provide deeper insights or a compelling narrative about the societal shift.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783563
    url:     https://reddit.com/r/nostalgia/comments/d3zgv1/remember_when_you_didnt_have_to_enter_your/

  [7/10] I miss when actors looked like everyday people
    id:      nost-0026
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    score_breakdown:
      total_score: 7
      market_gap_score: 8
      build_feasibility: 8
      revenue_potential: 6
      urgency: 7
      why_now: The increasing homogenization of actor aesthetics, fueled by social media and evolving beauty standards, makes the nostalgia for 'everyday' looks more poignant and relevant for critical analysis in 2026.
      recommended_action: PUBLISH
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Analysis remaining superficial and failing to provide deep, novel insights beyond anecdotal observation.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783566
    url:     https://reddit.com/r/nostalgia/comments/1qthpux/i_miss_when_actors_looked_like_everyday_people/

  [7/10] Summer Sleepovers at the friends house who had a trampoline
    id:      nost-0030
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    description: In the early 80s, 82-84, i was ages 5-7, i used to sleep outside on a lounge/lawn chair, alone. I woke up one morning with a stray cat snuggled up with me. I wasnt allowed to keep it, and that made me
    score_breakdown:
      total_score: 7
      market_gap_score: 8
      build_feasibility: 9
      revenue_potential: 4
      urgency: 6
      why_now: Gen X and early Millennials, who experienced childhood in the 80s, are in their prime years for consuming and appreciating nostalgic content, making 2026 an ideal time to tap into this sentiment.
      recommended_action: PITCH
      effort_estimate: weeks
      revenue_estimate: SMALL
      top_risk: The specific nature of the memory might make it too niche for broad appeal, and its standalone monetization potential is low.
    tags:    product_archaeology, nostalgia, comment_signal
    added:   2026-03-19T15:20:25.783578
    url:     https://reddit.com/r/nostalgia/comments/1rgz8d7/summer_sleepovers_at_the_friends_house_who_had_a/

  [7/10] Historical Twins Division
    id:      historical-twins-division
    type:    division
    status:  new
    source:  gemini-session-2026-03-26
    description: Nightly scrape builds character data pools from historical figures. Three-bucket triage. Mirror Test validation. Static/Fluid toggle. Feeds CTW pipeline directly.
    score_breakdown:
      total_score: 7
      market_gap_score: 7
      build_feasibility: 6
      revenue_potential: 7
      urgency: 8
      why_now: The explosive growth in generative AI and demand for authentic, dynamic characters across gaming, education, and virtual experiences makes 2026 ideal for a validated historical character data pipeline.
      recommended_action: BUILD
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: The complexity and accuracy of inferring nuanced character data from historical sources, especially regarding 'Mirror Test validation' and mitigating historical biases.
    tags:    ctw, historical, pipeline, characters, nightly
    added:   2026-03-26

  [7/10] Ancient Tech Grading System
    id:      ancient-tech-grading
    type:    tool
    status:  new
    source:  gemini-session-2026-03-26
    description: Three-bucket system (Logical/Plausible/Reality-Flip) for evaluating ancient technologies and theories. Composite scoring. Ghost Book adjacent.
    score_breakdown:
      total_score: 7
      market_gap_score: 8
      build_feasibility: 8
      revenue_potential: 5
      urgency: 6
      why_now: As public interest in ancient mysteries and the demand for critical thinking tools intensify, 2026 is an opportune time to introduce a structured evaluation system for often-speculative theories.
      recommended_action: BUILD
      effort_estimate: weeks
      revenue_estimate: NICHE
      top_risk: Difficulty in establishing objective criteria and perceived authority, potentially leading to user disagreement or dismissal of the system's validity.
    tags:    ghost-book, grading, ancient-tech, scoring
    added:   2026-03-26

  [7/10] Institutional Twin Councils
    id:      institutional-twin-councils
    type:    platform+product
    status:  WHITEBOARD
    source:  Joe session — expanded from Historical Twins concept
    description: Domain-expert and institutional knowledge twins grouped by board, field, or regulatory function. Queryable on demand for proposal stress-testing, regulatory pre-review, legal argument testing, academic peer review, and product validation. Three tiers: public historical commons, curated domain councils, custom institutional twins. Replaces $500-5000/hr expert panels at near-zero marginal cost.
    score_breakdown:
      total_score: 7
      market_gap_score: 9
      build_feasibility: 4
      revenue_potential: 9
      urgency: 8
      why_now: The convergence of advanced AI capabilities with a pervasive market need for rapid, cost-effective expert insights makes 2026 an opportune moment to develop this concept.
      recommended_action: RESEARCH
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: Achieving sufficient AI reliability and institutional trust for high-stakes decision validation, coupled with acquiring sensitive proprietary institutional data.
    added:   2026-03-26

  [7/10] Creative Review Agent
    id:      creative-review-agent
    type:    agent+quality-control
    status:  WHITEBOARD
    source:  
    description: Routes creative output to domain-appropriate reviewer panels based on content type and subgenre. Full taxonomy built covering Comedy (10 subgenres), Drama, Horror, Sci-Fi, Fantasy, Romance, Thriller, Historical, Children/YA, Non-Fiction, Marketing, Screenplay, Music, Game, Educational. Weighted panels for blended content. Dissent protocol flags reviewer disagreements as data. Quality gate: PUBLISH/REVISE/REWORK/REJECT. Reference: creative-review-taxonomy.md
    score_breakdown:
      total_score: 7
      recommended_action: BUILD
      why_now: AI advancements enable robust content classification, streamlining crucial creative quality control now.
      effort_estimate: months
      revenue_estimate: MEDIUM
      top_risk: Scope creep and over-engineering for internal needs, leading to prolonged development time.
      score_breakdown: {'market_timing': 7, 'feasibility': 6, 'revenue_potential': 6, 'strategic_fit': 8}
    added:   2026-03-29

  [6/10] Google Glass
    id:      vint-0020
    type:    product_gap
    status:  new
    source:  
    description: No, while AR glasses are still being developed, mainstream adoption for general consumers remains elusive without solving the core issues.
    score_breakdown:
      total_score: 6
      market_gap_score: 9
      build_feasibility: 4
      revenue_potential: 10
      urgency: 8
      why_now: Continued advancements in AI, miniaturized displays, and sensor technology, coupled with growing consumer familiarity with wearables, create a more receptive environment for discreet AR glasses, making 2026 a critical time for foundational development.
      recommended_action: RESEARCH
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: Inability to overcome persistent social awkwardness, privacy concerns, and the lack of a killer, everyday consumer use case at a viable price point.
    tags:    product_archaeology, vintage, vintage-2010s
    added:   2026-03-19T15:16:03.025790

  [6/10] Remember when Pizza Hut had a buffet. Good times.
    id:      nost-0023
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    score_breakdown:
      total_score: 6
      market_gap_score: 8
      build_feasibility: 9
      revenue_potential: 4
      urgency: 3
      why_now: The core demographic that experienced the Pizza Hut buffet will still be highly active online in 2026, driving engagement with nostalgic content.
      recommended_action: PUBLISH
      effort_estimate: weeks
      revenue_estimate: SMALL
      top_risk: Content becoming generic or lost in the vast amount of existing nostalgic content.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783546
    url:     https://reddit.com/r/nostalgia/comments/1lgjctm/remember_when_pizza_hut_had_a_buffet_good_times/

  [6/10] Technical Council Peer Review
    id:      technical-council-review
    type:    testing-improvement
    status:  new
    source:  gemini-session-2026-03-26
    description: Load domain historical twins as adversarial reviewers for architecture decisions. Hamilton/Shannon/Kay/Hopper for system architecture. Better than generic AI scoring.
    score_breakdown:
      total_score: 6
      market_gap_score: 8
      build_feasibility: 3
      revenue_potential: 7
      urgency: 7
      why_now: The increasing sophistication of AI models in understanding and generating complex text makes simulating historical expert perspectives more viable, while current AI solutions often lack the nuanced domain-specific judgment this idea promises.
      recommended_action: RESEARCH
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: The immense technical challenge of accurately modeling and simulating the nuanced, adversarial architectural philosophies of complex historical figures in a practically useful and contextually relevant way.
    tags:    architecture, review, historical-twins, peer-review, council
    added:   2026-03-26

  [6/10] Parcel Mesh Network
    id:      parcel-mesh-network
    type:    proposal
    status:  WHITEBOARD
    source:  manual
    description: Distributed mesh network using parcel/property nodes. Federal funding path via FEMA/BRIC/HUD. Privacy-first architecture.
    score_breakdown:
      total_score: 6
      market_gap_score: 7
      build_feasibility: 4
      revenue_potential: 8
      urgency: 9
      why_now: Increasing climate-related disasters and the urgent need for resilient, decentralized communication infrastructure make 2026 ideal for securing federal funding aimed at disaster preparedness.
      recommended_action: PITCH
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: Securing widespread property owner adoption and managing the immense logistical complexities of decentralized deployment at scale.
    tags:    mesh, privacy, federal-funding, infrastructure, council-needed
    added:   2026-03-26

  [6/10] Vedic Math Build — Active Status
    id:      vedic-build-status
    type:    infrastructure
    status:  IN_PROGRESS
    source:  
    description: Stack B (_studio_vedic) staged and ready. Config G vector context wired in. Scan runs tonight at 2:30 AM to produce conversion manifest. Build agent spec complete. Kernel stubs written with shadow verification and ab-report logging. A/B dispatcher wires after manifest confirms scope.
    score_breakdown:
      total_score: 6
      recommended_action: BUILD
      why_now: Project is in active development, staged for immediate technical progression and testing.
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Significant investment in complex infrastructure without confirmed market demand for the end product.
      score_breakdown: {'market_timing': 5, 'feasibility': 8, 'revenue_potential': 3, 'strategic_fit': 6}
    added:   2026-03-29

  [5/10] Tucker Torpedo
    id:      vint-0008
    type:    product_gap
    status:  new
    source:  
    description: No, the automotive industry continues to innovate on safety and design, but the Tucker's forward-thinking approach was ahead of its time.
    score_breakdown:
      total_score: 5
      market_gap_score: 6
      build_feasibility: 3
      revenue_potential: 7
      urgency: 6
      why_now: The transformative shift to electric vehicle platforms and advanced manufacturing techniques in 2026 creates an unprecedented opportunity to revisit and implement radical safety and design philosophies like Tucker's.
      recommended_action: PITCH
      effort_estimate: months
      revenue_estimate: LARGE
      top_risk: Securing massive capital and navigating automotive regulatory compliance for a new vehicle concept.
    tags:    product_archaeology, vintage, vintage-1940s
    added:   2026-03-19T15:16:03.025767

  [5/10] Remember when yellow milk jugs were used to protect the milk from light?
    id:      nost-0027
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    score_breakdown:
      total_score: 5
      market_gap_score: 6
      build_feasibility: 9
      revenue_potential: 2
      urgency: 3
      why_now: The continuous churn of social media feeds and the evergreen appeal of niche historical facts make 2026 a suitable time for short-form content exploring forgotten product details.
      recommended_action: PUBLISH
      effort_estimate: days
      revenue_estimate: SMALL
      top_risk: Limited audience interest beyond a very specific nostalgic demographic, hindering significant engagement or standalone monetization.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783569
    url:     https://reddit.com/r/nostalgia/comments/1ry5aqw/remember_when_yellow_milk_jugs_were_used_to/

  [5/10] Vedic Math Computational Layer
    id:      vedic-math-layer
    type:    infrastructure+patent
    status:  WHITEBOARD
    source:  
    description: Software abstraction layer routing matrix operations, large integer multiplication, and vector similarity scoring to Vedic-optimized C extensions. Environment-aware portability wrapper with self-logging efficiency comparison. Real speedups on specific math-heavy operations. NOT a general token reducer. Genuine value in matrix ops and vector search.
    score_breakdown:
      total_score: 5
      recommended_action: RESEARCH
      why_now: AI/ML explosion drives demand for faster matrix/vector operations, creating market need.
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Vedic math optimizations might not provide significant, demonstrable speedups over existing highly optimized libraries.
      score_breakdown: {'market_timing': 8, 'feasibility': 2, 'revenue_potential': 7, 'strategic_fit': 4}
    added:   2026-03-29

  [4/10] I miss having that previous channel button on remotes
    id:      nost-0029
    type:    product_archaeology
    status:  new
    source:  reddit_r_nostalgia
    description: Bonus points for being able to successfully bounce between 3 shows while making sure your 2 favorite shows stayed on that button.
    score_breakdown:
      total_score: 4
      market_gap_score: 7
      build_feasibility: 4
      revenue_potential: 2
      urgency: 3
      why_now: As smart home platforms consolidate diverse media experiences, 2026 presents an opportunity to re-introduce seamless channel navigation across all content sources.
      recommended_action: PITCH
      effort_estimate: weeks
      revenue_estimate: NICHE
      top_risk: Reliance on third-party platform adoption and the declining relevance of traditional linear TV viewing.
    tags:    product_archaeology, nostalgia, reddit
    added:   2026-03-19T15:20:25.783575
    url:     https://reddit.com/r/nostalgia/comments/1rwvjis/i_miss_having_that_previous_channel_button_on/

  [3/10] Vedic AI Inference Operating System
    id:      vedic-ai-inference-os
    type:    infrastructure+patent+product
    status:  WHITEBOARD
    source:  
    description: Purpose-built lightweight OS optimized for AI inference workloads. Vedic arithmetic at kernel HAL level for memory allocation, process scheduling, and security hashing. Cascading efficiency — every process inherits faster math. GPU/CPU heat reduction via reduced switching activity.
    score_breakdown:
      total_score: 3
      recommended_action: RESEARCH
      why_now: AI inference demand is soaring, driving critical need for efficiency and heat reduction.
      effort_estimate: years
      revenue_estimate: LARGE
      top_risk: Extreme complexity of OS kernel development and unproven real-world benefits of Vedic math.
      score_breakdown: {'market_timing': 7, 'feasibility': 1, 'revenue_potential': 8, 'strategic_fit': 1}
    added:   2026-03-29

  [3/10] Vedic AI Upgrade as a Service
    id:      vedic-upgrade-service
    type:    service+patent+revenue
    status:  WHITEBOARD
    source:  
    description: Install Vedic CUDA kernel layer on client AI systems. Run concurrent 30-day shadow comparison — original stack vs Vedic stack on identical workloads. Generate client-specific before/after efficiency report showing exact dollar savings. Ghost page calculator as lead magnet. Provisional patent on concurrent shadow deployment architecture.
    score_breakdown:
      total_score: 3
      recommended_action: RESEARCH
      why_now: Rising AI compute costs demand efficiency, but 'Vedic' aspect needs scientific grounding.
      effort_estimate: years
      revenue_estimate: NICHE
      top_risk: Core 'Vedic CUDA' tech lacks scientific basis, making it unfeasible or incredible.
      score_breakdown: {'market_timing': 5, 'feasibility': 2, 'revenue_potential': 3, 'strategic_fit': 2}
    added:   2026-03-29

  [2/10] High-end consumer phonographs
    id:      vint-0006
    type:    product_gap
    status:  new
    source:  
    description: No, modern digital music players and streaming services have filled this gap more effectively and affordably for mass consumption.
    score_breakdown:
      total_score: 2
      market_gap_score: 1
      build_feasibility: 7
      revenue_potential: 1
      urgency: 1
      why_now: The overwhelming prevalence of superior digital and even modern analog (vinyl) audio formats means there is no compelling 'why now' for high-end consumer phonographs, unless targeting an extremely niche, museum-quality, bespoke collector's market.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Lack of market demand and a viable commercial ecosystem for the original phonograph media format.
    tags:    product_archaeology, vintage, vintage-1930s
    added:   2026-03-19T15:16:03.025762

  [2/10] Apple Newton
    id:      vint-0017
    type:    product_gap
    status:  new
    source:  
    description: No, the concept of a personal digital assistant was vastly improved and superseded by smartphones.
    score_breakdown:
      total_score: 2
      market_gap_score: 1
      build_feasibility: 8
      revenue_potential: 1
      urgency: 1
      why_now: There is no compelling 'why now' as the core concept has been fully integrated and surpassed by modern smartphones.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Market irrelevance due to current smartphones and tablets offering superior functionality and convenience.
    tags:    product_archaeology, vintage, vintage-1990s
    added:   2026-03-19T15:16:03.025784

  [1/10] The 'Autodynophone'
    id:      vint-0003
    type:    product_gap
    status:  new
    source:  
    description: No, modern digital music players have made such complex, single-purpose devices obsolete.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: There is no market-driven reason for 2026 to be the right time, as this product type is fundamentally obsolete due to modern digital alternatives.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Complete market irrelevance and lack of demand.
    tags:    product_archaeology, vintage, vintage-1920s
    added:   2026-03-19T15:16:03.025747

  [1/10] Early Automatic Dishwashers (e.g., 'Sanitor' brand)
    id:      vint-0004
    type:    product_gap
    status:  new
    source:  
    description: No, automatic dishwashers are now highly effective, affordable, and common household appliances.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: There is no 'why now' for building or publishing an 'Early Automatic Dishwasher' product, as the market is fully saturated with superior, affordable, and highly effective modern appliances.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: SMALL
      top_risk: Complete market indifference due to the existence of vastly superior, affordable, and widely adopted modern alternatives.
    tags:    product_archaeology, vintage, vintage-1920s
    added:   2026-03-19T15:16:03.025756

  [1/10] Automatic dishwashers (early models)
    id:      vint-0007
    type:    product_gap
    status:  new
    source:  
    description: No, modern dishwashers are efficient, affordable, and a common household appliance, completely filling the original need.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: There is no market demand for an inferior, early model dishwasher when modern appliances completely fulfill the need efficiently and affordably, making 2026 an irrelevant timeframe for this specific product concept.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Complete lack of market demand due to superior and cost-effective modern alternatives already available.
    tags:    product_archaeology, vintage, vintage-1930s
    added:   2026-03-19T15:16:03.025765

  [1/10] Ford Edsel
    id:      vint-0009
    type:    product_gap
    status:  new
    source:  
    description: No, the market for distinct mid-range family cars is well-served by numerous brands today, and consumer preferences have shifted significantly from the Edsel's concept.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: There is no compelling reason for a 2026 revival, as market preferences have fundamentally shifted away from the Edsel's concept and the segment is already well-served.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Complete market rejection and significant financial loss due to a mismatch with contemporary consumer preferences and market saturation.
    tags:    product_archaeology, vintage, vintage-1950s
    added:   2026-03-19T15:16:03.025769

  [1/10] Nuclear-Powered Cars (concept)
    id:      vint-0010
    type:    product_gap
    status:  new
    source:  
    description: No, while electric and alternative fuel vehicles are prevalent, the fundamental safety and logistical issues of personal nuclear propulsion remain too great to ever fill this conceptual gap.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 1
      revenue_potential: 1
      urgency: 1
      why_now: The fundamental safety, logistical, and ethical issues of personal nuclear propulsion remain too great to ever fill this conceptual gap, making 2026 an inappropriate time for consideration.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Catastrophic radiation exposure and contamination from accidents or failures.
    tags:    product_archaeology, vintage, vintage-1950s
    added:   2026-03-19T15:16:03.025771

  [1/10] Quadraphonic Sound
    id:      vint-0012
    type:    product_gap
    status:  new
    source:  
    description: No, the desire for immersive audio is now filled by surround sound and object-based audio technologies like Dolby Atmos.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 3
      revenue_potential: 1
      urgency: 1
      why_now: There is no compelling reason for Quadraphonic Sound to re-emerge in 2026, as modern immersive audio technologies like Dolby Atmos have far surpassed its capabilities and market adoption.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: The complete market saturation and technical superiority of current immersive audio formats (Dolby Atmos, DTS:X, etc.) make Quadraphonic Sound obsolete.
    tags:    product_archaeology, vintage, vintage-1970s
    added:   2026-03-19T15:16:03.025775

  [1/10] 8-Track Tapes
    id:      vint-0013
    type:    product_gap
    status:  new
    source:  
    description: No, convenient and portable music consumption is now filled by digital streaming services and improved physical formats.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 3
      revenue_potential: 1
      urgency: 1
      why_now: 2026 holds no unique circumstances or market shifts that would create demand for 8-track tapes, which were surpassed by superior formats decades ago.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Zero market demand due to vastly superior modern and existing retro alternatives.
    tags:    product_archaeology, vintage, vintage-1970s
    added:   2026-03-19T15:16:03.025777

  [1/10] New Coke
    id:      vint-0014
    type:    product_gap
    status:  new
    source:  
    description: No, the market for various cola formulations and brands is well-covered.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 8
      revenue_potential: 1
      urgency: 1
      why_now: There is no compelling reason why 2026 would be the right time to reintroduce New Coke as a sustainable product, given its original failure was due to strong consumer dislike for the taste, not timing.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Repeat of widespread consumer rejection and significant brand damage, echoing its original failure.
    tags:    product_archaeology, vintage, vintage-1980s
    added:   2026-03-19T15:16:03.025779

  [1/10] Betamax VCR
    id:      vint-0016
    type:    product_gap
    status:  new
    source:  
    description: No, physical media formats have largely been superseded by digital streaming and downloads.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 3
      revenue_potential: 1
      urgency: 1
      why_now: 2026 offers no unique advantages or market shifts that would make a new Betamax VCR viable, as digital media continues its dominance and original content for the format is non-existent.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Complete lack of market demand and the impossibility of economically sourcing or manufacturing obsolete components.
    tags:    product_archaeology, vintage, vintage-1980s
    added:   2026-03-19T15:16:03.025782

  [1/10] Virtual Boy
    id:      vint-0018
    type:    product_gap
    status:  new
    source:  
    description: No, modern VR headsets offer full color and far superior immersion, rendering the Virtual Boy's niche obsolete.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: Modern VR technology has rendered the Virtual Boy's original niche completely obsolete, making 2026 an irrelevant time for its revival.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Complete market irrelevance and strong negative brand association with eye strain and discomfort.
    tags:    product_archaeology, vintage, vintage-1990s
    added:   2026-03-19T15:16:03.025786

  [1/10] Microsoft Zune
    id:      vint-0019
    type:    product_gap
    status:  new
    source:  
    description: No, the market for dedicated portable music players has largely been superseded by smartphones and streaming services.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 5
      revenue_potential: 1
      urgency: 1
      why_now: There is no compelling market or technological shift in 2026 that would justify reviving a dedicated portable music player when smartphones dominate the listening experience.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: NICHE
      top_risk: Complete lack of market demand due to smartphone saturation and widespread adoption of streaming services.
    tags:    product_archaeology, vintage, vintage-2000s
    added:   2026-03-19T15:16:03.025787

  [1/10] HTC First (Facebook Phone)
    id:      vint-0021
    type:    product_gap
    status:  new
    source:  
    description: No, integrated social media operating systems or dedicated social phones did not become a trend and are not a modern gap.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: There is no discernible 'why now' as the market has decisively moved away from dedicated social media hardware in favor of apps on general-purpose smartphones.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: SMALL
      top_risk: Profound lack of user demand and inability to secure necessary deep OS-level integration with major social platforms.
    tags:    product_archaeology, vintage, vintage-2010s
    added:   2026-03-19T15:16:03.025792

  [1/10] Juicero
    id:      vint-0022
    type:    product_gap
    status:  new
    source:  
    description: No, while convenience in health food is desired, this specific, overpriced, non-functional solution is not a modern gap.
    score_breakdown:
      total_score: 1
      market_gap_score: 1
      build_feasibility: 2
      revenue_potential: 1
      urgency: 1
      why_now: The inherent flaws of Juicero, including its overpriced and unnecessary technology, remain unaddressed, making 2026 an inopportune time for its re-introduction.
      recommended_action: KILL
      effort_estimate: months
      revenue_estimate: SMALL
      top_risk: The product's fundamental lack of value proposition and extreme price for a task easily done by hand, leading to inevitable market rejection.
    tags:    product_archaeology, vintage, vintage-2010s
    added:   2026-03-19T15:16:03.025794

  [0/10] GitHub Trending: sponsors/explore
    id:      gh-sponsors-explore
    type:    github_trending
    status:  
    source:  
    description: Open-Source Frontier Voice AI
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: trending/developers
    id:      gh-trending-developers
    type:    github_trending
    status:  
    source:  
    description: TimesFM (Time Series Foundation Model) is a pretrained time-series foundation model developed by Google Research for tim
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: microsoft/VibeVoice
    id:      gh-microsoft-VibeVoice
    type:    github_trending
    status:  
    source:  
    description: A visual, example-driven guide to Claude Code — from basic concepts to advanced agents, with copy-paste templates that b
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: apps/github-copilot-cli
    id:      gh-apps-github-copilot-cli
    type:    github_trending
    status:  
    source:  
    description: Turn any PDF or image document into structured data for your AI. A powerful, lightweight OCR toolkit that bridges the ga
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: google-research/timesfm
    id:      gh-google-research-timesfm
    type:    github_trending
    status:  
    source:  
    description: The agent that grows with you
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: sponsors/luongnv89
    id:      gh-sponsors-luongnv89
    type:    github_trending
    status:  
    source:  
    description: Hunt down social media accounts by username across social networks
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: luongnv89/claude-howto
    id:      gh-luongnv89-claude-howto
    type:    github_trending
    status:  
    source:  
    description: A unified library of SOTA model optimization techniques like quantization, pruning, distillation, speculative decoding, 
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: PaddlePaddle/PaddleOCR
    id:      gh-PaddlePaddle-PaddleOCR
    type:    github_trending
    status:  
    source:  
    description: PyTorch building blocks for the OLMo ecosystem
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: apps/github-actions
    id:      gh-apps-github-actions
    type:    github_trending
    status:  
    source:  
    description: ⭐AI-driven public opinion &amp; trend monitor with multi-platform aggregation, RSS, and smart alerts.🎯 告别信息过载，你的 AI 舆情监控
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: NousResearch/hermes-agent
    id:      gh-NousResearch-hermes-agent
    type:    github_trending
    status:  
    source:  
    description: ChatDev 2.0: Dev All through LLM-powered Multi-Agent Collaboration
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: sherlock-project/sherlock
    id:      gh-sherlock-project-sherlock
    type:    github_trending
    status:  
    source:  
    description: A framework for building, orchestrating and deploying AI agents and multi-agent workflows with support for Python and .N
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: NVIDIA/Model-Optimizer
    id:      gh-NVIDIA-Model-Optimizer
    type:    github_trending
    status:  
    source:  
    description: Supercharge Your LLM with the Fastest KV Cache Layer
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: allenai/OLMo-core
    id:      gh-allenai-OLMo-core
    type:    github_trending
    status:  
    source:  
    description: A python CAD programming library
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: sansan0/TrendRadar
    id:      gh-sansan0-TrendRadar
    type:    github_trending
    status:  
    source:  
    description: Netflix-level subtitle cutting, translation, alignment, and even dubbing - one-click fully automated AI video subtitle t
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: OpenBMB/ChatDev
    id:      gh-OpenBMB-ChatDev
    type:    github_trending
    status:  
    source:  
    description: Convert documentation websites, GitHub repositories, and PDFs into Claude AI skills with automatic conflict detection
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: MervinPraison/PraisonAI
    id:      gh-MervinPraison-PraisonAI
    type:    github_trending
    status:  
    source:  
    description: GLM-OCR: Accurate × Fast × Comprehensive
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: apps/claude
    id:      gh-apps-claude
    type:    github_trending
    status:  
    source:  
    description: We write your reusable computer vision tools. 💜
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: yusufkaraaslan/Skill_Seekers
    id:      gh-yusufkaraaslan-Skill_Seekers
    type:    github_trending
    status:  
    source:  
    description: Use claude-code for free in the terminal, VSCode extension or via discord like openclaw
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: zai-org/GLM-OCR
    id:      gh-zai-org-GLM-OCR
    type:    github_trending
    status:  
    source:  
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: roboflow/supervision
    id:      gh-roboflow-supervision
    type:    github_trending
    status:  
    source:  
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: apps/pre-commit-ci
    id:      gh-apps-pre-commit-ci
    type:    github_trending
    status:  
    source:  
    tags:    github, trending, python
    added:   

  [0/10] GitHub Trending: Alishahryar1/free-claude-code
    id:      gh-Alishahryar1-free-claude-code
    type:    github_trending
    status:  
    source:  
    tags:    github, trending, python
    added:   


## STUDIO CURRENT STATE

  ERROR: [Errno 2] No such file or directory: 'G:/My Drive/Projects/_studio\\state.json'

---
End of context. Generated: 2026-04-03 10:05