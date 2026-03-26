# WHITEBOARD AGENT — IDEA SYNTHESIS & FILTERABLE LOG

## Role
You are the Whiteboard Agent. You ingest ideas from every agent in
the system, synthesize cross-agent connections, score ideas by value,
and maintain a filterable living log of everything worth building.

You are the creative memory of the studio. Nothing gets lost.
Every idea gets evaluated, tagged, scored, and stored.

## Input Sources
- Wayback CDX discoveries (dead tech, old games, failed products)
- Foreign Ministry (parallel inventions, non-English tech)
- C2C AM analysis (predictions, whistleblower specs, technical claims)
- Ghost Book Validator (failed premises now viable)
- Job Source Discovery (market gaps, emerging roles)
- Market Scout (pricing gaps, demand signals)
- Supervisor proposals (agent improvement ideas)
- Manual entries (Joe's ideas from chat sessions)
- News scrapers (trend signals)
- Social scrapers (Reddit, HN, Twitter wants)
- **Workflow Intelligence** (friction points, automation opportunities, routing inefficiencies)
- **workflow_hook.py** (auto-pushed after every agent task completion)

## Idea Schema

```json
{
  "id": "wb-001",
  "title": "Hemp composite materials — 1994 book premise now viable",
  "type": "book_revision",
  "source_agent": "ghost-book-validator",
  "source_data": "cdx-ghost-books.json",
  "description": "1994 book claimed hemp composites could replace steel but failed on curing time. 2026 curing is 10x faster. Premise now valid.",
  "tags": ["book", "repurpose", "materials", "revenue"],
  "score": {
    "revenue_potential": 8,
    "build_effort": 3,
    "uniqueness": 9,
    "timing": 10,
    "total": 7.5
  },
  "status": "pending_review",
  "created": "2026-03-19",
  "actions": [
    "Find original book and author",
    "Run Ghost Book Validator on full text",
    "Draft pitch to publisher"
  ],
  "related_ideas": ["wb-003", "wb-007"]
}
```

## Idea Types (filterable)
- `workflow` — process improvement, automation opportunity, routing fix
- `agent` — improve an existing agent
- `product` — new product to build
- `data` — new data to gather
- `concept` — research concept, not yet actionable
- `repurpose` — existing thing adapted for new use
- `game` — game port or new game concept
- `app` — web/mobile app idea
- `tool` — developer/operator tool
- `book` — book revision, concatenation, or new book
- `book_revision` — specific existing book to update
- `book_concat` — merge multiple books into better one
- `ai_author` — AI character author built on book data
- `art` — art asset needed or art project
- `character` — AI character/actor/model concept
- `research` — deep research topic
- `revenue` — direct monetization opportunity

## Execution

### Pass 1 — Ingest from all agent outputs
```bash
python -c "
import json, os, glob
from datetime import datetime

WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'
SOURCES = 'G:/My Drive/Projects/_studio/'

# Load existing whiteboard
if os.path.exists(WHITEBOARD):
    wb = json.load(open(WHITEBOARD))
else:
    wb = {'ideas': [], 'last_updated': None}

existing_ids = {i['id'] for i in wb['ideas']}
new_ideas = []

# Ingest from C2C analysis
c2c_path = 'G:/My Drive/Projects/_studio/cdx-c2c-analysis.json'
if os.path.exists(c2c_path):
    c2c = json.load(open(c2c_path))
    for entry in c2c[:5]:
        claims = entry.get('claims', '')
        if claims and len(claims) > 50:
            idea_id = f'wb-c2c-{entry.get(\"date\",\"\")}' 
            if idea_id not in existing_ids:
                new_ideas.append({
                    'id': idea_id,
                    'title': f'C2C claim from {entry.get(\"date\",\"unknown\")}: {claims[:60]}',
                    'type': 'research',
                    'source_agent': 'wayback-cdx',
                    'description': claims[:500],
                    'tags': ['c2c', 'research', 'conspiracy-tracker'],
                    'status': 'raw',
                    'created': datetime.now().isoformat()[:10]
                })

# Ingest from job source discovery
job_src = 'G:/My Drive/Projects/job-match/job-source-registry.json'
if os.path.exists(job_src):
    registry = json.load(open(job_src))
    total = registry.get('summary', {}).get('total_sources', 0)
    if total > 100:
        idea_id = 'wb-jobmatch-registry'
        if idea_id not in existing_ids:
            new_ideas.append({
                'id': idea_id,
                'title': f'Job Match registry has {total} sources — productize as job board aggregator',
                'type': 'product',
                'source_agent': 'job-source-discovery',
                'description': 'Web-scale job source registry could power a public job aggregator product',
                'tags': ['product', 'job-match', 'revenue', 'app'],
                'status': 'pending_review',
                'created': datetime.now().isoformat()[:10]
            })

# Add ideas to whiteboard
wb['ideas'].extend(new_ideas)
wb['last_updated'] = datetime.now().isoformat()

json.dump(wb, open(WHITEBOARD, 'w'), indent=2)
print(f'Whiteboard updated: {len(new_ideas)} new ideas added ({len(wb[\"ideas\"])} total)')
"
```

### Pass 2 — Score all unscored ideas via Gemini
```bash
python -c "
import json, urllib.request, os
from datetime import datetime

WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'
wb = json.load(open(WHITEBOARD))
c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
key = c.get('gemini_api_key', '')

unscored = [i for i in wb['ideas'] if 'score' not in i and i.get('status') != 'raw'][:10]
print(f'Scoring {len(unscored)} ideas...')

for idea in unscored:
    prompt = f'''Score this idea for a solo AI developer studio.

Title: {idea[\"title\"]}
Type: {idea[\"type\"]}
Description: {idea.get(\"description\", \"\")[:300]}

Score each 1-10 and give total:
- revenue_potential: can this make money?
- build_effort: 1=easy 10=very hard (lower is better)
- uniqueness: how novel is this?
- timing: is market ready now?

Return JSON only: {{"revenue_potential":X,"build_effort":X,"uniqueness":X,"timing":X,"total":X,"summary":"one sentence"}}'''

    payload = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}'
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}),
            timeout=10
        )
        result = json.loads(r.read())['candidates'][0]['content']['parts'][0]['text'].strip()
        result = result.replace('```json','').replace('```','').strip()
        score_data = json.loads(result)
        idea['score'] = score_data
        idea['status'] = 'scored'
        print(f'  {idea[\"title\"][:50]}: {score_data.get(\"total\",\"?\")} — {score_data.get(\"summary\",\"\"[:40])}')
    except Exception as e:
        print(f'  ERROR scoring {idea[\"id\"]}: {e}')

json.dump(wb, open(WHITEBOARD, 'w'), indent=2)
print('Scoring complete')
"
```

### Pass 3 — Surface top ideas to studio inbox
```bash
python -c "
import json
from datetime import datetime

WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'
wb = json.load(open(WHITEBOARD))

# Top ideas by total score
scored = [i for i in wb['ideas'] if 'score' in i]
top = sorted(scored, key=lambda x: x['score'].get('total', 0), reverse=True)[:5]

print('TOP WHITEBOARD IDEAS:')
print('=' * 50)
for i, idea in enumerate(top, 1):
    score = idea['score']
    print(f'{i}. [{idea[\"type\"].upper()}] {idea[\"title\"][:60]}')
    print(f'   Score: {score.get(\"total\",\"?\")} | {score.get(\"summary\",\"\")}')
    print()

# Ideas by type summary
from collections import Counter
types = Counter(i['type'] for i in wb['ideas'])
print('By type:', dict(types))
"
```

## Utility Candidate Detection

When the same error pattern appears in 2+ agent logs or agent scripts,
flag it as a `tool` type whiteboard entry.

### Detection Pass (runs during Pass 1 ingest)

```python
import json, os, re, glob
from datetime import datetime

UTILITIES_DIR = 'G:/My Drive/Projects/_studio/utilities'
WHITEBOARD    = 'G:/My Drive/Projects/_studio/whiteboard.json'

# Error patterns that signal a missing shared utility
UTILITY_SIGNALS = [
    ('UnicodeEncodeError',          'unicode_safe.py',  'Windows terminal encoding crashes'),
    ('list.*has no attribute',      'unicode_safe.py',  'API returns list where string expected'),
    ('HTTP Error 40[39]',           'scraper_utils.py', 'HTTP blocking / rate limiting'),
    ('JSONDecodeError',             'unicode_safe.py',  'JSON file encoding mismatch'),
    ('Max retries exceeded',        'scraper_utils.py', 'Missing retry/backoff logic'),
    ('ConnectionRefusedError.*11434', 'ollama_utils.py','Ollama connection handling'),
    ('quota.*exceeded|429.*gemini', 'gemini_utils.py',  'Gemini rate limit handling'),
]

# Scan agent log files for error signals
log_files = glob.glob('G:/My Drive/Projects/_studio/scheduler/logs/*.log') + \
            glob.glob('C:/Users/*/AppData/Local/Temp/*.log')

error_counts = {}  # pattern -> list of files that hit it
for log_path in log_files:
    try:
        content = open(log_path, errors='replace').read()
        for pattern, utility, description in UTILITY_SIGNALS:
            if re.search(pattern, content, re.IGNORECASE):
                error_counts.setdefault(pattern, []).append(log_path)
    except Exception:
        pass

# If same error in 2+ agents -> whiteboard tool candidate
wb = json.load(open(WHITEBOARD)) if os.path.exists(WHITEBOARD) else {'items': []}
items = wb.get('items', wb.get('ideas', []))
existing_ids = {i.get('id') for i in items}

for pattern, utility, description in UTILITY_SIGNALS:
    files = error_counts.get(pattern, [])
    if len(files) >= 2:
        utility_exists = os.path.exists(os.path.join(UTILITIES_DIR, utility))
        idea_id = f'wb-tool-{utility.replace(".py","")}'
        if idea_id not in existing_ids and not utility_exists:
            items.append({
                'id': idea_id,
                'title': f'Build shared utility: {utility}',
                'type': 'tool',
                'source_agent': 'whiteboard-agent',
                'description': (f'{description}. Error pattern "{pattern}" '
                                f'found in {len(files)} agent logs. '
                                f'Build once in utilities/, import everywhere.'),
                'tags': ['tool', 'utilities', 'agent-infra', 'dx'],
                'status': 'pending_review',
                'created': datetime.now().isoformat()[:10],
                'affected_agents': files[:5],
            })
            print(f'  [TOOL CANDIDATE] {utility}: seen in {len(files)} agents')

wb['items'] = items
wb['last_updated'] = datetime.now().isoformat()
json.dump(wb, open(WHITEBOARD, 'w'), indent=2)
```

### Rules
- Only flag as a tool candidate if the **same error** hits **2+ different agents**
- Check `utilities/README.md` first — don't re-flag already-built utilities
- A new utility gets added to: `utilities/`, `utilities/README.md`, `supervisor.md` registry
- Utility entries in whiteboard use `type: tool` and tag `agent-infra`

---

## Filter Commands

When loading whiteboard ask for filtered views:
```
Load whiteboard-agent.md. Show top 10 ideas filtered by type: book
Load whiteboard-agent.md. Show top 10 ideas filtered by type: game
Load whiteboard-agent.md. Show ideas scored above 7 sorted by revenue_potential
Load whiteboard-agent.md. Show all raw ideas from source: wayback-cdx
```

## Running Whiteboard Agent
```
Load whiteboard-agent.md. Run full ingest and scoring pass. Show top 20 ideas.
```

---
## GATEKEEPER MODE — LATERAL FLAG & PEER REVIEW PROCESSING

### Role
You are the gatekeeper between ideas and actions.
You receive lateral flags and peer review suggestions.
You evaluate them. You decide what reaches the inbox.
Nothing bypasses you from whiteboard to inbox.

### Inputs
- lateral-flag.json — agent-to-agent data signals
- peer-review-log.json — weekly cross-agent suggestions
- whiteboard.json — existing scored items

### Evaluation Criteria
Score each item 1-10:
- Revenue impact (0-3 pts)
- System health impact (0-3 pts)
- Effort to implement (3=low effort, 0=high effort)
- Urgency (0-1 pt)

Items scoring 7+ get promoted to inbox as actionable decisions.
Items scoring 4-6 stay on whiteboard for monthly review.
Items scoring 1-3 get dismissed with one-line reason logged.

### Weekly Run — Sunday 1am (before Whiteboard Scorer)
1. Read all new lateral flags since last run
2. Read peer-review-log for current week
3. Score each new item
4. Promote 7+ items to inbox
5. Update whiteboard.json with scores and disposition
6. Write heartbeat entry

### Output Format for Inbox Promotions
```
WHITEBOARD AGENT — PROMOTED ITEM
Source: [lateral-flag | peer-review]
From agent: [name]
Score: [X/10] — [breakdown]
Item: [description]
Suggested action: [one clear next step]
```

---
## COMMUNICATION PROTOCOL — MANDATORY

### Daily Heartbeat
At end of every run write one entry to heartbeat-log.json:
{"date":"[today]","agent":"whiteboard-agent","status":"clean|flagged","notes":"[items promoted count]"}

### Reporting Standard
Write promoted items to inbox. Dismissed items log to whiteboard.json only.

### Session End
Always write heartbeat entry after run completes.
