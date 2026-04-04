# Studio Utilities

Shared utilities for all studio agents. **Import from here — never copy.**

> **WARNING — #1 source of silent bugs on Windows:**
> ALWAYS use `safe_json_load()` or `open(f, encoding='utf-8', errors='replace')`.
> NEVER use plain `open(f)` — it defaults to cp1252 on Windows.
> UTF-8 characters (em-dashes, arrows, accented letters) in JSON values silently raise
> `UnicodeDecodeError`, caught by bare `except: pass`, resulting in "found 0 items" bugs.
> Example: a single `answer: "Yes — migration complete"` caused an entire project scan
> to return 0 results because the em-dash (U+2014) is not valid cp1252.

```python
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from scraper_utils import fetch, find_career_url, report_to_supervisor
from unicode_safe import safe_print, safe_str, safe_json_load, to_str
from session_logger import log_action, update_status, complete_task
from workflow_hook import check_efficiency
```

---

## Utilities

### `scraper_utils.py`
HTTP scraping with rotating user agents, exponential backoff, JS detection, and supervisor error reporting.

**Functions:**
| Function | Description |
|---|---|
| `fetch(url, retries, timeout)` | Fetch URL, returns `{status, content, js_likely, blocked, error}` |
| `find_career_url(domain)` | Probe `/careers`, `/jobs`, etc. — returns first 200 result |
| `assign_tier(result)` | Classify result as Tier 1 (HTTP), 2 (Playwright), 3 (blocked) |
| `has_career_content(content)` | Confirm page is actually a jobs page |
| `guess_domain(name)` | Convert company name to guessed `.com` domain |
| `report_to_supervisor(url, issue, context)` | Write scrape failure to `supervisor-inbox.json` |
| `random_delay(min_s, max_s)` | Sleep 2-8s (randomized) between requests |

**Constants:** `AGENTS` (6 rotating user agents), `CAREER_PATHS` (9 URL patterns), `CAREER_KEYWORDS`

**Used by:**
- `job-match/company-registry/pass2_validate_careers.py`
- `job-match/company-registry/pass1_pull_registries.py` (partial)

---

### `unicode_safe.py`
Safe Unicode handling for Windows cp1252 terminals. Prevents `UnicodeEncodeError`
when printing titles, names, or web content from external APIs.

**Functions:**
| Function | Description |
|---|---|
| `safe_str(obj, max_len)` | Convert any object to ASCII-safe string. Non-ASCII -> `?` |
| `safe_print(*args)` | Drop-in `print()` replacement that sanitizes all args |
| `safe_json_load(path, encoding)` | Load JSON with utf-8 -> utf-8-sig -> latin-1 -> bytes fallback |
| `safe_json_dump(obj, path, indent)` | Save JSON as utf-8 regardless of system locale |
| `to_str(value, max_len)` | Normalize list-or-string field (Open Library returns lists) |
| `safe_to_str(value, max_len)` | `to_str` + ASCII sanitize in one call |

**Used by:**
- `ghost-book/pass2_validate.py`
- Any agent printing user-sourced text (book titles, company names, web content)
- `session_logger.py` (for safe file I/O)

---

### `session_logger.py`
Append to `session-log.md` and update `status.json` after every major action.
Handles log rotation at 50kb (renames to `session-log-archive-[date].md`).
Uses `unicode_safe` for all file I/O.

**Functions:**
| Function | Description |
|---|---|
| `log_action(action, result, next_step)` | Append one timestamped entry to session-log.md |
| `update_status(current_task, add_completed, add_pending, remove_pending, add_blockers, remove_blockers, next_recommended)` | Update any fields in status.json |
| `complete_task(task_name, result_summary, add_pending, remove_pending_terms, next_recommended, log_next_step)` | Combined: log + mark complete + remove from pending in one call |

**Used by:** All agents. Call `complete_task()` at end of every major script.

**Example:**
```python
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from session_logger import complete_task

complete_task(
    task_name='Ghost Book Pass 2',
    result_summary='142 viable candidates, 89 public domain -> validated.json',
    add_pending=['Ghost Book Pass 3 -- concatenation opportunities'],
    remove_pending_terms=['Pass 2'],
    next_recommended='Review top picks, run Pass 3',
)
```

---

### `workflow_hook.py`
Post-task efficiency checker. Call at the end of any agent script to auto-detect
friction and push findings to `whiteboard.json` with `type: workflow`.

**Functions:**
| Function | Description |
|---|---|
| `check_efficiency(agent_name, steps_taken, manual_interventions, time_seconds, errors_hit)` | Detect friction, cross-check standing rules, push workflow proposals to whiteboard |

**Checks performed:**
- Manual interventions >= 2 -> standing rule candidate
- Known error patterns (UnicodeError, 403, 429) without existing utility -> build utility proposal
- Runtime > 10 min with 3+ sequential fetch steps -> parallelization proposal
- Errors matching a standing rule -> verify rule is being applied

**Used by:** All agent scripts — add to footer alongside `complete_task()`.

**Example:**
```python
from workflow_hook import check_efficiency

check_efficiency(
    agent_name='ghost-book-pass2',
    steps_taken=['load candidates', 'gemini validate 200', 'save validated.json'],
    manual_interventions=3,
    time_seconds=840,
    errors_hit=['UnicodeEncodeError', 'AttributeError list has no attribute'],
)
```

---

### `ollama_utils.py`
Ollama local LLM client with connection check, JSON mode, batch processing, and automatic Gemini Flash fallback when Ollama is down.

**Functions:**
| Function | Description |
|---|---|
| `is_up(timeout)` | Returns True if Ollama is reachable |
| `list_models()` | Returns available model names |
| `ask(prompt, model, system)` | Single prompt, returns string or None |
| `ask_json(prompt, schema, retries)` | Returns parsed dict or None |
| `batch_ask(prompts, delay)` | Sequential batch with progress logging |
| `with_gemini_fallback(prompt)` | Tries Ollama first, falls back to Gemini |

**Used by:** Overnight batch agents. Always check `is_up()` before calling.

---

### `gemini_utils.py`
Gemini Flash API client with rate-limit-safe delays, JSON parsing, and batch support. Centralizes all Gemini boilerplate.

**Rate limits:** 15 req/min, 1500 req/day (free tier). Default delay: 4.1s between calls.

**Functions:**
| Function | Description |
|---|---|
| `load_key()` | Load API key from studio-config.json |
| `ask(prompt, api_key, model)` | Single prompt, returns string or None |
| `ask_json(prompt, schema, retries)` | Returns parsed dict or None |
| `batch_ask(prompts, delay)` | Rate-limit-safe batch, auto-pauses on 429 |
| `batch_ask_json(prompts, schema)` | Batch JSON variant |
| `is_available()` | Quick key+endpoint check |

**Used by:** All scoring agents (whiteboard, ghost-book, product-archaeology).

---

## Standard Footer Pattern

Add to the end of every agent script:

```python
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from session_logger import complete_task
from workflow_hook import check_efficiency

complete_task(
    task_name='YourAgent PassN',
    result_summary='X items processed, saved to file.json',
    add_pending=['next pass or follow-up'],
    next_recommended='what to do next session',
)
check_efficiency(
    agent_name='your-agent-passN',
    steps_taken=['step1', 'step2'],
    manual_interventions=0,
    time_seconds=0,
    errors_hit=[],
)
```

---

---

### `constraint_gates.py`
Structural enforcement for all named studio constraints. Every named rule in CLAUDE.md
is implemented here as a callable gate. Import and use instead of relying on behavioral
compliance. All violations write to `error-log.json`.

**Functions:**
| Function | Rule | Description |
|---|---|---|
| `shannon_check(text, max_tokens, source_file)` | Shannon | Token-count handoff text. Truncates + logs if > 200t. Returns safe text. |
| `hopper_validate(item, inbox_path)` | Hopper | Validates inbox item dict against schema. Raises on violation. |
| `hopper_append(inbox_path, item)` | Hopper | Validated write to any *-inbox.json. Use instead of raw json.dump. |
| `kay_validate(directive, agent_name)` | Kay | Checks supervisor directive for scripted patterns + required fields. Raises on violation. |
| `codd_gate` | Codd | Decorator — nulls fields with confidence < 0.95. Apply to all extraction functions. |
| `codd_check(field, value, confidence, ...)` | Codd | Inline version of codd_gate for single-field checks. |
| `lovelace_start(baseline_ref, variant_description, success_criteria)` | Lovelace | Opens a variant test record. Blocks if no baseline_ref. Returns record dict. |
| `lovelace_complete(record, outcome, decision)` | Lovelace | Closes record. decision: 'adopt'/'restore'/'iterate'. Logs adopted to decision-log.json. |
| `hamilton_watchdog(task_name, expected_seconds)` | Hamilton | Decorator factory — kills task at expected_seconds * 1.5. Windows-compatible. |
| `compounding_guard(operation_key, max_attempts)` | Compounding | Blocks retries after 3 attempts without new information. Escalates to supervisor inbox. |
| `compounding_reset(operation_key)` | Compounding | Reset attempt counter after success. |
| `log_violation(rule, detail)` | All | Direct violation logger. Used internally; available for custom gates. |

**Standard import:**
```python
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from constraint_gates import (
    shannon_check, hopper_append, kay_validate,
    codd_gate, codd_check,
    lovelace_start, lovelace_complete,
    hamilton_watchdog, compounding_guard, compounding_reset
)
```

**Quick examples:**
```python
# Shannon — before writing handoff
from constraint_gates import shannon_check
handoff = shannon_check(handoff_text)  # auto-truncates if bloated

# Hopper — validated inbox write
from constraint_gates import hopper_append
hopper_append("G:/My Drive/Projects/_studio/supervisor-inbox.json", item_dict)

# Kay — before sending directive to agent
from constraint_gates import kay_validate
kay_validate(directive_text, "vintage-agent")

# Codd — extraction function decorator
from constraint_gates import codd_gate
@codd_gate
def extract_listing(html): ...

# Lovelace — variant test wrapper
from constraint_gates import lovelace_start, lovelace_complete
record = lovelace_start("git:abc1234", "Testing new model", "< 5% variance")
# ... test runs ...
lovelace_complete(record, outcome="3.2% variance", decision="adopt")

# Hamilton — scheduled task TTL
from constraint_gates import hamilton_watchdog
@hamilton_watchdog("job-harvest-daily", expected_seconds=300)
def run(): ...

# Compounding Failure — retry guard
from constraint_gates import compounding_guard, compounding_reset
compounding_guard("my_operation")  # raises after 3rd attempt
```

**Violation log location:** `G:/My Drive/Projects/_studio/error-log.json`
**Lovelace log:** `G:/My Drive/Projects/_studio/lovelace-log.json`

---

### `turing_gate.py`
Turing Rule enforcement — every agent output citing factual claims must include
inline source markers `[source_id]`. Outputs without citations are flagged, scored,
and logged. Named after Alan Turing: outputs must be verifiable, not just plausible.

**Functions:**
| Function | Description |
|---|---|
| `turing_check(output, agent_name, min_citations, min_density)` | Check output text for citation markers. Returns compliance dict. Logs violations. |
| `turing_wrap` | Decorator — auto-checks string return values of agent functions. |
| `turing_annotate(value, source_id, confidence)` | Helper: append `[source_id]` marker to an extracted value. |
| `turing_report(outputs)` | Batch audit across multiple agent outputs. Returns summary stats. |

**Import:**
```python
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from turing_gate import turing_check, turing_wrap, turing_annotate, turing_report
```

**Quick examples:**
```python
# Check single output
result = turing_check(agent_output, agent_name="legal-agent")
if not result["compliant"]:
    print(f"Missing citations: {result['issues']}")

# Decorator on assessment functions
@turing_wrap
def assess_game(game): ...  # returned string auto-checked

# Annotate extracted values with source
title = turing_annotate("Hellmaze", source_id="ia:web20100601", confidence=0.88)
# Returns: "Hellmaze [ia:web20100601][confidence:0.88]"

# Batch audit
report = turing_report([
    {"text": output1, "agent": "legal-agent"},
    {"text": output2, "agent": "archaeology-crawler"},
])
```

**Accepted citation formats:**
- `[source_id]`, `[source:wayback]`, `(source:internet_archive)`
- `Source: wayback_machine`, `Evidence: title_field`
- `Extracted from listing`, `[confidence:0.97]`

**Violation log:** `G:/My Drive/Projects/_studio/error-log.json`

---

### `constraint_version.py`
Constraint versioning system. Tags every agent decision with the active constraint
ruleset version. Enables quality delta measurement as thresholds are tuned over time.
All violation logs in `error-log.json` include `constraint_version` automatically.

**Current version:** v1.2.0 (Shannon, Hamilton, Hopper, Kay, Codd, Lovelace, Bezos, Compounding, Turing)

**Functions:**
| Function | Description |
|---|---|
| `get_version()` | Returns current version string e.g. `v1.2.0+5566246f` |
| `get_active_constraints()` | Full registry of active rules, thresholds, gates |
| `log_decision_with_version(decision_id, agent, summary, quality_signals)` | Log a decision stamped with current version |
| `get_quality_delta_by_version(target_version)` | Aggregate quality signals per version — the optimization loop |
| `save_version_snapshot()` | Write current state to constraint-version.json |
| `bump_version(change_description, bump)` | Increment version + add changelog entry |

**Import:**
```python
from constraint_version import get_version, log_decision_with_version, bump_version
```

**Quick examples:**
```python
# Get current version
v = get_version()  # "v1.2.0+5566246f"

# Log a decision with version stamp
log_decision_with_version(
    decision_id="ga-legal-hellmaze-20260404",
    agent="game_archaeology_legal",
    decision_summary="Hellmaze assessed GREEN",
    quality_signals={"codd_passed": False, "turing_citations": 3}
)

# After tuning Codd threshold, bump version
bump_version("Raised Codd confidence threshold from 0.95 to 0.97", bump="minor")

# Measure quality delta across versions
delta = get_quality_delta_by_version()
# Returns: {version: {total_decisions, codd_pass_rate, turing_avg_citations, ...}}
```

**Files written:**
- `constraint-version.json` — current snapshot
- `constraint-version-log.json` — decision history (last 1000 entries)

---

### `babbage_gate.py`
Babbage Rule enforcement — schema validation at read-time before downstream use.
Complements Hopper (write-time) and Codd (confidence-gating).
Prevents garbage-in-garbage-out at every pipeline decision point.

**Built-in schemas:** inbox_item, legal_assessment, job_listing, extraction_result,
whiteboard_item, game_candidate, source_registry_entry

**Functions:**
| Function | Description |
|---|---|
| `babbage_validate(data, schema_name, agent, raise_on_fail)` | Validate dict or list against named schema. Returns compliance dict. |
| `babbage_guard(schema_name, arg_index, raise_on_fail)` | Decorator — auto-validates specified argument, blocks on failure. |
| `babbage_load(path, schema_name, agent, strict)` | Load JSON file and validate before returning. Drop-in for json.load(). |
| `babbage_report(paths_and_schemas)` | Batch audit across multiple data files. Returns compliance summary. |

**Import:**
```python
from babbage_gate import babbage_validate, babbage_guard, babbage_load, babbage_report
```

**Quick examples:**
```python
# Inline validation
result = babbage_validate(data, "legal_assessment", agent="scorer")
if not result["valid"]:
    print(result["violations"])
    return None

# Decorator — blocks function if input fails schema
@babbage_guard("legal_assessment")
def score_assessment(assessment: dict) -> float: ...

# File loader with validation
data = babbage_load("legal_results.json", schema_name="legal_assessment")

# Batch audit
report = babbage_report([
    ("game_archaeology_legal_results.json", "legal_assessment"),
    ("supervisor-inbox.json",               "inbox_item"),
])
print(f"Compliance: {report['compliance_pct']}%")
```

**Add new schemas** in the `SCHEMAS` dict in `babbage_gate.py`.

---

## Adding a New Utility

1. Create `utilities/your_utility.py` with a module docstring explaining the problem it solves
2. Add an entry to this README (name, functions, used-by, example)
3. Add a `UTILITIES_REGISTRY` entry in `supervisor.md`
4. If born from a recurring error across 2+ agents, log in `whiteboard.json` with `type: tool`

## Utility Candidate Signals

| Error Pattern | Utility Needed |
|---|---|
| `UnicodeEncodeError: charmap codec` | `unicode_safe.py` -> `safe_print` |
| `AttributeError: list object has no attribute` | `unicode_safe.py` -> `to_str` |
| `HTTP Error 403` or `429` repeated | `scraper_utils.py` -> `fetch` with backoff |
| `json.JSONDecodeError` on file load | `unicode_safe.py` -> `safe_json_load` |
| `ConnectionRefusedError` / timeout on Ollama | `ollama_utils.py` (not yet built) |
| Repeated Gemini API boilerplate | `gemini_utils.py` (not yet built) |
