# JOB SOURCE CRAWLER — MONTHLY BROAD DISCOVERY

## Role
You are the Job Source Crawler. You run monthly to discover and catalog
all active job posting sources on the web — job boards, company career
pages, niche sites, and aggregators. You build a "mailbox map" that the
daily job scraper uses to know exactly where to look for fresh postings.

You run entirely free via Wayback CDX + direct HTTP + Ollama analysis.
Zero Claude quota. Zero cost.

## Two-Tier Architecture

### Tier 1 — This agent (monthly)
Discovers job posting sources across the web. Builds and updates
job-sources.json — the master mailbox map.

### Tier 2 — Daily scraper (runs against job-sources.json)
Fetches only from known sources. Fast, targeted, no discovery overhead.
Built after this agent confirms sources are valid.

## Target Source Categories

### Category A — General Remote Job Boards
High volume, updated daily:
- remoteok.com
- weworkremotely.com
- remote.co/remote-jobs
- flexjobs.com
- jobspresso.co
- remotive.com
- nodesk.co/remote-jobs
- authentic.jobs

### Category B — Fraud/Trust & Safety Roles (Joe's target)
Niche boards matching your background:
- jobs.lever.co (filter: trust safety)
- boards.greenhouse.io (filter: fraud)
- jobs.ashbyhq.com
- careers.whatnot.com
- jobs.shopify.com/search?q=trust
- ebay.com/careers (fraud analyst)

### Category C — Data Analyst / Operations (secondary target)
- linkedin.com/jobs (remote data analyst)
- indeed.com/jobs?q=remote+data+analyst
- glassdoor.com/Job/remote-data-analyst
- angel.co/jobs (startups)
- builtin.com/jobs

### Category D — Marketplace/Collectibles Industry
Companies where your eBay/collectibles background is a differentiator:
- careers.whatnot.com
- ebay.com/careers
- poshmark.com/careers
- mercari.us/careers
- chairish.com/page/careers
- 1stdibs.com/careers
- comc.com/careers
- goldin.co/careers

## Execution

### Pass 1 — Discover and validate job sources
```bash
python -c "
import urllib.request, json, time, re, os
from datetime import datetime

OUTPUT = 'G:/My Drive/Projects/job-match/job-sources.json'

sources = [
    # General remote
    {'name': 'RemoteOK', 'url': 'https://remoteok.com/remote-jobs', 'category': 'general_remote', 'api': 'https://remoteok.com/api'},
    {'name': 'WeWorkRemotely', 'url': 'https://weworkremotely.com', 'category': 'general_remote', 'rss': 'https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss'},
    {'name': 'Remotive', 'url': 'https://remotive.com/remote-jobs', 'category': 'general_remote', 'api': 'https://remotive.com/api/remote-jobs'},
    {'name': 'Remote.co', 'url': 'https://remote.co/remote-jobs', 'category': 'general_remote'},
    {'name': 'Jobspresso', 'url': 'https://jobspresso.co', 'category': 'general_remote'},
    # Trust & Safety / Fraud
    {'name': 'Whatnot Careers', 'url': 'https://careers.whatnot.com', 'category': 'target_company'},
    {'name': 'eBay Careers', 'url': 'https://careers.ebayinc.com', 'category': 'target_company'},
    {'name': 'Poshmark Careers', 'url': 'https://poshmark.com/careers', 'category': 'target_company'},
    {'name': 'Mercari Careers', 'url': 'https://careers.mercari.com', 'category': 'target_company'},
    # Aggregators
    {'name': 'Indeed RSS', 'url': 'https://www.indeed.com/rss?q=remote+fraud+analyst&l=remote', 'category': 'aggregator', 'rss': True},
    {'name': 'Indeed Data Analyst', 'url': 'https://www.indeed.com/rss?q=remote+data+analyst&l=remote', 'category': 'aggregator', 'rss': True},
    {'name': 'RemoteOK API', 'url': 'https://remoteok.com/api?tags=fraud', 'category': 'api_source'},
]

validated = []
failed = []

for source in sources:
    url = source.get('api') or source.get('rss') or source['url']
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; StudioJobCrawler/1.0)',
                'Accept': 'application/json, text/html, application/rss+xml, */*'
            }
        )
        r = urllib.request.urlopen(req, timeout=10)
        status = r.getcode()
        content = r.read(500).decode('utf-8', errors='ignore')

        # Detect if it has job listings
        has_jobs = any(kw in content.lower() for kw in
            ['job', 'position', 'career', 'hiring', 'role', 'opening', 'apply'])

        source['status'] = 'active'
        source['http_status'] = status
        source['has_job_content'] = has_jobs
        source['last_checked'] = datetime.now().isoformat()
        source['fetch_url'] = url
        validated.append(source)
        print(f'  OK  {source[\"name\"]} — {status} — jobs detected: {has_jobs}')

    except Exception as e:
        source['status'] = 'failed'
        source['error'] = str(e)[:80]
        source['last_checked'] = datetime.now().isoformat()
        failed.append(source)
        print(f'  FAIL {source[\"name\"]} — {str(e)[:60]}')

    time.sleep(1)

output = {
    'generated': datetime.now().isoformat(),
    'total_sources': len(sources),
    'active': len(validated),
    'failed': len(failed),
    'sources': validated + failed
}

os.makedirs('G:/My Drive/Projects/job-match', exist_ok=True)
json.dump(output, open(OUTPUT, 'w'), indent=2)
print(f'Done. {len(validated)} active sources → job-sources.json')
"
```

### Pass 2 — Discover additional sources via Wayback CDX
Find archived job boards and career pages that may not be well-known:

```bash
python -c "
import urllib.request, json, time

OUTPUT = 'G:/My Drive/Projects/job-match/job-sources-discovered.json'

# Search CDX for job board URLs archived in last 2 years
search_patterns = [
    'remoteok.com/remote-*-jobs',
    'weworkremotely.com/remote-jobs*',
    'jobs.lever.co/*trust*',
    'jobs.lever.co/*fraud*',
    'boards.greenhouse.io/*trust*',
    'boards.greenhouse.io/*fraud*',
    'careers.whatnot.com*',
]

discovered = []
for pattern in search_patterns:
    encoded = urllib.request.quote(pattern)
    url = (f'http://web.archive.org/cdx/search/cdx'
           f'?url={encoded}&output=json&fl=original&limit=20'
           f'&from=20240101&collapse=urlkey&matchType=prefix')
    try:
        r = urllib.request.urlopen(url, timeout=15)
        rows = json.loads(r.read())
        urls = [row[0] for row in rows[1:]] if len(rows) > 1 else []
        discovered.extend(urls)
        print(f'  {pattern}: {len(urls)} URLs found')
    except Exception as e:
        print(f'  {pattern}: ERROR — {e}')
    time.sleep(1)

# Deduplicate
unique = list(set(discovered))
json.dump({'discovered_urls': unique, 'count': len(unique)}, open(OUTPUT, 'w'), indent=2)
print(f'Total discovered: {len(unique)} unique job URLs → job-sources-discovered.json')
"
```

### Pass 3 — Score sources with Ollama
For each validated source, use Ollama to assess relevance to Joe's profile:

```bash
python -c "
import json, urllib.request, time

sources_data = json.load(open('G:/My Drive/Projects/job-match/job-sources.json'))
active = [s for s in sources_data['sources'] if s['status'] == 'active']

PROFILE = '''Remote worker seeking: fraud analyst, trust & safety, data analyst, operations analyst.
Background: eBay/collectibles market expertise, data analysis, billing operations, workflow management.
Strong preference: written communication, remote work, marketplace/e-commerce companies.'''

def ollama_score(source_name, source_url, profile):
    prompt = f'''Score this job source 1-10 for relevance to this candidate profile.
Return only: SCORE: X/10 | REASON: one sentence

Profile: {profile}
Job source: {source_name} ({source_url})'''

    payload = json.dumps({
        'model': 'gemma3:4b',
        'prompt': prompt,
        'stream': False
    }).encode()

    try:
        r = urllib.request.urlopen(
            urllib.request.Request(
                'http://127.0.0.1:11434/api/generate',
                data=payload,
                headers={'Content-Type': 'application/json'}
            ), timeout=30
        )
        return json.loads(r.read())['response'].strip()
    except Exception as e:
        return f'SCORE: 5/10 | REASON: Could not assess — {e}'

print('Scoring sources with Ollama...')
for source in active[:10]:  # Score top 10
    score = ollama_score(source['name'], source['url'], PROFILE)
    source['relevance_score'] = score
    print(f'  {source[\"name\"]}: {score[:80]}')
    time.sleep(1)

json.dump(sources_data, open('G:/My Drive/Projects/job-match/job-sources.json', 'w'), indent=2)
print('Scoring complete — job-sources.json updated')
"
```

### Pass 4 — Build daily scraper config
Generate the config file the daily job scraper will use:

```bash
python -c "
import json
from datetime import datetime

sources_data = json.load(open('G:/My Drive/Projects/job-match/job-sources.json'))
active = [s for s in sources_data['sources'] if s['status'] == 'active']

# Build daily scraper config
daily_config = {
    'generated': datetime.now().isoformat(),
    'scrape_interval': 'daily',
    'search_terms': [
        'fraud analyst remote',
        'trust safety analyst remote',
        'data analyst remote',
        'operations analyst remote',
        'marketplace fraud remote',
        'collectibles fraud analyst',
    ],
    'target_companies': [
        'Whatnot', 'eBay', 'Poshmark', 'Mercari', 'Shopify',
        'StockX', 'GOAT', 'Chairish', '1stDibs', 'Goldin'
    ],
    'exclude_keywords': [
        'senior director', 'VP', 'vice president', 'chief',
        'on-site', 'in-office', 'relocate'
    ],
    'salary_min': 45000,
    'sources': [
        {
            'name': s['name'],
            'fetch_url': s.get('fetch_url', s['url']),
            'category': s['category'],
            'type': 'api' if 'api' in s.get('fetch_url','') else
                    'rss' if s.get('rss') else 'html'
        }
        for s in active
    ]
}

json.dump(daily_config, open('G:/My Drive/Projects/job-match/daily-scraper-config.json', 'w'), indent=2)
print(f'Daily scraper config built — {len(active)} sources configured')
print('Run daily-job-scraper.md against this config to fetch fresh listings')
"
```

## Overnight Run Command

```
Load job-source-crawler.md. Run all 4 passes overnight:
1. Validate all job sources
2. Discover additional sources via Wayback CDX
3. Score sources with Ollama
4. Build daily scraper config

Save all results to G:\My Drive\Projects\job-match\
Run as background tasks where possible.
```

## Output Files
- `job-sources.json` — validated source list with scores
- `job-sources-discovered.json` — CDX-discovered URLs
- `daily-scraper-config.json` — config for daily scraper

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| HTTP validation | Python direct | FREE |
| CDX discovery | Wayback API | FREE |
| Source scoring | Ollama local | FREE |
| Config generation | Python | FREE |
| Everything | No Claude needed | $0.00 |

## Next Step
After this runs → build daily-job-scraper.md which reads
daily-scraper-config.json and fetches fresh job listings every morning,
scores them against Joe's profile, and writes top matches to
job-match-results.json for review in studio inbox.
