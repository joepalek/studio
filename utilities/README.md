# Studio Utilities

Shared utilities for all studio agents. **Import from here — never copy.**

```python
import sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from scraper_utils import fetch, find_career_url, report_to_supervisor
from unicode_safe import safe_print, safe_str, safe_json_load, to_str
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
| `random_delay(min_s, max_s)` | Sleep 2–8s (randomized) between requests |

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
| `safe_str(obj, max_len)` | Convert any object to ASCII-safe string. Non-ASCII → `?` |
| `safe_print(*args)` | Drop-in `print()` replacement that sanitizes all args |
| `safe_json_load(path, encoding)` | Load JSON with utf-8 → utf-8-sig → latin-1 → bytes fallback |
| `safe_json_dump(obj, path, indent)` | Save JSON as utf-8 (not system locale) |
| `to_str(value, max_len)` | Normalize list-or-string field (Open Library returns lists) |
| `safe_to_str(value, max_len)` | `to_str` + ASCII sanitize in one call |

**Used by:**
- `ghost-book/pass2_validate.py` (safe_str, to_str — inline copy, migrate when convenient)
- Any agent printing user-sourced text (book titles, company names, web content)

---

## Adding a New Utility

1. Create `utilities/your_utility.py` with a module docstring explaining the problem it solves
2. Add an entry to this README (name, functions, used-by)
3. Add a `UTILITIES_REGISTRY` entry in `supervisor.md`
4. If the utility was born from a recurring error across 2+ agents, log it in `whiteboard.json` with `type: tool`

## Utility Candidate Signals

These error patterns in agent logs indicate a missing shared utility:

| Error Pattern | Likely Utility Needed |
|---|---|
| `UnicodeEncodeError: charmap codec` | `unicode_safe.py` → `safe_print` |
| `AttributeError: list object has no attribute` on API field | `unicode_safe.py` → `to_str` |
| `HTTP Error 403` or `429` repeated across agents | `scraper_utils.py` → `fetch` with backoff |
| `json.JSONDecodeError` on file load | `unicode_safe.py` → `safe_json_load` |
| `ConnectionRefusedError` / timeout on Ollama | shared `ollama_utils.py` (not yet built) |
| Repeated Gemini API boilerplate across scripts | shared `gemini_utils.py` (not yet built) |
