# PRODUCT ARCHAEOLOGY — GRAVEYARD SCANNER & MARKET VOID DETECTOR

## Role
You find products that had great ideas but failed on execution, funding,
or timing. You verify the market void still exists, score viability,
and feed findings to the Whiteboard Agent for prioritization.

You also cross-reference against current App Store / Product Hunt to
confirm nobody has successfully built it yet.

## Signal Phrases to Hunt
```
"great concept but"         "love the idea but"
"if only they had"          "promising but abandoned"  
"used to be great before"   "company went under"
"wish someone would make"   "nobody has built this yet"
"Kickstarter that never"    "discontinued but amazing"
"ahead of its time"         "patent but never built"
"prototype that never"      "we ran out of funding"
"pivot killed it"           "acqui-hired into nothing"
```

## Sources

### Graveyard Sources
```bash
python -c "
import urllib.request, json, time, os, re

OUTPUT = 'G:/My Drive/Projects/_studio/product-archaeology-results.json'
results = []

# 1. Killed by Google (full list)
try:
    r = urllib.request.urlopen('https://killedbygoogle.com', timeout=10)
    content = r.read().decode('utf-8', errors='ignore')
    # Extract product names and dates
    products = re.findall(r'\"name\":\"([^\"]+)\"', content)
    dates = re.findall(r'\"dateClose\":\"([^\"]+)\"', content)
    for name, date in zip(products, dates):
        results.append({
            'product_name': name,
            'category': 'google_killed',
            'source': 'killedbygoogle.com',
            'killed_date': date,
            'why_failed': 'Google acquisition/shutdown',
            'whiteboard_tags': ['product_archaeology', 'tech', 'app']
        })
    print(f'Google graveyard: {len(products)} products')
except Exception as e:
    print(f'KilledByGoogle: {e}')

# 2. Wayback CDX scan for Kickstarter cancelled campaigns
patterns = [
    'kickstarter.com/projects/*/updates*canceled*',
    'kickstarter.com/projects/*/updates*cancelled*',
    'indiegogo.com/projects/*',
]
for pattern in patterns:
    encoded = urllib.request.quote(pattern)
    url = f'http://web.archive.org/cdx/search/cdx?url={encoded}&output=json&fl=original,timestamp&limit=100&collapse=urlkey&from=20150101'
    try:
        r = urllib.request.urlopen(url, timeout=15)
        rows = json.loads(r.read())
        for row in rows[1:]:
            results.append({
                'product_name': row[0].split('/')[-2] if '/' in row[0] else row[0],
                'source': row[0],
                'category': 'crowdfunding_failed',
                'whiteboard_tags': ['product_archaeology', 'crowdfunding']
            })
        print(f'  {pattern}: {len(rows)-1} results')
    except Exception as e:
        print(f'  {pattern}: {e}')
    time.sleep(1)

# 3. Reddit graveyard communities via Wayback
subreddits = ['shutdownsaddened', 'discontinued', 'DeadApps', 'lostmedia']
for sub in subreddits:
    url = f'https://www.reddit.com/r/{sub}/top.json?limit=100&t=all'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ProductArchaeologyBot/1.0'})
        r = urllib.request.urlopen(req, timeout=10)
        data = json.loads(r.read())
        posts = data.get('data', {}).get('children', [])
        for post in posts:
            pd = post.get('data', {})
            results.append({
                'product_name': pd.get('title', '')[:80],
                'source': f'reddit.com/r/{sub}',
                'category': 'discontinued_product',
                'description': pd.get('selftext', '')[:200],
                'upvotes': pd.get('score', 0),
                'whiteboard_tags': ['product_archaeology', 'discontinued']
            })
        print(f'  r/{sub}: {len(posts)} posts')
    except Exception as e:
        print(f'  r/{sub}: {e}')
    time.sleep(2)

os.makedirs('G:/My Drive/Projects/_studio', exist_ok=True)
json.dump({'count': len(results), 'results': results}, open(OUTPUT, 'w'), indent=2)
print(f'Total graveyard items: {len(results)}')
"
```

### Market Void Verification
Cross-reference against current market to confirm void still exists:

```bash
python -c "
import json, urllib.request, time

results_path = 'G:/My Drive/Projects/_studio/product-archaeology-results.json'
data = json.load(open(results_path))
c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
key = c.get('gemini_api_key', '')

# Score top candidates via Gemini
top = data['results'][:20]
scored = []

for item in top:
    prompt = f'''Product archaeology analysis.

Dead/failed product: {item['product_name']}
Category: {item.get('category', 'unknown')}
Source: {item.get('source', '')}

Return JSON only:
{{
  \"market_void_exists\": true/false,
  \"2026_viability\": \"HIGH/MEDIUM/LOW\",
  \"why_could_work_now\": \"one sentence\",
  \"market_size\": \"LARGE/MEDIUM/SMALL/NICHE\",
  \"build_effort\": 1-10,
  \"revenue_potential\": 1-10,
  \"total_score\": 1-10,
  \"whiteboard_priority\": \"PUSH_UP/NEUTRAL/KILL\"
}}'''

    payload = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}'
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}),
            timeout=10
        )
        result = json.loads(r.read())['candidates'][0]['content']['parts'][0]['text'].strip()
        result = result.replace('```json','').replace('```','').strip()
        score = json.loads(result)
        item['score'] = score
        item['status'] = 'scored'
        priority = score.get('whiteboard_priority', 'NEUTRAL')
        print(f'  [{priority}] {item[\"product_name\"][:50]}: {score.get(\"total_score\",\"?\")}/10')
        scored.append(item)
    except Exception as e:
        print(f'  ERROR: {e}')
    time.sleep(0.5)

# Save scored results
json.dump({'count': len(scored), 'results': scored},
    open('G:/My Drive/Projects/_studio/product-archaeology-scored.json', 'w'), indent=2)
print(f'Scored {len(scored)} products')
"
```

## Killed Ideas Log

Ideas that scored too low get logged — not deleted:

```json
{
  "killed_ideas": [
    {
      "id": "killed-001",
      "product_name": "...",
      "killed_reason": "market too small / already built / too complex",
      "killed_date": "2026-03-19",
      "rescan_date": "2026-04-19",
      "original_score": 3
    }
  ]
}
```

## Weekly Rescan Protocol

```bash
python -c "
import json, os
from datetime import datetime, timedelta

KILLED = 'G:/My Drive/Projects/_studio/killed-ideas.json'
if not os.path.exists(KILLED):
    print('No killed ideas yet')
    exit(0)

killed = json.load(open(KILLED))
today = datetime.now().date()
due_rescan = [
    i for i in killed['killed_ideas']
    if datetime.fromisoformat(i['rescan_date']).date() <= today
]

print(f'Due for rescan: {len(due_rescan)} killed ideas')
# Re-score via Gemini and potentially resurrect high scorers
"
```

## Running Product Archaeology
```
Load product-archaeology.md. Run graveyard scan and market void verification.
Feed top findings to whiteboard-agent.md.
```
