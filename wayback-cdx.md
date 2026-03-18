# WAYBACK CDX SKILL — ARCHIVE SCRAPER

## Role
You are the Wayback CDX Skill. You query the Internet Archive's CDX API
to find snapshots of any URL or domain across any time range. You are a
shared skill used by Ghost Book Validator, Digital Archaeology Agent,
Conspiracy Tracker, Foreign Ministry, and any agent that needs to
research historical web content.

You run entirely on free resources — the CDX API is free, all processing
routes through Ollama locally. Zero cost per run.

## CDX API Basics
The CDX API returns a list of all snapshots for a URL:
```
http://web.archive.org/cdx/search/cdx
  ?url=example.com
  &output=json
  &fl=timestamp,original,statuscode,mimetype
  &limit=100
  &from=20000101
  &to=20091231
```

No API key required. Rate limit: ~1 request/second sustained.

## Core Query Function

```bash
python -c "
import urllib.request, json, time, sys

def cdx_query(url, date_from=None, date_to=None, limit=100, mime_filter=None):
    '''Query Wayback CDX API for snapshots of a URL'''
    params = {
        'url': url,
        'output': 'json',
        'fl': 'timestamp,original,statuscode,mimetype,length',
        'limit': str(limit),
        'collapse': 'digest',  # deduplicate identical snapshots
    }
    if date_from: params['from'] = date_from
    if date_to:   params['to'] = date_to
    if mime_filter: params['filter'] = f'mimetype:{mime_filter}'

    query = '&'.join(f'{k}={urllib.request.quote(str(v))}' for k,v in params.items())
    api_url = f'http://web.archive.org/cdx/search/cdx?{query}'

    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'StudioResearchAgent/1.0'})
        r = urllib.request.urlopen(req, timeout=15)
        rows = json.loads(r.read())
        if not rows or len(rows) < 2:
            return []
        headers = rows[0]
        return [dict(zip(headers, row)) for row in rows[1:]]
    except Exception as e:
        print(f'CDX ERROR: {e}', file=sys.stderr)
        return []

# Test call
results = cdx_query('coast-to-coast-am.com', date_from='19980101', date_to='20051231', limit=20)
print(f'Found {len(results)} snapshots')
for r in results[:5]:
    print(f'  {r[\"timestamp\"][:8]} — {r[\"original\"]} ({r[\"mimetype\"]})')
"
```

## Fetch Snapshot Content

```bash
python -c "
import urllib.request, time

def fetch_snapshot(timestamp, url):
    '''Fetch actual content from a Wayback snapshot'''
    wayback_url = f'https://web.archive.org/web/{timestamp}/{url}'
    try:
        req = urllib.request.Request(
            wayback_url,
            headers={'User-Agent': 'StudioResearchAgent/1.0'}
        )
        r = urllib.request.urlopen(req, timeout=20)
        content = r.read().decode('utf-8', errors='ignore')
        # Strip HTML tags for text extraction
        import re
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]  # First 5000 chars
    except Exception as e:
        return f'FETCH_ERROR: {e}'

# Test
text = fetch_snapshot('20030615120000', 'http://www.coasttocoastam.com/')
print(text[:500])
"
```

## Overnight Batch Research Jobs

### Job 1 — C2C AM Archive Scan (Coast to Coast AM 1998-2005)
Finds all archived snapshots of C2C AM, extracts guest lists and topics.
Estimated runtime: 2-3 hours on Ollama overnight.

```bash
python -c "
import urllib.request, json, time, os, re

OUTPUT_FILE = 'G:/My Drive/Projects/_studio/cdx-c2c-results.json'

def cdx_query(url, date_from, date_to, limit=500):
    params = f'url={urllib.request.quote(url)}&output=json&fl=timestamp,original,statuscode&limit={limit}&from={date_from}&to={date_to}&collapse=digest'
    try:
        r = urllib.request.urlopen(f'http://web.archive.org/cdx/search/cdx?{params}', timeout=15)
        rows = json.loads(r.read())
        return [dict(zip(rows[0], row)) for row in rows[1:]] if len(rows) > 1 else []
    except: return []

def fetch_text(ts, url):
    try:
        r = urllib.request.urlopen(f'https://web.archive.org/web/{ts}/{url}', timeout=20)
        raw = r.read().decode('utf-8', errors='ignore')
        text = re.sub(r'<[^>]+>', ' ', raw)
        return re.sub(r'\s+', ' ', text).strip()[:3000]
    except: return ''

c2c_urls = [
    'coasttocoastam.com',
    'www.coasttocoastam.com',
    'artbell.com',
    'www.artbell.com',
]

results = []
for site in c2c_urls:
    print(f'Scanning {site}...')
    snaps = cdx_query(site, '19980101', '20051231', limit=200)
    print(f'  Found {len(snaps)} snapshots')
    # Sample every 10th snapshot for content
    for snap in snaps[::10]:
        text = fetch_text(snap['timestamp'], f'http://{site}/')
        if text and len(text) > 200:
            results.append({
                'site': site,
                'timestamp': snap['timestamp'],
                'date': snap['timestamp'][:8],
                'text_preview': text[:500],
                'full_text': text
            })
            print(f'    Fetched: {snap[\"timestamp\"][:8]}')
        time.sleep(1.5)  # Respect archive.org rate limit
    time.sleep(3)

json.dump(results, open(OUTPUT_FILE, 'w'), indent=2)
print(f'Done. {len(results)} pages saved to cdx-c2c-results.json')
" &
echo "C2C scan running in background — results → cdx-c2c-results.json"
```

### Job 2 — Dead Tech Forum Scan (Early digital/tech forums 1999-2008)
Finds archived content from old tech forums in multiple languages.

```bash
python -c "
import urllib.request, json, time, re

OUTPUT_FILE = 'G:/My Drive/Projects/_studio/cdx-tech-forums.json'

dead_sites = [
    # English tech forums
    ('slashdot.org', '19990101', '20051231'),
    ('kuro5hin.org', '19990101', '20081231'),
    ('plastic.com',  '20010101', '20051231'),
    # German tech
    ('heise.de/newsticker', '20000101', '20061231'),
    ('pro-linux.de',        '20000101', '20081231'),
    # Japanese tech
    ('2ch.net/tech', '20010101', '20071231'),
]

results = []
for site, date_from, date_to in dead_sites:
    params = f'url={urllib.request.quote(site)}&output=json&fl=timestamp,original&limit=50&from={date_from}&to={date_to}&collapse=digest'
    try:
        r = urllib.request.urlopen(f'http://web.archive.org/cdx/search/cdx?{params}', timeout=15)
        rows = json.loads(r.read())
        snaps = [dict(zip(rows[0], row)) for row in rows[1:]] if len(rows) > 1 else []
        results.append({'site': site, 'period': f'{date_from[:4]}-{date_to[:4]}', 'snapshot_count': len(snaps), 'snapshots': snaps[:20]})
        print(f'{site}: {len(snaps)} snapshots found')
    except Exception as e:
        print(f'{site}: ERROR — {e}')
    time.sleep(2)

json.dump(results, open(OUTPUT_FILE, 'w'), indent=2)
print(f'Done. Results saved to cdx-tech-forums.json')
" &
echo "Tech forum scan running in background"
```

### Job 3 — Ghost Book Premise Hunt
Finds archived academic and research sites mentioning specific topics.
Used by Ghost Book Validator agent.

```bash
python -c "
import urllib.request, json, time, re

OUTPUT_FILE = 'G:/My Drive/Projects/_studio/cdx-ghost-books.json'

# Topics to hunt — books that failed due to lack of data
search_topics = [
    ('hemp composite materials strength', '19900101', '20051231'),
    ('vedic mathematics computing algorithms', '19950101', '20081231'),
    ('ancient metallurgy iron impossible artifacts', '20000101', '20101231'),
    ('sanskrit programming language nasa', '19950101', '20101231'),
]

results = []
for topic, date_from, date_to in search_topics:
    # Search for wayback pages mentioning these topics via CDX URL wildcard
    query_url = f'*{topic.replace(\" \",\"*\")}*'
    params = f'url={urllib.request.quote(query_url)}&output=json&fl=timestamp,original&matchType=domain&limit=30&from={date_from}&to={date_to}'
    try:
        r = urllib.request.urlopen(f'http://web.archive.org/cdx/search/cdx?{params}', timeout=15)
        rows = json.loads(r.read())
        snaps = [dict(zip(rows[0], row)) for row in rows[1:]] if len(rows) > 1 else []
        results.append({'topic': topic, 'snapshot_count': len(snaps), 'urls': [s['original'] for s in snaps[:10]]})
        print(f'{topic}: {len(snaps)} results')
    except Exception as e:
        print(f'{topic}: {e}')
    time.sleep(2)

json.dump(results, open(OUTPUT_FILE, 'w'), indent=2)
print(f'Ghost book hunt done → cdx-ghost-books.json')
"
```

## Analyze Results with Ollama (free, local)

After overnight scans complete, run analysis locally:

```bash
python -c "
import json, urllib.request

def ollama_analyze(text, prompt):
    payload = json.dumps({
        'model': 'gemma3:4b',
        'prompt': f'{prompt}\n\nText:\n{text[:2000]}',
        'stream': False
    }).encode()
    r = urllib.request.urlopen(
        urllib.request.Request('http://127.0.0.1:11434/api/generate',
        data=payload, headers={'Content-Type': 'application/json'}),
        timeout=60
    )
    return json.loads(r.read())['response'].strip()

# Load C2C results and extract key claims
results = json.load(open('G:/My Drive/Projects/_studio/cdx-c2c-results.json'))
findings = []

for item in results[:20]:  # Process first 20 pages
    analysis = ollama_analyze(
        item['full_text'],
        'Extract any specific factual claims, predictions, names, dates, or technical details mentioned. List them as bullet points. Skip vague opinions.'
    )
    findings.append({'date': item['date'], 'site': item['site'], 'claims': analysis})
    print(f'Analyzed {item[\"date\"]}')

json.dump(findings, open('G:/My Drive/Projects/_studio/cdx-c2c-analysis.json', 'w'), indent=2)
print('Analysis complete → cdx-c2c-analysis.json')
"
```

## Running Overnight

Start all three jobs in sequence before bed:

```
Load wayback-cdx.md. Run overnight batch:
1. Start Job 1 (C2C AM archive scan)
2. Start Job 2 (Dead tech forums)  
3. Start Job 3 (Ghost book hunt)
All run in background via bash. Results write to _studio folder.
In the morning run the Ollama analysis pass on results.
```

## Output Files
All results write to `G:\My Drive\Projects\_studio\`:
- `cdx-c2c-results.json` — C2C AM pages 1998-2005
- `cdx-c2c-analysis.json` — Ollama-extracted claims
- `cdx-tech-forums.json` — Dead tech forum index
- `cdx-ghost-books.json` — Ghost book topic URLs

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| CDX API queries | bash/python, no LLM | FREE |
| Page fetching | bash/python, no LLM | FREE |
| Content analysis | Ollama local | FREE |
| Pattern synthesis | Gemini Flash | FREE |
| Final report | Claude | Only on demand |

Total overnight cost: $0.00

## Rules
- Always sleep 1-2 seconds between archive.org requests
- Never exceed 30 requests/minute to archive.org
- Always write results to JSON incrementally (not at end) in case of crash
- Mark results with timestamp so morning analysis knows what ran
- Ollama analysis runs AFTER fetching — never block fetching on analysis
