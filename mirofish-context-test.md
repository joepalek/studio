# MIROFISH CONTEXT TEST — Full Framework
# Finding the best shared context architecture
# for sidebar + Claude.ai + Claude Code
# Generated: 2026-03-26

---

## THE PROBLEM

Three interfaces need to share one brain:
- Opera Sidebar (sidebar-agent.html via localhost)
- Claude.ai (web chat, this conversation)
- Claude Code (VS Code terminal sessions)

Each one currently starts fresh. No shared memory.
Session gaps, rate limits, and context resets destroy continuity.

Known failure points:
1. Session handoff — close Opera, reopen next day, context gone
2. Cross-interface — Claude Code doesn't know what Opera discussed
3. Stale context — studio-context.md gets outdated between regenerations
4. Token waste — injecting 11,000 word context on every message
5. Inbox drift — multiple inbox files get out of sync
6. Rate limit gaps — overnight tasks fail silently, nobody knows
7. Decision loss — decisions made in one interface invisible to others

---

## THE 8 CONFIGURATIONS TO TEST

### Config A — Current Approach (baseline)
Method: studio-context.md manually injected at session start
Interfaces: all three read the same file manually

Strengths: simple, already exists, works for Claude Code
Weaknesses: manual, stale, token-heavy, doesn't survive gaps
Failure mode: user forgets to inject, or context is 3 days old

Safety net: auto-regenerate on session start via generate-context.py

### Config B — Structured Files (CLAUDE.md + handoff)
Method: CLAUDE.md rules + session-handoff.md + decision-log.json
All three interfaces read these three files at session start

Strengths: already partially built, lightweight, Git-tracked
Weaknesses: still manual load, handoff file needs discipline to write
Failure mode: handoff not written at session end

Safety net: nightly-rollup writes handoff automatically
Safety net 2: CLAUDE.md standing rule enforces end-of-session write

### Config C — Supabase Live State (shared DB)
Method: All three interfaces read/write to Supabase tables
Tables: system_state, inbox_items, decisions, session_log
Real-time sync — change in one interface visible to all immediately

Strengths: truly real-time, survives any session gap
Weaknesses: requires API calls, costs money at scale, latency
Failure mode: Supabase down, network issues, auth expiry

Safety net: fallback to local JSON files if Supabase unreachable
Safety net 2: sync local files TO Supabase on connect

### Config D — Git as Source of Truth
Method: _studio repo is the shared brain
All three interfaces commit/pull before reading state
State lives in JSON files, Git tracks all changes

Strengths: free, auditable, already exists, offline capable
Weaknesses: requires git pull before reading, merge conflicts possible
Failure mode: dirty working tree, merge conflict blocks reads

Safety net: read-only pull never causes conflicts
Safety net 2: separate read-only branch for context, writes go to main

### Config E — Hybrid (RECOMMENDED TO TEST FIRST)
Method: Three-layer system
Layer 1 (permanent rules): CLAUDE.md — never changes, injected always
Layer 2 (session state): session-handoff.md — updated each session
Layer 3 (live data): Supabase for inbox + decisions only (not full context)

Strengths: rules are stable, session state is lightweight,
          only dynamic data hits Supabase
Weaknesses: three systems to maintain
Failure mode: any one layer fails

Safety net: each layer degrades gracefully without the others
Safety net 2: layer 3 falls back to local JSON if Supabase down

### Config F — Compressed Context Injection
Method: studio-context.md compressed to under 2,000 tokens
Key facts only: project list, completion %, last decision, active blockers
Injected on every message automatically (not manually)

Strengths: always current, low token cost, automatic
Weaknesses: loses detail, summary may miss important context
Failure mode: compression loses critical context

Safety net: full context available on demand via FILES tab
Safety net 2: escalation keywords trigger full context load

### Config G — Vector Memory (local RAG)
Method: Ollama + local embedding model
All sessions, decisions, project notes stored as vectors
Query on session start: "what do I need to know right now?"

Strengths: scales infinitely, semantic search, truly intelligent recall
Weaknesses: complex setup, requires Ollama running, latency
Failure mode: Ollama down, embedding model not loaded

Safety net: fall back to Config B if Ollama unavailable
Safety net 2: pre-warm embeddings on machine startup

### Config H — Claude Memory System
Method: Use Claude.ai's built-in memory (now available free)
Key system facts stored as Claude memories
Combined with CLAUDE.md for Claude Code sessions

Strengths: native to Claude.ai, no extra infrastructure
Weaknesses: only works in Claude.ai, not Claude Code or sidebar
Failure mode: memories not portable to other interfaces

Safety net: export memories to CLAUDE.md periodically
Safety net 2: use as supplement to Config E, not replacement

---

## SCORING CRITERIA (rate each config 1-10 per dimension)

1. SURVIVAL — survives 24h session gap with no human intervention
2. CROSS-INTERFACE — change in one interface visible to others
3. TOKEN COST — how many tokens does maintaining context cost per message
4. STALENESS — how quickly does context go out of date
5. SETUP COMPLEXITY — how hard to implement and maintain
6. FAILURE RECOVERY — how gracefully does it fail and recover
7. OFFLINE CAPABLE — works without internet (local-first)
8. SCALABILITY — still works when system has 50 projects instead of 13

Max score per config: 80

---

## THE TEST PROTOCOL

### Round 1 — Individual Config Tests
For each config:

Test 1 — SESSION GAP
  Setup: inject context, have conversation, close all interfaces
  Wait: 1 hour (simulated 24h gap)
  Reopen: does the next session know what happened before?
  Score: 0 (no memory) to 10 (full memory)

Test 2 — CROSS-INTERFACE SYNC  
  Setup: make a decision in Claude Code
  Check: does sidebar show that decision without manual refresh?
  Check: does Claude.ai know about it in next message?
  Score: 0 (no sync) to 10 (instant sync)

Test 3 — STALE DETECTION
  Setup: inject context from 48 hours ago
  Ask: "what's the most recent thing we worked on?"
  Check: does the AI know its context is stale?
  Score: 0 (confidently wrong) to 10 (flags staleness correctly)

Test 4 — FAILURE RECOVERY
  Setup: simulate the config's primary failure mode
  Check: does it fall back gracefully?
  Check: does it recover automatically when issue resolves?
  Score: 0 (complete failure) to 10 (seamless recovery)

Test 5 — TOKEN EFFICIENCY
  Measure: tokens used per message for context maintenance
  Target: under 500 tokens per message for context overhead
  Score: 0 (>3000 tokens) to 10 (<200 tokens)

### Round 2 — Hybrid Testing
Take top 2-3 configs from Round 1
Combine their strengths
Run all 5 tests again on hybrids
Document what broke and why

### Round 3 — Stress Testing
Take winner from Round 2
Run for 3 simulated days:
  Day 1: normal usage (multiple sessions, overnight run)
  Day 2: failure injection (kill Ollama, corrupt handoff file, rate limit)
  Day 3: recovery validation (does it come back clean?)

---

## IMPLEMENTATION PLAN

### Phase 1 — Build test harness (Claude Code)
Create: context-test-harness.py
  - Implements all 8 configs as loadable modules
  - Runs all 5 tests against each config
  - Scores automatically where possible
  - Writes results to context-test-results.json

Create: context-test-results.json seed file

### Phase 2 — Run Round 1
Load harness, run all 8 configs through 5 tests
Generate scored comparison table
Identify top 3 configs

### Phase 3 — Build hybrids
Based on Round 1 findings, build 2-3 hybrid configs
Re-run tests

### Phase 4 — Stress test winner
Run 3-day simulation on winning config
Document all failure points
Add safety nets for each failure

### Phase 5 — Implement winner
Update CLAUDE.md with winning architecture
Update sidebar to use winning context method
Update run-agent.py to use winning context method
Document in decision-log.json as permanent architectural decision

---

## EXPECTED WINNER HYPOTHESIS

Based on analysis before testing, Config E (Hybrid) is most likely to win:
- CLAUDE.md for permanent rules (zero tokens, always injected)
- session-handoff.md for session state (lightweight, 200-300 tokens)
- Supabase for live inbox/decisions only (targeted, not full context)
- Git pull before read (free, offline-capable fallback)

But this is a hypothesis. The test may reveal surprises.
The Mirofish protocol finds the truth regardless of hypothesis.

---

## OUTPUT FILES

context-test-harness.py — test runner
context-test-results.json — scored results per config per test
context-test-round2.json — hybrid config results
context-stress-test.json — 3-day stress test results
context-winner.md — final recommendation with implementation plan
decision-log.json entry — permanent architectural decision record
