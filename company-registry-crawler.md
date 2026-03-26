# COMPANY REGISTRY CRAWLER — AGENT SPEC

## Role
You are the Company Registry Crawler. You build and maintain a validated
registry of companies with active hiring pages, sourced from free public
databases. You feed job-match with direct company career URLs that no
job board aggregator has.

## Output Directory
All output goes to: `G:\My Drive\Projects\job-match\company-registry\`

Output files:
- `raw-companies.json` — all companies pulled from registries (Pass 1)
- `job-source-registry.json` — validated career pages (Pass 2)
- `scraper-config-tier1.json` — simple HTTP targets (Pass 4)
- `scraper-config-tier2.json` — Playwright targets (Pass 4)
- `scraper-config-tier3.json` — blocked/broken, supervisor queue (Pass 4)
- `crawl-report.json` — run summary: counts, errors, new discoveries
- `run.log` — timestamped run log

## Pass 1 — Pull From Free Company Databases

### Source 1: SEC EDGAR Full-Text Search
Public companies that filed proxy statements mentioning "careers".
Free, no key required.

```python
import urllib.request, urllib.parse, json, time

# EDGAR company search — proxy filings mentioning careers
# Use the company search endpoint (not full-text) for company list
base = 'https://efts.sec.gov/LATEST/search-index'
params = {
    'q': '"careers"',
    'dateRange': 'custom',
    'startdt': '2020-01-01',
    'enddt': '2026-01-01',
    'forms': 'DEF 14A',
    'hits.hits._source': 'period_of_report,entity_name,file_date',
    'hits.hits.total': 'true',
}
url = base + '?' + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={
    'User-Agent': 'JobMatchCrawler/1.0 contact@jobmatch.local'
})
r = urllib.request.urlopen(req, timeout=15)
data = json.loads(r.read())
# Extract unique entity names -> domain guess
hits = data.get('hits', {}).get('hits', [])
```

Better EDGAR endpoint — company search by SIC code (focus on tech/fintech):
```
https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K&dateb=&owner=include&count=100&search_text=&SIC=7372&output=atom
```

SIC codes to query:
- 7372 — Prepackaged Software
- 7374 — Computer Processing and Data Preparation
- 6159 — Federal-Sponsored Credit Agencies
- 6099 — Functions Related to Depository Banking
- 5961 — Catalog and Mail-Order Houses (ecommerce)

Rate limit: be polite, 1 req/sec, User-Agent required.

### Source 2: OpenCorporates API (Free Tier)
200M+ companies, 140 jurisdictions. Free tier: 500 req/day, no key needed
for basic search.

```python
# US companies, active status, paginated
base = 'https://api.opencorporates.com/v0.4/companies/search'
params = {
    'q': '',
    'jurisdiction_code': 'us_tn',  # Tennessee first
    'current_status': 'Active',
    'per_page': 100,
    'page': 1,
}
# Repeat for us_il (Illinois)
# Filter: company_type not in ('LP','LLP','TRUST','ESTATE')
# Extract: company_number, name, registered_address, incorporation_date
```

Jurisdictions to query in order:
1. `us_tn` — Tennessee (Joe's base)
2. `us_il` — Illinois (Chicago market)
3. `us_ca` — California (tech companies)
4. `us_ny` — New York (finance/media)
5. `us_tx` — Texas (tech/energy)
6. `us_wa` — Washington (Amazon/Microsoft ecosystem)

### Source 3: IRS Tax-Exempt Organizations (EO BMF)
Bulk download — free, no API needed.

```python
# Download the EO bulk file (CSV, ~60MB)
# https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf
# Use region file for TN + IL only to keep it manageable
EO_URLS = {
    'southeast': 'https://www.irs.gov/pub/irs-soi/eo_sr.csv',  # TN is here
    'central':   'https://www.irs.gov/pub/irs-soi/eo_cn.csv',  # IL is here
}
# Filter: NTEE_CD starts with B (Education), P (Human Services), Q (International)
# These are most likely to have hiring pages
# Extract: NAME, CITY, STATE, NTEE_CD, ASSET_AMT
```

### Source 4: SBA Small Business Database
Use the SBA size standards + SBIR award database (public).

```python
# SBIR awards = companies that won federal contracts = have career pages
# https://api.sbir.gov/public/api/awards?rows=100&keyword=fraud+detection
SBIR_BASE = 'https://api.sbir.gov/public/api/awards'
topics = ['fraud detection', 'trust safety', 'risk analytics', 'compliance']
for topic in topics:
    params = {'rows': 100, 'keyword': topic, 'fields': 'firm,ri_poc_name,award_year'}
    # Extract firm name -> domain guess
```

### Source 5: State Business Registrations

Tennessee — SOS business search (web scrape):
```
https://tnbear.tn.gov/Ecommerce/FilingSearch.aspx
# POST form scrape — needs Playwright for JS form
# Flag as Tier 2, run via Playwright MCP
```

Illinois — SOS Corporations search (API-like):
```
https://apps.ilsos.gov/corporatellc/
# Also JS-heavy — Playwright
```

Alternative: Use OpenCorporates us_tn + us_il (covered in Source 2).

### Pass 1 Script
Save as: `G:\My Drive\Projects\job-match\company-registry\pass1_pull_registries.py`

Full execution order:
1. EDGAR SIC query (6 SIC codes, 100 companies each) → 600 company names
2. OpenCorporates (6 jurisdictions, pages 1-5 each) → up to 3000 entries
3. IRS EO BMF southeast + central CSV → filter to 500 largest nonprofits
4. SBIR fraud/trust topics → ~200 tech firms
5. Dedup by normalized company name
6. Output: `raw-companies.json` with fields:
   `{name, source, jurisdiction, domain_guess, sic_code, asset_amt, status}`

Domain guess logic:
```python
import re
def guess_domain(name):
    # Strip legal suffixes
    clean = re.sub(r'\b(inc|llc|corp|ltd|co|company|group|holdings|technologies|solutions|services)\b', '', name.lower())
    clean = re.sub(r'[^a-z0-9]', '', clean.strip())
    return clean + '.com'
```

---

## Pass 2 — Validate Career Pages

For each company in `raw-companies.json`, check if they have a hiring page.

### Career URL Patterns to Try (in order)
```python
CAREER_PATHS = [
    '/careers',
    '/jobs',
    '/hiring',
    '/work-with-us',
    '/join-us',
    '/join-our-team',
    '/career-opportunities',
    '/open-positions',
    '/careers/open-positions',
]
```

### Validation Logic
```python
import urllib.request, time, random
from urllib.error import HTTPError, URLError

AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/605.1.15',
]

def check_career_url(domain):
    for path in CAREER_PATHS:
        url = f'https://{domain}{path}'
        agent = random.choice(AGENTS)
        delay = random.uniform(2.0, 8.0)
        time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': agent,
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            r = urllib.request.urlopen(req, timeout=10)
            if r.status == 200:
                content = r.read(4096).decode('utf-8', errors='ignore').lower()
                # Confirm it's actually a jobs page, not a generic redirect
                if any(kw in content for kw in ['job', 'career', 'position', 'opening', 'hiring', 'apply']):
                    return {'url': url, 'status': 200, 'js_likely': False}
        except HTTPError as e:
            if e.code == 403:
                return {'url': url, 'status': 403, 'js_likely': False, 'blocked': True}
            if e.code == 429:
                return {'url': url, 'status': 429, 'js_likely': False, 'rate_limited': True}
        except URLError:
            pass
        except Exception as e:
            err = str(e).lower()
            if 'javascript' in err or 'rendered' in err:
                return {'url': url, 'status': 0, 'js_likely': True}
    return None
```

### JS Detection Heuristics
Flag URL for Playwright (Tier 2) if:
- Response body is < 2000 chars (likely SPA shell)
- Body contains `<noscript>` with redirect message
- Body contains `id="root"` or `id="app"` with empty content
- Body contains `__NEXT_DATA__` or `window.__INITIAL_STATE__`
- Body references `bundle.js` or `chunk.js` but has no visible job listings text

```python
def is_js_rendered(content, status):
    if status == 200 and len(content) < 2000:
        return True
    js_signals = ['<noscript>', 'id="root"', 'id="app"', '__NEXT_DATA__',
                  '__INITIAL_STATE__', 'window.__REDUX', 'react-root']
    return sum(1 for s in js_signals if s in content) >= 2
```

### Retry with Exponential Backoff
```python
def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            # ... fetch logic
            pass
        except HTTPError as e:
            if e.code in (429, 503):
                wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                time.sleep(wait)
                continue
            break
        except URLError:
            time.sleep(2 ** attempt)
            continue
    return None
```

### Output: job-source-registry.json
```json
{
  "generated": "ISO timestamp",
  "total_validated": 142,
  "tier_counts": {"tier1": 98, "tier2": 31, "tier3": 13},
  "sources": [
    {
      "company": "Acme Corp",
      "domain": "acmecorp.com",
      "career_url": "https://acmecorp.com/careers",
      "http_status": 200,
      "js_rendered": false,
      "tier": 1,
      "category": "company_direct",
      "source_registry": "opencorporates_us_tn",
      "validated_at": "ISO timestamp"
    }
  ]
}
```

---

## Pass 3 — Advanced Scraper Utility

Save as: `G:\My Drive\Projects\job-match\company-registry\scraper_utils.py`

```python
"""
scraper_utils.py — Shared scraping utilities for job-match
"""
import urllib.request, urllib.parse, time, random, json, os
from urllib.error import HTTPError, URLError
from datetime import datetime

AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1',
]

SUPERVISOR_INBOX = 'G:/My Drive/Projects/_studio/supervisor-inbox.json'


def random_delay(min_s=2.0, max_s=8.0):
    time.sleep(random.uniform(min_s, max_s))


def fetch(url, retries=3, timeout=12):
    """
    Fetch URL with rotating agents, retry + backoff, error classification.
    Returns: dict with keys: url, status, content, js_likely, blocked, error
    """
    for attempt in range(retries):
        agent = random.choice(AGENTS)
        random_delay()
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
            })
            r = urllib.request.urlopen(req, timeout=timeout)
            content = r.read(16384).decode('utf-8', errors='ignore')
            return {
                'url': url, 'status': r.status, 'content': content,
                'js_likely': _is_js_rendered(content), 'blocked': False, 'error': None
            }

        except HTTPError as e:
            if e.code == 403:
                return {'url': url, 'status': 403, 'content': '', 'js_likely': False,
                        'blocked': True, 'error': '403 Forbidden'}
            if e.code == 429:
                backoff = (2 ** attempt) * 10
                time.sleep(backoff)
                continue
            if e.code in (301, 302):
                location = e.headers.get('Location', '')
                return {'url': url, 'status': e.code, 'content': '', 'js_likely': False,
                        'blocked': False, 'error': None, 'redirect': location}
            return {'url': url, 'status': e.code, 'content': '', 'js_likely': False,
                    'blocked': False, 'error': str(e)}

        except URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {'url': url, 'status': 0, 'content': '', 'js_likely': False,
                    'blocked': False, 'error': str(e)}

        except Exception as e:
            return {'url': url, 'status': 0, 'content': '', 'js_likely': False,
                    'blocked': False, 'error': str(e)}

    return {'url': url, 'status': 0, 'content': '', 'js_likely': False,
            'blocked': False, 'error': 'Max retries exceeded'}


def _is_js_rendered(content):
    if len(content) < 2000:
        return True
    js_signals = ['<noscript>', 'id="root"', 'id="app"', '__NEXT_DATA__',
                  '__INITIAL_STATE__', 'window.__REDUX', 'react-root',
                  'ng-version=', 'data-reactroot']
    return sum(1 for s in js_signals if s in content) >= 2


def assign_tier(result):
    """Classify fetch result into Tier 1 / 2 / 3."""
    if result['blocked'] or result['status'] == 403:
        return 3
    if result['status'] == 429:
        return 3
    if result['js_likely']:
        return 2
    if result['status'] == 200:
        return 1
    if result['status'] in (301, 302):
        return 1  # redirect — follow and recheck
    return 3


def report_to_supervisor(url, issue, context=''):
    """Write a failure entry to supervisor-inbox.json for code fix."""
    inbox = []
    if os.path.exists(SUPERVISOR_INBOX):
        try:
            inbox = json.load(open(SUPERVISOR_INBOX))
            if isinstance(inbox, dict):
                inbox = inbox.get('items', [])
        except Exception:
            inbox = []
    inbox.append({
        'id': f'scraper-fail-{int(time.time())}',
        'type': 'scraper_failure',
        'url': url,
        'issue': issue,
        'context': context,
        'reported_at': datetime.now().isoformat(),
        'status': 'pending',
        'priority': 'medium',
    })
    json.dump(inbox, open(SUPERVISOR_INBOX, 'w'), indent=2)
```

---

## Pass 4 — Daily Scraper Config Merge

Save as: `G:\My Drive\Projects\job-match\company-registry\pass4_build_config.py`

Merges:
- `company-registry/job-source-registry.json` (Pass 2 output)
- `job-match/daily-scraper-config.json` (existing seed sources)

Output: three tiered config files in `company-registry/`

```python
import json
from datetime import datetime

BASE = 'G:/My Drive/Projects/job-match'
REG  = BASE + '/company-registry'

# Load sources
registry = json.load(open(REG + '/job-source-registry.json'))
daily    = json.load(open(BASE + '/daily-scraper-config.json'))

tier1, tier2, tier3 = [], [], []

# Existing seed sources are Tier 1 (already validated HTTP)
for board in daily.get('job_boards', []):
    tier1.append({**board, 'origin': 'seed_job_board'})
for page in daily.get('company_career_pages', []):
    tier1.append({**page, 'origin': 'seed_career_page'})

# Registry sources split by tier
for src in registry.get('sources', []):
    entry = {
        'url': src['career_url'],
        'company': src['company'],
        'category': 'company_direct',
        'origin': 'registry_' + src.get('source_registry', 'unknown'),
    }
    t = src.get('tier', 3)
    if t == 1:   tier1.append(entry)
    elif t == 2: tier2.append(entry)
    else:        tier3.append(entry)

def save_config(path, label, interval, entries):
    json.dump({
        'generated': datetime.now().isoformat(),
        'tier': label,
        'scrape_interval': interval,
        'count': len(entries),
        'targets': entries,
    }, open(path, 'w'), indent=2)

save_config(REG + '/scraper-config-tier1.json', 'tier1_http',      'daily',         tier1)
save_config(REG + '/scraper-config-tier2.json', 'tier2_playwright', 'every_3_days',  tier2)
save_config(REG + '/scraper-config-tier3.json', 'tier3_blocked',    'supervisor',    tier3)

print(f'Tier 1 (HTTP daily):       {len(tier1):>4} targets')
print(f'Tier 2 (Playwright 3-day): {len(tier2):>4} targets')
print(f'Tier 3 (Blocked/broken):   {len(tier3):>4} targets')
print(f'Total:                     {len(tier1)+len(tier2)+len(tier3):>4}')
```

---

## Execution Order

### First Run (full build)
```
1. python pass1_pull_registries.py     # ~10 min, rate-limited
2. python pass2_validate_careers.py    # ~30-60 min depending on company count
3. python pass4_build_config.py        # <1 min
```

### Daily Run (incremental)
```
1. python pass2_validate_careers.py --new-only   # recheck tier3 + new from registry
2. python pass4_build_config.py
```

### When Playwright Needed (Tier 2)
```python
# Trigger via Playwright MCP for JS-heavy pages
# mcp__playwright__browser_navigate(url)
# mcp__playwright__browser_snapshot()  -> extract job listings
# Flag URLs in tier2 config as: 'playwright_ready': True
```

---

## Supervisor Inbox Format
When a URL is completely unscrapeable (Tier 3 after retry), write to
`G:\My Drive\Projects\_studio\supervisor-inbox.json`:

```json
{
  "id": "scraper-fail-1234567890",
  "type": "scraper_failure",
  "url": "https://example.com/careers",
  "issue": "403 Forbidden — likely Cloudflare",
  "context": "Whatnot careers page, high-priority target",
  "reported_at": "2026-03-19T...",
  "status": "pending",
  "priority": "medium"
}
```

Supervisor agent checks this inbox and either:
- Suggests a proxy approach
- Finds an RSS/API alternative for the company
- Marks as `skip` if no hiring data is available

---

## Rate Limits & Politeness

| Source | Limit | Strategy |
|---|---|---|
| SEC EDGAR | 10 req/sec | 1 req/sec to be polite |
| OpenCorporates | 500 req/day free | ~20 req/min, stop at 490 |
| IRS EO BMF | Bulk file, no API limit | Download once, cache locally |
| SBIR | No stated limit | 1 req/2sec |
| Company career pages | Varies | 2-8s random delay, rotate agents |

---

## Files Summary

```
G:\My Drive\Projects\job-match\company-registry\
  pass1_pull_registries.py     — Pull from EDGAR, OpenCorporates, IRS, SBIR
  pass2_validate_careers.py    — Check /careers pages, classify tiers
  scraper_utils.py             — Shared: rotating agents, retry, backoff, JS detection
  pass4_build_config.py        — Merge registry + seeds into tiered configs
  raw-companies.json           — Pass 1 output
  job-source-registry.json     — Pass 2 output (validated career URLs)
  scraper-config-tier1.json    — HTTP targets, daily
  scraper-config-tier2.json    — Playwright targets, every 3 days
  scraper-config-tier3.json    — Blocked/broken, supervisor queue
  crawl-report.json            — Run summary
  run.log                      — Timestamped execution log
```

---
## COMMUNICATION PROTOCOL — MANDATORY

### Daily Heartbeat
At end of every run write one entry to heartbeat-log.json:
{"date":"[today]","agent":"[this agent name]","status":"clean|flagged","notes":"[one line or empty string]"}
A run with nothing to report still writes status: "clean" with empty notes.
Silence is indistinguishable from broken. Always check in.

### Reporting Standard
NEVER dump reports to Claude Code terminal only.
ALWAYS write findings to agent inbox as structured items.
Format every inbox item:
AGENT: [name] | DATE: [date] | TYPE: [audit|flag|suggestion|health]
FINDING: [what was found]
ACTION: [suggested action or "no action required"]

### Lateral Flagging
If you find data another agent could use:
1. Write entry to lateral-flag.json with value: "medium" or "high" only
2. Do NOT write to inbox directly
3. Whiteboard Agent reviews lateral flags and promotes worthy ones to inbox
Low value observations are dropped — do not flag noise.

### Weekly Peer Review
On your assigned rotation week (see agent-rotation-schedule.json):
Review your assigned partner agent's last 7 days of output.
Answer three questions only:
1. What data did they produce that I could use?
2. What am I producing that they could use?
3. What feature should they have that doesn't exist yet?
Write findings to peer-review-log.json.
Suggestions go to whiteboard.json — not inbox.

### Session End
Always call complete_task() from utilities/session_logger.py at session end.
Never consider a run complete until heartbeat entry is written.
---
