# Pool Job Creator — v1.0 Design Specification
# Author: Joe Palek | Studio | Generated: 2026-04-02
# Status: DESIGN DOC — not yet built

---

## WHAT THIS IS

An autonomous overnight agent that works through the 100-pool catalog,
builds new Tier 1 pipeline agents, runs them through a battery of tests,
and queues them for human review.

NOT a deploy-to-market system. NOT autonomous publishing.
Everything passes through a human approval gate before going live.

The pipeline is: BUILD → TEST → REVIEW → APPROVE → SCHEDULE
You are the gate between TEST and APPROVE. Nothing ships without you.

---

## THE PROBLEM IT SOLVES

Currently: Each pool agent is hand-built in a session (30-60 min each).
With 100 pools in the catalog, that's 50-100 hours of manual work.

Pool Job Creator turns that into:
  - 15 min to spec a new pool (CONFIG values + source URL)
  - Overnight: builder runs, tests, queues for review
  - 15 min the next morning: you review the output, approve or reject
  - Total human time per pool: ~30 min instead of 60+

---

## ARCHITECTURE — 4 LAYERS

### Layer 1: Pool Catalog (input)
File: pool_catalog.json
Contains all 100+ pools with:
  - pool_id, pool_number, pool_name
  - source_url, source_format, cadence
  - priority (1-5), status (queued/building/testing/review/approved/live/killed)
  - data_category (commodity/geopolitical/financial/climate/trade)
  - expected_fields: list of fields to extract
  - sellability_score (1-10, set after first successful run)
  - notes

### Layer 2: Pool Job Creator Agent (builder)
File: agents/pool_job_creator.py
Runs: nightly at 01:30 via \Studio\PoolJobCreator
Does:
  1. Reads pool_catalog.json — finds next N pools with status=queued
  2. For each pool: generates fetch_raw() + parse_raw() via Claude Code
  3. Copies tier1_pipeline_template.py → agents/{pool_id}.py
  4. Fills CONFIG block from catalog values
  5. Writes the fetch and parse implementations
  6. Runs battery of tests (Layer 3)
  7. Writes result to pool_catalog.json + review queue

### Layer 3: Test Battery (quality gate)
File: pool_test_battery.py
Run automatically by creator, also callable standalone:
  python pool_test_battery.py --pool {pool_id}

### Layer 4: Review Queue (human gate)
File: data/review-queue.json
You check this. Approve or reject each pool.
Approved → registers to Task Scheduler, status=live
Rejected → status=killed + reason logged

---

## THE TEST BATTERY — 8 TESTS

Every pool must pass all 8 before reaching your review queue.
Any failure = status set to "failed" + failure reason logged.
You can override a failed pool manually if you choose.

### T1 — FETCH TEST
Can the agent actually get the data?
  - Attempts fetch_raw() with 3 retries
  - Validates response is non-empty (> 500 bytes)
  - Validates response is the right format (JSON/XML/CSV/PDF parses without error)
  - PASS: data fetched and parseable
  - FAIL: network error, auth error, empty response, format mismatch

### T2 — PARSE TEST (Codd gate)
Does parse_raw() return structured records?
  - Runs parse_raw() on fetched data
  - Validates record count > 0
  - Validates at least 60% of expected_fields populated across records
  - Validates no field contains obviously wrong data (dates in number fields, etc.)
  - PASS: records > 0, fields > 60% populated
  - FAIL: empty parse, <60% fields, schema mismatch

### T3 — PLAUSIBILITY TEST
Are the numbers sane?
  - For numeric fields: check values are within order-of-magnitude of known ranges
  - For date fields: check dates are within last 5 years
  - For text fields: check language is English (or expected language)
  - Flags (not fails) values that look suspicious — human reviews flags
  - PASS: no implausible values detected
  - WARN: suspicious values flagged for human review
  - FAIL: >25% of values implausible

### T4 — CONSISTENCY TEST
Does the data change month over month as expected?
  - Fetches data on two consecutive runs (or uses cached run)
  - Compares checksums — if identical on a non-monthly source, flags as stale
  - For monthly sources: verifies data has changed from prior cached version
  - PASS: data changes as expected for cadence
  - FAIL: data never changes (dead source), or changes every second (unstable)

### T5 — DUAL AI SIGNAL TEST
Do Mistral and Gemini agree on the directional signal?
  - Runs full normalization + synthesis on parsed data
  - Extracts directional call from both models
  - CONSENSUS: both agree → signal confidence = high
  - DIVERGENT: disagree → signal confidence = low, flags for human review
  - Note: DIVERGENT is not a hard fail — some pools legitimately have mixed signals
  - PASS: consensus OR divergent with plausible reason
  - FAIL: both models return FAILED/ERROR

### T6 — TREND DETECTION TEST
Can we see signal patterns over time?
  - Fetches last 3 available data points (3 months for monthly, 3 weeks for weekly)
  - Runs synthesis on each
  - Checks if directional calls vary (all NEUTRAL = low signal pool)
  - Scores trend detectability: HIGH/MEDIUM/LOW
  - PASS: at least one non-NEUTRAL signal in 3 runs
  - WARN: all NEUTRAL — may be low-signal pool, flagged for human review
  - FAIL: cannot fetch historical data at all

### T7 — SELLABILITY SCORING
Is this data worth paying for?
  Automated scoring on 5 dimensions (1-10 each):
  - Freshness: How often does data update? (daily=10, annual=2)
  - Uniqueness: Is this freely available elsewhere? (exclusive=10, everywhere=2)
  - Signal clarity: Do AI models produce clear directional calls? (consensus=10, always neutral=2)
  - Audience size: How many buyers need this? (broad=10, niche=2)
  - Reliability: Did T1-T6 all pass cleanly? (all pass=10, warnings=6, fails=2)
  Total sellability score = weighted average (max 10)
  Threshold: score >= 6 → recommend Pro tier, >= 8 → recommend Institutional

### T8 — SCHEMA VALIDATION
Does the output conform to Tier 1 standards?
  - Validates state.json written correctly after dry run
  - Validates daily-digest.json entry added
  - Validates log file written with no ERROR lines
  - Validates output JSON has required fields: agent_id, classification, synthesis, commodities
  - PASS: all schema checks green
  - FAIL: missing fields, malformed JSON, ERROR in logs

---

## REVIEW QUEUE FORMAT

After passing the test battery, each pool lands here:
File: data/review-queue.json

Each entry contains:
{
  "pool_id":          "acled-conflict",
  "pool_number":      47,
  "pool_name":        "ACLED Armed Conflict Event Data",
  "status":           "AWAITING_REVIEW",
  "queued_at":        "2026-04-03T02:45:00",
  "test_results": {
    "T1_fetch":       "PASS",
    "T2_parse":       "PASS",
    "T3_plausibility":"WARN — 3 date values look suspicious",
    "T4_consistency": "PASS",
    "T5_dual_ai":     "CONSENSUS — both BEARISH",
    "T6_trend":       "HIGH — clear signal variation over 3 runs",
    "T7_sellability":  8.2,
    "T8_schema":      "PASS"
  },
  "sample_synthesis": "Corn Belt conflict events up 12% this month...",
  "sample_records":   3,
  "recommended_tier": "Institutional",
  "agent_file":       "agents/acled-conflict.py",
  "human_decision":   null,   // set to "APPROVE" or "REJECT"
  "rejection_reason": null,
  "approved_at":      null
}

---

## YOUR REVIEW WORKFLOW

You will get a Supervisor inbox notification each morning:
  "Pool Job Creator: 3 pools ready for review"

You open review-queue.json (or a future sidebar panel) and for each pool:

  APPROVE → pool moves to status=approved
            → scheduler XML generated automatically
            → schtasks /Create runs automatically
            → status becomes "live" next morning after first overnight run
            → you get a notification with the first real output

  REJECT  → status=killed
           → you write a brief reason (helps train future pool selection)
           → pool removed from overnight runs

  HOLD    → status=hold
           → pool stays in queue, not built yet
           → useful when: "good idea, wrong time, revisit in 60 days"

---

## WHAT THE CREATOR AGENT DOES NOT DO

To be explicit about the boundaries:

  ✗ Does NOT publish to Beehiiv automatically
  ✗ Does NOT contact customers
  ✗ Does NOT price or sell anything
  ✗ Does NOT approve its own pools
  ✗ Does NOT deploy to production without your explicit APPROVE

  ✓ Builds the agent code
  ✓ Runs all 8 tests
  ✓ Scores sellability
  ✓ Queues for your review
  ✓ After your APPROVE: registers to scheduler
  ✓ After first live run: sends you the output for final sanity check

---

## POOL CATALOG STATUS STATES

queued      → in catalog, waiting to be built
building    → creator agent is working on it right now
testing     → test battery running
review      → awaiting your decision
approved    → you said yes, scheduler registered
live        → running overnight, producing data
hold        → paused, revisit later
killed      → rejected, not being built
failed      → test battery failed, needs manual intervention

---

## PHASE PLAN

### Phase 0 — Foundation (build now)
  - pool_catalog.json — populate with first 20 pools from existing list
  - pool_test_battery.py — standalone test runner
  - Review queue format finalized

### Phase 1 — Manual Builder (next session)
  - You manually spec 5 pools in pool_catalog.json
  - Run pool_test_battery.py on each manually
  - Prove the test framework works before automating the build step
  - Review queue UI in sidebar (simple JSON viewer with APPROVE/REJECT buttons)

### Phase 2 — Automated Builder (after Phase 1 validated)
  - pool_job_creator.py — overnight agent
  - Takes queued pools, generates fetch_raw() + parse_raw() via AI
  - Runs battery automatically
  - Supervisor notification on completion

### Phase 3 — Sellability Intelligence (after 10+ live pools)
  - Pattern recognition across pool results
  - "This pool correlates with that pool" cross-validation chains
  - Automated pitch deck generation per pool for subscriber outreach
  - You get: "Pool X has 6 months of data, sellability 8.4, here's the one-pager"

---

## BEHAVIORAL RULES (CLAUDE.md compliance)

Pike:       Test battery runs the minimum tests needed — no over-engineering
Gall:       Builder evolves from tier1_pipeline_template.py — no new framework
Hamilton:   Every test has a timeout — battery aborts at 20 min total
Bezos:      Fetch tests have 3-attempt circuit breaker
Codd:       T2 enforces blank-over-wrong on all parsed fields
Shannon:    Review queue entries capped at 200 tokens per pool summary
Kay:        Creator sends goals (test this pool) not scripts (here is exact code)
Hopper:     Every pool tracks pull_timestamp + checksum from first run

---

## USDA PSD EMAIL — ALTERNATE CONTACT

The fas.opendata@fas.usda.gov address bounced. Correct paths:
  1. Web form: https://www.fas.usda.gov/contact (select "Data and Statistics")
  2. Try the API again in 48hrs — api.data.gov keys sometimes need propagation time
  3. If still 403 after 48hrs: fall back to web form

The PSD integration code is already written and waiting.
No action needed in the pipeline — it will auto-activate when the key works.

---

## NEXT ACTIONS (priority order)

1. Try PSD API again in 48hrs before submitting web form
2. Build pool_catalog.json with first 20 pools (this session or next)
3. Build pool_test_battery.py — standalone, manually triggered
4. Test battery against wasde-parser (already live — prove the framework)
5. Add sidebar panel: review queue viewer with APPROVE/REJECT
6. Then: pool_job_creator.py overnight builder

---
# END OF SPEC
# File: G:\My Drive\Projects\_studio\POOL_JOB_CREATOR_SPEC.md
# Next session: "Read STUDIO_BRIEFING.md then POOL_JOB_CREATOR_SPEC.md"
