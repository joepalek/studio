# Studio Utilities

Shared utilities for all studio agents. **Import from here — never copy.**

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
