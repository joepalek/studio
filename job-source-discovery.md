# JOB SOURCE DISCOVERY — WEB-SCALE JOB SURFACE MAPPER

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

## What Counts as a Job Source

ANY URL pattern that regularly contains active job postings:
- Major job boards (Indeed, LinkedIn, ZipRecruiter, Monster, Dice, etc.)
- Niche industry boards (tech, healthcare, legal, trades, etc.)
- Company career pages (apple.com/careers, walmart.com/careers, etc.)
- Government job boards (USAJobs, state workforce sites, county HR sites)
- Local/regional job sites (regional newspapers, local boards)
- Staffing agencies and recruiters
- Social platforms with job sections (LinkedIn, Facebook Jobs, Twitter/X)
- Professional associations with job boards
- University job boards
- Non-profit and NGO job sites
- Freelance platforms (Upwork, Fiverr, Toptal for contract work)
- Remote-specific boards
- Diversity-focused boards
- Veteran-focused boards
- Industry forums with hiring sections (Reddit r/forhire, Hacker News Who's Hiring)

## Pass 1 — Mine Common Crawl Index for Job URLs

Common Crawl indexes the entire web monthly. Query its index API
to find all URLs containing job-related path patterns:

```bash
python -c "
import urllib.request, json, time, os

OUTPUT_DIR = 'G:/My Drive/Projects/job-match/source-discovery/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Common Crawl Index API — searches latest crawl
# Free, no auth needed, covers billions of pages
CC_INDEX = 'https://index.commoncrawl.org/CC-MAIN-2025-18-index'

# Job URL patterns to search
job_patterns = [
    '*/careers',
    '*/careers/*',
    '*/jobs',
    '*/jobs/*',
    '*/job-openings',
    '*/job-openings/*',
    '*/hiring',
    '*/work-with-us',
    '*/join-us',
    '*/join-our-team',
    '*/employment',
    '*/employment-opportunities',
    '*/open-positions',
    '*/current-openings',
]

all_sources = set()

for pattern in job_patterns[:5]:  # Start with first 5, expand later
    url = f'{CC_INDEX}?url={urllib.request.quote(pattern)}&output=json&limit=1000&fl=url,status'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'JobMatchCrawler/1.0'})
        r = urllib.request.urlopen(req, timeout=30)
        for line in r.read().decode().split(chr(10)):
            if not line.strip(): continue
            try:
                record = json.loads(line)
                if record.get('status') == '200':
                    all_sources.add(record['url'])
            except: pass
        print(f'  {pattern}: {len(all_sources)} total URLs so far')
    except Exception as e:
        print(f'  {pattern}: ERROR — {e}')
    time.sleep(2)

# Save raw discovered URLs
with open(OUTPUT_DIR + 'cc-discovered-raw.json', 'w') as f:
    json.dump({'count': len(all_sources), 'urls': list(all_sources)[:10000]}, f)

print(f'Common Crawl discovery: {len(all_sources)} job URLs found')
"
```

## Pass 2 — Mine Job Posting Schema Markup Sites

Sites that use Google's JobPosting structured data are designed
to be found. Query Google's dataset or use sitemap mining:

```bash
python -c "
import urllib.request, json, time, re, os

OUTPUT_DIR = 'G:/My Drive/Projects/job-match/source-discovery/'

# Known high-value job sources by category
# This is a SEED list — the crawler expands from here

SEED_SOURCES = {
    'major_boards': [
        'https://www.indeed.com/jobs',
        'https://www.linkedin.com/jobs',
        'https://www.ziprecruiter.com/jobs',
        'https://www.monster.com/jobs',
        'https://www.careerbuilder.com/jobs',
        'https://www.dice.com/jobs',
        'https://www.glassdoor.com/Job',
        'https://www.simplyhired.com/jobs',
        'https://www.snagajob.com/jobs',
        'https://www.idealist.org/en/jobs',
    ],
    'tech_niche': [
        'https://jobs.github.com',
        'https://stackoverflow.com/jobs',
        'https://angel.co/jobs',
        'https://wellfound.com/jobs',
        'https://www.ycombinator.com/jobs',
        'https://hired.com/jobs',
        'https://www.builtinchicago.org/jobs',
        'https://www.builtinnyc.com/jobs',
        'https://www.builtinla.com/jobs',
        'https://news.ycombinator.com/jobs',
    ],
    'government': [
        'https://www.usajobs.gov',
        'https://www.governmentjobs.com',
        'https://www.federaljobs.net',
        'https://jobs.state.gov',
        'https://www.careeronestop.org',
        'https://www.jobsforfelons.net',
        # State workforce boards
        'https://jobs.tn.gov',
        'https://illinoisworknet.com/jobs',
        'https://www.jobs.ca.gov',
        'https://www.texasworkforce.org/jobs',
        'https://www.floridajobs.org',
    ],
    'remote_specific': [
        'https://remoteok.com',
        'https://weworkremotely.com',
        'https://remotive.com/remote-jobs',
        'https://remote.co/remote-jobs',
        'https://jobspresso.co',
        'https://nodesk.co/remote-jobs',
        'https://authentic.jobs',
        'https://www.flexjobs.com',
        'https://remoteleaf.com',
        'https://justremote.co',
    ],
    'diversity_focused': [
        'https://www.diversityjobs.com',
        'https://www.blackprofessionals.com/jobs',
        'https://www.hispanicjobs.com',
        'https://www.iminorities.com',
        'https://www.disability.gov/jobs',
        'https://www.recruitmilitary.com/jobs',
        'https://www.veteranjobs.com',
        'https://www.hiremilitary.us',
        'https://www.womenforhire.com',
        'https://outprofessionals.com/jobs',
    ],
    'industry_niche': [
        # Healthcare
        'https://www.healthcarejobsite.com',
        'https://www.healthecareers.com',
        'https://www.nursejobscafe.com',
        # Legal
        'https://www.lawjobs.com',
        'https://www.legalstaff.com',
        # Finance
        'https://www.efinancialcareers.com',
        'https://www.financialjobbank.com',
        # Trades
        'https://www.tradespeople.co.uk/jobs',
        'https://www.constructionjobs.com',
        # Education
        'https://www.higheredjobs.com',
        'https://www.schoolspring.com',
        # Non-profit
        'https://www.idealist.org/en/jobs',
        'https://jobs.nonprofitjobseeker.com',
    ],
    'social_platforms': [
        'https://www.linkedin.com/jobs',
        'https://www.facebook.com/jobs',
        'https://twitter.com/search?q=hiring',
        'https://www.reddit.com/r/forhire',
        'https://www.reddit.com/r/jobsearchhacks',
        'https://news.ycombinator.com/jobs',
    ],
    'aggregators': [
        'https://www.jooble.org',
        'https://www.adzuna.com/jobs',
        'https://www.trovit.com/jobs',
        'https://www.jobrapido.com',
        'https://www.talent.com/jobs',
        'https://www.neuvoo.com/jobs',
        'https://www.jobsora.com',
    ],
    'staffing_agencies': [
        'https://www.manpower.com/jobs',
        'https://www.adecco.com/en-us/find-a-job',
        'https://www.roberthalfstaff.com/jobs',
        'https://www.kellyjobs.com',
        'https://www.expresspros.com/us/find-a-job',
        'https://www.spherion.com/find-jobs',
        'https://www.staffmark.com/find-work',
    ],
    'local_regional': [
        'https://www.craigslist.org/about/sites',  # All CL cities
        'https://www.localjobnetwork.com',
        'https://www.jobs-near-me.org',
        'https://www.careerjet.com',
        'https://www.jobing.com',
    ],
    'freelance_contract': [
        'https://www.upwork.com/freelance-jobs',
        'https://www.freelancer.com/jobs',
        'https://www.toptal.com/jobs',
        'https://www.guru.com/jobs',
        'https://www.peopleperhour.com/freelance-jobs',
        'https://99designs.com/jobs',
    ]
}

# Count totals
total = sum(len(v) for v in SEED_SOURCES.values())
print(f'Seed sources cataloged: {total} across {len(SEED_SOURCES)} categories')
for cat, urls in SEED_SOURCES.items():
    print(f'  {cat}: {len(urls)} sources')

with open(OUTPUT_DIR + 'seed-sources.json', 'w') as f:
    json.dump(SEED_SOURCES, f, indent=2)

print(f'Saved to seed-sources.json')
"
```

## Pass 3 — Validate All Seed Sources (parallel HTTP checks)

```bash
python -c "
import urllib.request, json, time, os, concurrent.futures
from datetime import datetime

OUTPUT_DIR = 'G:/My Drive/Projects/job-match/source-discovery/'
seeds = json.load(open(OUTPUT_DIR + 'seed-sources.json'))

# Flatten all sources
all_sources = []
for category, urls in seeds.items():
    for url in urls:
        all_sources.append({'url': url, 'category': category})

def check_source(source):
    url = source['url']
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; JobMatchBot/1.0)'},
        )
        r = urllib.request.urlopen(req, timeout=8)
        status = r.getcode()
        content_len = len(r.read(1000))
        return {**source, 'status': 'active', 'http': status, 'has_content': content_len > 100, 'checked': datetime.now().isoformat()}
    except urllib.error.HTTPError as e:
        return {**source, 'status': 'blocked' if e.code == 403 else 'error', 'http': e.code, 'checked': datetime.now().isoformat()}
    except Exception as e:
        return {**source, 'status': 'failed', 'error': str(e)[:60], 'checked': datetime.now().isoformat()}

print(f'Validating {len(all_sources)} sources...')
results = []

# Check in batches of 10 concurrent
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(check_source, s): s for s in all_sources}
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        result = future.result()
        results.append(result)
        status_icon = 'OK' if result['status'] == 'active' else 'XX'
        if i % 10 == 0:
            active = len([r for r in results if r['status'] == 'active'])
            print(f'  Progress: {i+1}/{len(all_sources)} — {active} active so far')

active = [r for r in results if r['status'] == 'active']
blocked = [r for r in results if r['status'] == 'blocked']
failed = [r for r in results if r['status'] in ['failed', 'error']]

print(f'Results: {len(active)} active | {len(blocked)} blocked (403) | {len(failed)} failed')

with open(OUTPUT_DIR + 'validated-sources.json', 'w') as f:
    json.dump({
        'generated': datetime.now().isoformat(),
        'total': len(results),
        'active': len(active),
        'blocked': len(blocked),
        'failed': len(failed),
        'sources': results
    }, f, indent=2)

print('Saved to validated-sources.json')
"
```

## Pass 4 — Discover Company Career Pages via Sitemap Mining

Large companies publish sitemap.xml files that list all their URLs.
Career pages are almost always in there:

```bash
python -c "
import urllib.request, json, re, time, os

OUTPUT_DIR = 'G:/My Drive/Projects/job-match/source-discovery/'

# Fortune 500 + major employers — check their sitemaps for career URLs
major_employers = [
    'amazon.com', 'walmart.com', 'apple.com', 'microsoft.com', 'google.com',
    'meta.com', 'netflix.com', 'salesforce.com', 'adobe.com', 'oracle.com',
    'ibm.com', 'accenture.com', 'deloitte.com', 'pwc.com', 'kpmg.com',
    'jpmorgan.com', 'bankofamerica.com', 'wellsfargo.com', 'citigroup.com',
    'target.com', 'homedepot.com', 'lowes.com', 'costco.com', 'kroger.com',
    'ups.com', 'fedex.com', 'usps.com', 'dhl.com',
    'mcdonalds.com', 'starbucks.com', 'subway.com', 'yum.com',
    'boeing.com', 'lockheedmartin.com', 'raytheon.com', 'generaldynamics.com',
    'pfizer.com', 'johnsonandjohnson.com', 'abbvie.com', 'merck.com',
    'unitedhealthgroup.com', 'anthem.com', 'aetna.com', 'humana.com',
    # Marketplace/e-commerce (relevant to Joe's background)
    'ebay.com', 'etsy.com', 'shopify.com', 'poshmark.com', 'mercari.us',
    'whatnot.com', 'stockx.com', 'goat.com', 'chairish.com', 'rubylane.com',
]

career_urls = []

for domain in major_employers[:20]:  # Start with first 20
    sitemap_url = f'https://www.{domain}/sitemap.xml'
    try:
        req = urllib.request.Request(
            sitemap_url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; JobMatchBot/1.0)'}
        )
        r = urllib.request.urlopen(req, timeout=8)
        content = r.read().decode('utf-8', errors='ignore')

        # Find career-related URLs in sitemap
        urls = re.findall(r'<loc>(https?://[^<]+)</loc>', content)
        career = [u for u in urls if any(kw in u.lower() for kw in
            ['/career', '/job', '/hiring', '/work-with', '/join', '/employment'])]

        if career:
            career_urls.extend(career)
            print(f'  {domain}: {len(career)} career URLs')
        else:
            # Try common career page paths directly
            for path in ['/careers', '/jobs', '/about/careers']:
                try:
                    test_url = f'https://www.{domain}{path}'
                    r2 = urllib.request.urlopen(
                        urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'}),
                        timeout=5
                    )
                    if r2.getcode() == 200:
                        career_urls.append(test_url)
                        print(f'  {domain}: found at {path}')
                        break
                except: pass
    except Exception as e:
        print(f'  {domain}: {str(e)[:50]}')
    time.sleep(0.5)

with open(OUTPUT_DIR + 'company-career-pages.json', 'w') as f:
    json.dump({'count': len(career_urls), 'urls': career_urls}, f, indent=2)

print(f'Company career pages found: {len(career_urls)}')
"
```

## Pass 5 — Build Master Source Registry

Combine all discovered sources into one master file:

```bash
python -c "
import json, os
from datetime import datetime

OUTPUT_DIR = 'G:/My Drive/Projects/job-match/source-discovery/'
MASTER = 'G:/My Drive/Projects/job-match/job-source-registry.json'

registry = {
    'generated': datetime.now().isoformat(),
    'version': '1.0',
    'description': 'Master registry of all known job posting surfaces on the web',
    'sources': []
}

# Load validated seeds
try:
    validated = json.load(open(OUTPUT_DIR + 'validated-sources.json'))
    for s in validated['sources']:
        if s['status'] == 'active':
            registry['sources'].append({
                'url': s['url'],
                'category': s['category'],
                'status': 'active',
                'type': 'seed',
                'last_validated': s.get('checked', '')
            })
except: pass

# Load Common Crawl discovered
try:
    cc = json.load(open(OUTPUT_DIR + 'cc-discovered-raw.json'))
    for url in cc.get('urls', [])[:5000]:
        registry['sources'].append({
            'url': url,
            'category': 'cc_discovered',
            'status': 'unvalidated',
            'type': 'crawl_discovered'
        })
except: pass

# Load company career pages
try:
    company = json.load(open(OUTPUT_DIR + 'company-career-pages.json'))
    for url in company.get('urls', []):
        registry['sources'].append({
            'url': url,
            'category': 'company_career',
            'status': 'active',
            'type': 'sitemap_discovered'
        })
except: pass

# Summary
active = len([s for s in registry['sources'] if s['status'] == 'active'])
total = len(registry['sources'])
registry['summary'] = {
    'total_sources': total,
    'active_validated': active,
    'unvalidated': total - active
}

json.dump(registry, open(MASTER, 'w'), indent=2)
print(f'Master registry: {total} sources ({active} validated active)')
print(f'Saved to job-source-registry.json')
print()
print('Next: build daily-job-scraper.md to read this registry')
print('and fetch fresh listings from each source daily')
"
```

## Running Overnight

```
Load job-source-discovery.md. Run all 5 passes as background tasks.
Save all results to G:\My Drive\Projects\job-match\source-discovery\
This is for the Job Match product — builds web-scale job source registry.
```

## What This Produces

- `source-discovery/seed-sources.json` — 80+ categorized seed sources
- `source-discovery/cc-discovered-raw.json` — Common Crawl job URLs
- `source-discovery/validated-sources.json` — HTTP-verified active sources
- `source-discovery/company-career-pages.json` — Fortune 500 + employer career pages
- `job-source-registry.json` — Master registry, input to daily scraper

## Scale Expectations
- Seed sources: ~80 validated sources across 12 categories
- Common Crawl: potentially thousands of company career pages
- Company sitemaps: hundreds of direct career page URLs
- Total registry: 500-5000+ unique job posting surfaces

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| Common Crawl API | Python direct | FREE |
| HTTP validation | Python concurrent | FREE |
| Sitemap mining | Python direct | FREE |
| Registry building | Python | FREE |
| Everything | No LLM needed | $0.00 |

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
