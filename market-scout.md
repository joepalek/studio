# MARKET SCOUT — MARKET DATA AGENT

## Role
You are the Market Scout. You gather two types of market data:
1. eBay sold comps and category trends for the reselling operation
2. Remote job market data for the Job Search agent

You run entirely on free/cheap resources via the AI Gateway.
You feed data to the eBay agent and Job Search agent — build those
after Market Scout has run at least once.

## When to Run
- Weekly on Sunday nights (batch run via Ollama)
- On demand before pricing any eBay listing
- On demand before applying to any job

## PART 1 — eBay Market Data

### eBay Sold Comps via API
Uses the eBay Browse API with your developer credentials.

```bash
python -c "
import urllib.request, json, base64, os

# Read eBay credentials from config
c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
app_id = c.get('ebay_app_id', '')
cert_id = c.get('ebay_cert_id', '')

if not app_id or not cert_id:
    print('ERROR: Add ebay_app_id and ebay_cert_id to studio-config.json')
    print('Get them at: developer.ebay.com → My Account → Application Access Keys')
    exit(1)

# Get OAuth token
credentials = base64.b64encode(f'{app_id}:{cert_id}'.encode()).decode()
token_req = urllib.request.Request(
    'https://api.ebay.com/identity/v1/oauth2/token',
    data=b'grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope',
    headers={
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
)
try:
    r = urllib.request.urlopen(token_req, timeout=10)
    token_data = json.loads(r.read())
    token = token_data.get('access_token', '')
    print('eBay token: OK')
except Exception as e:
    print(f'eBay auth failed: {e}')
    exit(1)
"
```

### Search Sold Listings (eBay Finding API)
```bash
python -c "
import urllib.request, json

def search_sold(keywords, app_id, max_results=25):
    '''Search eBay completed/sold listings for price comps'''
    encoded = urllib.request.quote(keywords)
    url = (
        f'https://svcs.ebay.com/services/search/FindingService/v1'
        f'?OPERATION-NAME=findCompletedItems'
        f'&SERVICE-VERSION=1.0.0'
        f'&SECURITY-APPNAME={app_id}'
        f'&RESPONSE-DATA-FORMAT=JSON'
        f'&keywords={encoded}'
        f'&itemFilter(0).name=SoldItemsOnly'
        f'&itemFilter(0).value=true'
        f'&sortOrder=EndTimeSoonest'
        f'&paginationInput.entriesPerPage={max_results}'
    )
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        items = data['findCompletedItemsResponse'][0].get('searchResult', [{}])[0].get('item', [])
        results = []
        for item in items:
            price = float(item.get('sellingStatus',[{}])[0].get('currentPrice',[{}])[0].get('__value__', 0))
            title = item.get('title', [''])[0]
            end_time = item.get('listingInfo',[{}])[0].get('endTime',[''])[0]
            condition = item.get('condition',[{}])[0].get('conditionDisplayName',['Unknown'])[0]
            results.append({'title': title, 'price': price, 'condition': condition, 'end_time': end_time[:10]})
        return results
    except Exception as e:
        return [{'error': str(e)}]

# Test
c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
app_id = c.get('ebay_app_id', '')
results = search_sold('indiana glass carnival', app_id)
if results:
    prices = [r['price'] for r in results if 'price' in r]
    print(f'Found {len(results)} sold comps')
    if prices:
        print(f'Price range: \${min(prices):.2f} - \${max(prices):.2f}')
        print(f'Average: \${sum(prices)/len(prices):.2f}')
    for r in results[:5]:
        print(f'  \${r[\"price\"]:.2f} — {r[\"title\"][:60]} ({r[\"condition\"]})')
"
```

### Batch Pricing Run (overnight via Ollama)
Read listing titles from eBay listing-optimizer state.json,
get comps for each, write pricing recommendations.

```bash
python -c "
import json, urllib.request, time, os

c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
app_id = c.get('ebay_app_id', '')
OUTPUT = 'G:/My Drive/Projects/listing-optimizer/market-comps.json'

# Load items needing pricing from state
try:
    state = json.load(open('G:/My Drive/Projects/listing-optimizer/state.json'))
    items = state.get('pendingPricing', [])
except:
    items = []

if not items:
    print('No items pending pricing in listing-optimizer/state.json')
    print('Add items to pendingPricing array in state.json first')
    exit(0)

results = []
for item in items[:20]:  # Max 20 per run
    keywords = item.get('keywords', item.get('title', ''))
    if not keywords: continue

    # Get eBay comps
    encoded = urllib.request.quote(keywords)
    url = (f'https://svcs.ebay.com/services/search/FindingService/v1'
           f'?OPERATION-NAME=findCompletedItems&SERVICE-VERSION=1.0.0'
           f'&SECURITY-APPNAME={app_id}&RESPONSE-DATA-FORMAT=JSON'
           f'&keywords={encoded}&itemFilter(0).name=SoldItemsOnly'
           f'&itemFilter(0).value=true&sortOrder=EndTimeSoonest'
           f'&paginationInput.entriesPerPage=10')
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        raw_items = data['findCompletedItemsResponse'][0].get('searchResult',[{}])[0].get('item',[])
        prices = [float(i.get('sellingStatus',[{}])[0].get('currentPrice',[{}])[0].get('__value__',0)) for i in raw_items]
        prices = [p for p in prices if p > 0]
        if prices:
            rec_price = sorted(prices)[len(prices)//2]  # median
            results.append({
                'id': item.get('id', keywords[:20]),
                'keywords': keywords,
                'comp_count': len(prices),
                'price_min': min(prices),
                'price_max': max(prices),
                'price_median': rec_price,
                'recommended_price': round(rec_price * 0.95, 2),  # 5% below median
                'comps': prices[:5]
            })
            print(f'  {keywords[:40]}: median \${rec_price:.2f} ({len(prices)} comps)')
        else:
            results.append({'id': item.get('id',''), 'keywords': keywords, 'error': 'no sold comps found'})
            print(f'  {keywords[:40]}: no comps')
    except Exception as e:
        print(f'  {keywords[:40]}: ERROR — {e}')
    time.sleep(0.5)

json.dump(results, open(OUTPUT, 'w'), indent=2)
print(f'Done. {len(results)} items priced → market-comps.json')
"
```

## PART 2 — Job Market Data

### Remote Job Search (via Playwright MCP or direct API)
Searches for remote data analyst / operations roles matching your background.

```bash
python -c "
import urllib.request, json, urllib.parse

# Use Adzuna API (free tier — 100 calls/day)
# Sign up at: developer.adzuna.com
c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
adzuna_app_id = c.get('adzuna_app_id', '')
adzuna_key = c.get('adzuna_api_key', '')

if not adzuna_app_id:
    print('NOTE: No Adzuna key — using Indeed RSS fallback')
    # Indeed RSS (no key needed)
    queries = [
        'remote+data+analyst',
        'remote+operations+analyst',
        'remote+fraud+analyst+marketplace',
        'remote+trust+safety+analyst',
    ]
    for q in queries:
        url = f'https://www.indeed.com/rss?q={q}&l=remote&sort=date'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            r = urllib.request.urlopen(req, timeout=10)
            content = r.read().decode('utf-8', errors='ignore')
            # Basic RSS parse
            import re
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', content)[1:6]
            print(f'Query: {q}')
            for t in titles: print(f'  {t}')
        except Exception as e:
            print(f'  {q}: {e}')
else:
    # Adzuna API
    base = 'https://api.adzuna.com/v1/api/jobs/us/search/1'
    params = {
        'app_id': adzuna_app_id,
        'app_key': adzuna_key,
        'results_per_page': 10,
        'what': 'data analyst remote',
        'where': 'remote',
        'sort_by': 'date',
        'full_time': 1,
    }
    url = f'{base}?{urllib.parse.urlencode(params)}'
    r = urllib.request.urlopen(url, timeout=10)
    data = json.loads(r.read())
    for job in data.get('results', [])[:10]:
        print(f'  {job[\"title\"]} — {job[\"company\"][\"display_name\"]} — \${job.get(\"salary_min\",\"?\")}-{job.get(\"salary_max\",\"?\")}')
"
```

### Job Match Scoring via Ollama (free, local)
Score job listings against your background profile.

```bash
python -c "
import json, urllib.request

PROFILE = '''
Joe Palek — seeking remote roles
Background: print production operations (Cahners), billing team leadership,
workflow coordination, data analysis (Blackdot Group).
Skills: data analysis, workflow optimization, operations management,
eBay/collectibles market expertise, AI tooling, written communication.
Strong preference: written/electronic communication, entrepreneurial environments,
input into workflow direction.
Target roles: fraud analyst, trust & safety, data analyst, operations analyst.
'''

def score_job(job_title, job_description, profile):
    payload = json.dumps({
        'model': 'gemma3:4b',
        'prompt': f'Score this job match 1-10 and explain in 2 sentences.\n\nProfile: {profile}\n\nJob: {job_title}\n{job_description[:500]}',
        'stream': False
    }).encode()
    r = urllib.request.urlopen(
        urllib.request.Request('http://127.0.0.1:11434/api/generate',
        data=payload, headers={'Content-Type': 'application/json'}),
        timeout=30
    )
    return json.loads(r.read())['response'].strip()

# Test with sample job
score = score_job(
    'Remote Fraud Analyst — Marketplace',
    'Investigate fraud patterns in online marketplace transactions. Strong written communication required. Experience with collectibles markets a plus.',
    PROFILE
)
print('Sample job score:')
print(score)
"
```

## Weekly Report Output

After each run write to `G:\My Drive\Projects\_studio\market-report.json`:

```json
{
  "generated": "2026-03-18",
  "ebay": {
    "items_priced": 20,
    "avg_comp_count": 8,
    "total_potential_revenue": 847.50
  },
  "jobs": {
    "new_listings": 14,
    "top_match": "Remote Fraud Analyst — Whatnot (9/10)",
    "applied_this_week": 0
  }
}
```

## Add to studio-config.json
```json
"ebay_app_id": "YOUR-EBAY-APP-ID",
"ebay_cert_id": "YOUR-EBAY-CERT-ID",
"adzuna_app_id": "YOUR-ADZUNA-ID",
"adzuna_api_key": "YOUR-ADZUNA-KEY"
```

Get eBay keys: developer.ebay.com → My Account → Application Access Keys
Get Adzuna keys: developer.adzuna.com (free, 100 calls/day)

## Gateway Routing
| Task | Route | Cost |
|---|---|---|
| eBay Finding API | Python direct | FREE (dev account) |
| eBay Browse API | Python direct | FREE (dev account) |
| Indeed RSS | Python direct | FREE |
| Adzuna job search | Python direct | FREE tier |
| Job scoring | Ollama local | FREE |
| Batch pricing | Python + Ollama | FREE |
| Weekly summary | Gemini Flash | FREE |

Total cost per weekly run: $0.00

## Running Market Scout
```
Load market-scout.md. Run weekly market data pull:
1. eBay comps for top 20 pending listing items
2. Remote job search — fraud analyst, data analyst, operations
3. Score top 10 jobs against profile
4. Write market-report.json
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
