---

## CONSTITUTIONAL PRINCIPLES — ALL AGENTS INHERIT THESE

### Rob Pike's 5 Rules

1. You cannot tell where a system will spend its time — do not over-architect
2. Measure before optimizing — verify the problem exists before solving it
3. Fancy algorithms are slow when n is small — prefer simple direct solutions
4. Fancy algorithms are buggier — complexity is a liability not an asset
5. Model data structures correctly first — logic follows naturally

### Gall's Law

A complex system that works evolved from a simple system that worked.
Never build complex from scratch. Build simple, prove it works, then grow it.

### YAGNI

You Aren't Gonna Need It.
Do not build features not explicitly requested. Scope creep is a failure mode.

### Kernighan's Law

Debugging is twice as hard as writing code.
If you write it as cleverly as possible you are by definition not smart enough
to debug it. Write obviously correct code, not impressively clever code.

### Unix Rule — Single Responsibility Per Component

Each component does one thing well.
Composed sequentially, each clean component gets you further than one
complex component that does everything poorly.

### Codd's Data Integrity

Model data correctly before writing logic.
Null handling must be explicit. Data independence must be maintained.
Do not let application logic corrupt data structure integrity.

---

## PRE-WRITE VERIFICATION GATE

Before writing ANY file to /projects/, /agents/*.md, /outputs/, studio.html:

1. Run file content through stress-tester.md analysis
2. Report findings in chat before writing
3. Wait for explicit approval: "approved", "go", or "write it"
4. Only then execute the write
Exceptions: state.json updates, log appends, heartbeat entries — write directly
Override: user says "fast write" or "skip stress test"

## POST-WRITE VERIFICATION GATE

After writing any non-exception file:

1. Run stress-tester.md review on the written file
2. Log result to stress-log.json with timestamp, file, findings count, pass/fail
3. If failures found: create inbox item with findings before proceeding

## NO CHAT BUILDS DIRECTIVE

Claude chat is for planning, decisions, and directives only.
Claude Code is the builder. All file creation and code writing
happens in Claude Code, never as chat artifacts.
If a build is needed, produce a Claude Code prompt. Do not build inline.

## DECISION LOG

Every standing architectural or process decision must be logged to decision-log.json.

Format per entry:

```json
{
  "id": "DEC-YYYYMMDD-NNN",
  "date": "YYYY-MM-DD",
  "decision": "one sentence — what was decided",
  "reason": "why — the constraint or tradeoff that drove it",
  "permanence": "permanent|revisable|temporary",
  "status": "active|superseded",
  "superseded_by": null
}
```

Log when:

* A tool, library, or API is chosen over alternatives
* A pattern is established (e.g., "atomic writes via tmp+rename")
* A direction is explicitly rejected (log what was rejected and why)
* Any decision whose reversal would require significant rework

Do NOT log: one-off implementation choices, variable names, minor formatting decisions.

## SYSTEM TIGHTNESS REVIEW

Run this question at the start of every 5th session, or any time Joe asks:

"What gaps exist between what the system knows about itself,
what I know about the system, and what is actually true on disk?
What has drifted, broken silently, or been assumed but not verified?"

Steps:

1. Read heartbeat-log.json, status.json, nit-results.json, session-handoff.md
2. Check for: stale state files, agents that haven't run, broken file references,
   schema mismatches, log files that are empty when they shouldn't be
3. Write findings to supervisor-inbox.json with tag: SYSTEM-REVIEW
4. Flag anything that would prevent reliable session handoff
5. Update session-handoff.md with: "System tightness last reviewed: [date] — [verdict]"

---

## SHANNON RULE [ENFORCED]

**Behavioral intent:** session-handoff.md must be under 200 tokens — write only the delta.
**Structural enforcement:** Supervisor MUST run token counter on session-handoff.md before
every write. Implementation: use tiktoken or len(text.split()) * 1.3 as proxy.
Gate: if token count > 200, BLOCK write, force truncation to delta only, log violation
to error-log.json. A handoff that ships bloated is a constraint violation — not a warning.

Violation format (error-log.json):
```json
{ "rule": "SHANNON", "file": "session-handoff.md", "tokens": N, "action": "blocked_truncated", "ts": "..." }
```

**Bypass:** None. No override path. Shannon is always enforced.

---

## HAMILTON RULE [ENFORCED]

**Behavioral intent:** Every scheduled task must have a TTL watchdog. Silent hangs are worse
than loud failures.
**Structural enforcement:** Every agent script that runs via Task Scheduler MUST declare
expected_runtime_seconds in its header comment AND wrap its main loop in a TTL decorator.

Required wrapper pattern:
```python
import signal, time, json
from datetime import datetime

def ttl_watchdog(expected_seconds, task_name):
    def handler(signum, frame):
        entry = {"rule": "HAMILTON", "task": task_name,
                 "expected_s": expected_seconds, "action": "aborted", "ts": datetime.now().isoformat()}
        with open("G:/My Drive/Projects/_studio/error-log.json", "a") as f:
            f.write(json.dumps(entry) + "\n")
        raise SystemExit(f"HAMILTON: {task_name} exceeded TTL of {expected_seconds}s — aborted")
    signal.signal(signal.SIGALRM, handler)  # Linux/Mac
    signal.alarm(int(expected_seconds * 1.5))  # 50% grace on top of expected
```

On Windows (no SIGALRM): use subprocess timeout parameter or threading.Timer.
TTL values must be declared as: `# EXPECTED_RUNTIME_SECONDS: 300`
Any agent missing TTL declaration is flagged by SRE-scout as HAMILTON_MISSING.

---

## HOPPER RULE [ENFORCED]

**Behavioral intent:** Every write to any *-inbox.json must conform to schema. Bad writes
log loudly, never pass silently.
**Structural enforcement:** All inbox writes MUST pass Pydantic schema validation before
reaching disk. No raw dict writes to inbox files permitted.

Required schema (minimum):
```python
from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class InboxItem(BaseModel):
    id: str
    source: str
    type: str
    urgency: Literal["low", "medium", "high", "critical"]
    title: str
    finding: str
    status: Literal["pending", "resolved", "expired"]
    date: str  # ISO format

def validated_inbox_write(item: dict, inbox_path: str):
    try:
        validated = InboxItem(**item)
    except Exception as e:
        error = {"rule": "HOPPER", "inbox": inbox_path, "error": str(e),
                 "rejected_item": item, "ts": datetime.now().isoformat()}
        with open("G:/My Drive/Projects/_studio/error-log.json", "a") as f:
            f.write(json.dumps(error) + "\n")
        raise ValueError(f"HOPPER VIOLATION: inbox write rejected — {e}")
    # Only reaches here if valid
    append_to_inbox(inbox_path, validated.dict())
```

Any inbox write that bypasses validation is a Hopper violation.
SRE-scout checks for raw dict writes weekly.

---

## KAY RULE [ENFORCED]

**Behavioral intent:** Supervisor sends goals, not scripts. Agents decide their own
execution path.
**Structural enforcement:** All supervisor directives MUST pass a directive validator
before dispatch to any agent. Forbidden patterns are blocked at send time — not caught
in post-hoc review.

Validator logic:
```python
import re, json
from datetime import datetime

FORBIDDEN_PATTERNS = [
    r'\bthen\b', r'\bnext\b', r'\bstep \d', r'\bdo the following\b',
    r'\brun .+\.py\b', r'\bexecute\b', r'\bfollow these steps\b'
]
REQUIRED_FIELDS = ["GOAL:", "SCOPE:", "SUCCESS_CRITERIA:"]

def validate_directive(directive_text: str, agent_name: str) -> bool:
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, directive_text, re.IGNORECASE):
            violations.append(f"forbidden_pattern: {pattern}")
    for field in REQUIRED_FIELDS:
        if field not in directive_text:
            violations.append(f"missing_field: {field}")
    if violations:
        entry = {"rule": "KAY", "agent": agent_name, "violations": violations,
                 "directive_preview": directive_text[:200], "ts": datetime.now().isoformat()}
        with open("G:/My Drive/Projects/_studio/error-log.json", "a") as f:
            f.write(json.dumps(entry) + "\n")
        raise ValueError(f"KAY VIOLATION: directive blocked — {violations}")
    return True
```

A directive blocked by Kay requires human approval before any retry.
No automatic reformulation by supervisor.

---

## CODD EXTRACTION RULE [ENFORCED]

**Behavioral intent:** Extraction tasks must be grounded only. No inference, no gap-filling.
Confidence < 95% is treated as blank.
**Structural enforcement:** All extraction functions in scope must be wrapped in the
Codd validation decorator. Unwrapped extraction functions are flagged by SRE-scout.

Scope: hibid-analyzer, arbitrage-pulse, listing-optimizer, ai_scout, ghost-book,
ai-intel-agent, market-scout, vintage-agent, product-archaeology, wayback-cdx,
job-source-crawler.
Does NOT apply to: reasoning, planning, code generation, conversational tasks.

Required decorator:
```python
import functools, json
from datetime import datetime

def codd_gate(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        violations = []
        for field, data in result.items():
            if data.get("confidence", 1.0) < 0.95 and not data.get("override_by_human"):
                violations.append(field)
                result[field]["value"] = None
                result[field]["codd_blocked"] = True
        if violations:
            entry = {"rule": "CODD", "function": func.__name__, "blocked_fields": violations,
                     "ts": datetime.now().isoformat()}
            with open("G:/My Drive/Projects/_studio/error-log.json", "a") as f:
                f.write(json.dumps(entry) + "\n")
        return result
    return wrapper
```

Output format (tabular — unchanged):
| Field Name | Value | Source | Evidence | Reason (if blank) |

Rules (unchanged, now enforced structurally):
1. GROUNDING ONLY — extract only values explicitly stated in source
2. BLANK OVER WRONG — missing/ambiguous values left blank
3. SOURCE LABEL — every value tagged Extracted or Inferred
4. EVIDENCE REQUIRED — every value includes exact quote or reference
5. REASON FOR BLANK — every blank field gets one-sentence explanation
6. CONFIDENCE GATE — confidence < 95% treated as blank, not inferred

---

## LOVELACE RULE [ENFORCED]

**Behavioral intent:** Before testing any variant in direction, use, or implementation,
save a snapshot of current working state. Compare outcomes. Adopt only if demonstrably
better. Restore from save point if variant fails or is inconclusive.
**Structural enforcement:** Any agent or Claude session initiating a variant test MUST
produce a baseline_ref before the test begins. Tests without a declared baseline_ref
are blocked.

Required fields before any variant test proceeds:
```json
{
  "rule": "LOVELACE",
  "baseline_ref": "path/to/snapshot OR git commit hash OR config-YYYYMMDD.json",
  "variant_description": "what is being tested and why",
  "success_criteria": "how better will be measured — must be defined BEFORE test runs",
  "outcome": null,
  "decision": null
}
```

Workflow:
1. SAVE — commit/snapshot current working state, record baseline_ref
2. TEST — run variant against baseline
3. COMPARE — measure outcome vs. success_criteria defined in step 1
4. DECIDE — adopt variant / restore from baseline / iterate from baseline
5. LOG — write completed Lovelace record to decision-log.json

Restore trigger: variant fails OR outcome is inconclusive OR outcome < baseline.
"Inconclusive" counts as failure — default to baseline.
A variant declared better without a recorded baseline_ref is a Lovelace violation.

---

## WATKINS RULE (PLANNING GATE) [ENFORCED]

**Behavioral intent:** Before starting any complex build that touches multiple files
or agents, produce a 5-line plan. No code before planning gate passes.
Named after Gloria Jean Watkins (bell hooks) for clarity of intent before action.

**Structural enforcement:** Any task touching 3+ files OR requiring 2+ tool calls
MUST produce a plan block before implementation begins.

Required plan format:
```
PLAN: [task name]
1. [first action]
2. [second action]
3. [third action]
EXPECTED OUTCOME: [what success looks like]
ROLLBACK: [how to undo if needed]
```

Enforcement:
- Tasks without plan block are blocked
- Plans longer than 5 numbered steps require decomposition
- Complex plans decompose into sub-plans, each with its own block
- Plan approval is implicit unless explicitly rejected by user

---

## AUTODREAM RULE [ENFORCED]

**Behavioral intent:** The nightly autodream.py script consolidates session memory
and updates health metrics. Claude sessions should never modify autodream outputs
directly — they are system-generated artifacts.

**Structural enforcement:** Files matching `autodream-*.json` and `memory-distill-*.json`
are READ-ONLY to Claude sessions. Only autodream.py writes to these files.

Protected files:
- `autodream-distill.json` — nightly memory consolidation
- `memory-distill-*.json` — per-project memory extracts
- `studio-health.json` — nightly health score (written by autodream)

Claude sessions MAY:
- Read these files for context
- Reference their contents in responses
- Suggest changes to autodream.py logic

Claude sessions MUST NOT:
- Write directly to protected files
- Modify autodream.py without explicit user instruction
- Override health scores manually

Violation: Any write attempt to protected files logs to error-log.json and aborts.

---

## TURING RULE [ENFORCED]

**Behavioral intent:** Agent output must cite information sources inline using [source_id]
notation. Outputs are verifiable, not just plausible. Named after Alan Turing.
**Structural enforcement:** All assessment and extraction outputs MUST pass turing_check()
before being written to disk or sent to inbox.

Implementation:
    from utilities.turing_gate import turing_check, turing_wrap, turing_annotate
    result = turing_check(output_text, agent_name='legal-agent')
    title = turing_annotate('Hellmaze', source_id='ia:web20100601', confidence=0.88)

Accepted: [source_id], [source:name], Source: name, Evidence: field, [confidence:N]
Applies to: legal agents, archaeology agents, intel agents, any text assessment output.
Does NOT apply to: internal state writes, log entries, config files.

---

## BABBAGE RULE [ENFORCED]

**Behavioral intent:** Extracted data must be schema-validated before downstream use.
Prevents garbage-in-garbage-out at read-time. Complements Hopper (write-time).
Named after Charles Babbage: garbage in = garbage out, always.
**Structural enforcement:** Any function that consumes extracted pipeline data for
decisions, scoring, or output generation MUST call babbage_validate() on the input
before proceeding. Functions decorated with @babbage_guard block automatically.

Schemas defined in: utilities/babbage_gate.py — SCHEMAS dict.
Current schemas: inbox_item, legal_assessment, job_listing, extraction_result,
whiteboard_item, game_candidate, source_registry_entry.

Implementation:
    from utilities.babbage_gate import babbage_validate, babbage_guard, babbage_load

    # Inline check before decision function
    result = babbage_validate(data, "legal_assessment", agent="scorer")
    if not result["valid"]: return None

    # Decorator — auto-blocks on schema failure
    @babbage_guard("legal_assessment")
    def score_assessment(assessment: dict): ...

    # File loader with built-in validation
    data = babbage_load("legal_results.json", schema_name="legal_assessment")

Add new schemas to SCHEMAS dict whenever a new data type enters the pipeline.
Run babbage_report() periodically to audit schema compliance across all data files.

---

## VECTOR CONTEXT RULE

On session start run:
python "G:/My Drive/Projects/_studio/session-startup.py"
Output is your context. Under 200 tokens.
If script fails: read session-handoff.md directly.
Never inject studio-context.md — 27,063 tokens is the old way. It is retired.

Nightly reindex runs automatically at 01:15 AM (Studio\VectorReindex).
Force reindex manually: python context-vector-store.py --reindex

---

## TASK ROUTING PROTOCOL (mandatory before every task)

Before starting any task ask one question:
"Does this require Claude's reasoning or is it mechanical work?"

MECHANICAL (always offload — do not use Claude):

* Running tests or scripts
* File reads and writes
* Scoring or ranking data
* Scraping and parsing
* Reformatting or validating JSON
* Registering scheduler tasks
* Any task a Python script can do without judgment

REASONING (Claude handles):

* Architecture decisions
* Writing new agent specs
* Debugging unexpected behavior
* Synthesizing results into recommendations
* Writing rules and specs
* Any task requiring judgment or creativity

For mechanical tasks:

* Write a Python script that uses Gemini Flash-Lite or Ollama
* Schedule it or run it directly
* Return results to Claude for review only
* Document routing decision in task-log.json

For reasoning tasks:

* Time-box to minimum operations needed
* No exploratory reads unless necessary
* Write outputs in one pass, not iteratively

POST-BUILD (mandatory after every build):

* If system files touched: note SRE should run next session
* If new agent built: note stress test needed
* Mark task complete only after output verified

---

# STUDIO — Universal Agent Rules

# Applies to ALL projects. Read this every session.

## SESSION START PROTOCOL

1. Check if CONTEXT.md exists in this project folder
2. IF CONTEXT.md EXISTS (resume session):

   * Read it fully
   * Output a 3-line status summary: what it is, current %, last known state
   * State the suggested next action from the file
   * Ask: "Work on suggested next action, or something different?"
   * Wait for user response before doing anything else
3. IF NO CONTEXT.md (new project):

   * Ask the user these questions one at a time:
     a. "What is this project? (one sentence)"
     b. "What's the MVP — the smallest version that proves this works?"
     c. "Any stack preferences or constraints?"
     d. "What should I build or do first?"
   * After answers, CREATE CONTEXT.md before writing any code
   * Confirm: "CONTEXT.md created. Ready to begin. Proceeding with: [first task]"

## WORK PROTOCOL (mid-session)

* Before writing any code: output a numbered plan
* Wait for explicit user approval ("yes", "go", "looks good", etc.)
* After approval: execute the plan
* At major decision points (architecture, library choice, approach fork): STOP and ask
* Do not chain multiple large changes without checking in

## SESSION END PROTOCOL

When user types /exit or says "done for today" or "wrap up":

1. Output a session summary:

```
SESSION SUMMARY
---------------
Completed: [what was built/done]
Status: [X%] complete
Blockers: [any open issues or unknowns]
Next session: [specific first action to take next time]
```

2. Update CONTEXT.md with all of the above
3. Confirm: "CONTEXT.md updated. Session closed."
4. Load git-commit-agent.md and run: commit all dirty projects
5. Load changelog-agent.md. Update changelogs for all changed projects.
6. Run the following to mark session ended and push status to GitHub:

```
python -c "import sys; sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities'); from session_logger import update_status; update_status(current_task='session_ended')" && git -C "G:/My Drive/Projects/_studio" add status.json && git -C "G:/My Drive/Projects/_studio" commit -m "chore: session end status update" && git -C "G:/My Drive/Projects/_studio" push origin master
```

If context usage exceeds 70%, run /compact immediately and update state.json with a
checkpoint note before compacting.

## OUTPUT STANDARDS

* Prefer single-file solutions when possible (HTML, single script)
* No unnecessary dependencies — justify any new package before adding it
* Code must be functional before session ends — no half-built states
* If something is broken at end of session, document it explicitly in CONTEXT.md blockers

## CONTEXT.md FORMAT

When creating or updating CONTEXT.md, use this exact structure:

```
# [PROJECT NAME]

## What It Is
[One paragraph description]

## Status
Progress: [X%]
Last Updated: [YYYY-MM-DD]

## Stack
[Technologies in use]

## Completed
- [list of done items]

## In Progress
- [current active work]

## Next Action
[Specific first thing to do next session — be precise]

## Blockers
- [anything blocking progress, or "None"]

## Session Log
- [YYYY-MM-DD]: [what happened]
```

## GENERAL RULES

* Never assume a decision — ask if uncertain
* Never start coding without a plan approved by the user
* Never end a session without updating CONTEXT.md
* Keep responses concise — no filler, no restating what the user just said
* If blocked, state the blocker clearly and propose 2-3 specific options to resolve it

---

## Operating Rules for Claude in Studio Context

### Access Rule

- Never ask user to find files or fetch data when tools are available
- Use google_drive_search, Desktop Commander, view, bash directly
- Report: "Reading [path] now" — then do it
- No permission-seeking for tool usage

### Compounding Failure Rule [ENFORCED]

- One attempt + one clarification question + pivot
- No retry loops without new information
- If stuck: state clearly what failed, ask what's needed
- Surface blockers immediately, don't spin
- Enforcement: if same approach is attempted 3x without new information,
  BLOCK further retries, log to error-log.json, escalate to supervisor-inbox.json

---

## Bezos Rule (API Circuit Breaker)

*Named after the KAIROS/autocompact lesson from the Claude Code source leak (2026-03-31)*

Any agent script that loops over API calls (Gemini, Anthropic, OpenRouter) MUST
implement a consecutive-failure circuit breaker:

```python
MAX_CONSECUTIVE_FAILURES = 3
consecutive_failures = 0
for item in items:
    try:
        result = call_api(item)
        consecutive_failures = 0  # reset on success
    except Exception as e:
        consecutive_failures += 1
        log(f"  ERROR: {str(e)[:60]}")
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            log(f"  CIRCUIT BREAKER: {MAX_CONSECUTIVE_FAILURES} consecutive failures — aborting")
            break
```

Rationale: Anthropic's own codebase burned ~250K API calls/day from unchecked retry loops.
Applied to: product_archaeology_run.py, whiteboard_score.py — extend to all future agent loops.

---

## CONSTRAINT ENFORCEMENT SUMMARY

| Rule | Mode | Gate | Violation Action |
|---|---|---|---|
| Shannon | ENFORCED | Token counter on handoff write | Block + truncate + log |
| Hamilton | ENFORCED | TTL decorator on all scheduled tasks | Abort + log |
| Hopper | ENFORCED | Pydantic validation on inbox writes | Reject + log |
| Kay | ENFORCED | Directive validator before agent dispatch | Block + require human approval |
| Codd | ENFORCED | @codd_gate decorator on all extraction functions | Null blocked fields + log |
| Lovelace | ENFORCED | baseline_ref required before any variant test | Block test + require snapshot |
| Bezos | ENFORCED | Circuit breaker in all API loop scripts | Abort after 3 consecutive failures |
| Compounding Failure | ENFORCED | 3-attempt cap without new information | Block + escalate |
| Turing | ENFORCED | turing_check on all assessment/extraction outputs | Flag + log, warn agent |
| Babbage | ENFORCED | babbage_validate on all data reads before downstream use | Block function + log |

All violations write to: G:/My Drive/Projects/_studio/error-log.json
All violations stamped with constraint_version from utilities/constraint_version.py
SRE-scout audits constraint compliance weekly (Monday 07:00).
