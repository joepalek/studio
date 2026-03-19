# INBOX MANAGER — DAILY SYNC AGENT

## Role
You are the Inbox Manager. You maintain the single source of truth for all
pending decisions, questions, and actions across every studio project.
You pull from Supabase (mobile answers), state.json files (project questions),
and agent outputs (whiteboard top picks, supervisor proposals).

You run on Python only — zero LLM needed. Cost: $0.00.

## Files
- `mobile-inbox.json` — list of items shown on mobile UI (truth source for display)
- `inbox-ledger.json` — full history: all items ever added, answered, resolved
- `supervisor-inbox.json` — scraper failures and agent errors needing fix
- Supabase `mobile_answers` table — answers submitted from phone

## Daily Sync — 7 Passes

### Pass 1 — Count pending items from all state.json files
```python
import json, os

PROJECTS_ROOT = 'G:/My Drive/Projects'
PROJECTS = [
    'acuscan-ar', 'arbitrage-pulse', 'CTW', 'hibid-analyzer', 'job-match',
    'listing-optimizer', 'nutrimind', 'sentinel-core', 'sentinel-performer',
    'sentinel-viewer', 'squeeze-empire', 'whatnot-apps', '_studio',
    'ghost-book', 'sysguard', 'watchdog',
]

all_pending = []
for p in PROJECTS:
    for fname in [f'{p}-state.json', 'state.json']:
        path = os.path.join(PROJECTS_ROOT, p, fname)
        if os.path.exists(path):
            try:
                d = json.load(open(path, encoding='utf-8', errors='replace'))
                for q in d.get('questions', d.get('pending_questions', [])):
                    all_pending.append({'project': p, 'question': q})
            except Exception:
                pass
            break

print(f'Pass 1: {len(all_pending)} pending questions from state.json files')
```

### Pass 2 — Fetch and apply Supabase answers
```python
import json, urllib.request
from datetime import datetime

c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
key = c.get('supabase_anon_key', '')
url = c.get('supabase_url', '')
if not key or not url:
    print('Pass 2: Supabase not configured — skip')
else:
    req = urllib.request.Request(
        url + '/rest/v1/mobile_answers?order=submitted_at.desc&limit=50',
        headers={'apikey': key, 'Authorization': 'Bearer ' + key}
    )
    r = urllib.request.urlopen(req, timeout=8)
    rows = json.loads(r.read())
    print(f'Pass 2: {len(rows)} answer sessions in Supabase')
    for row in rows:
        answers = row.get('answers', {})
        submitted = row.get('submitted_at', '')[:19]
        session = row.get('session_id', '')
        print(f'  session={session} answers={len(answers)} submitted={submitted}')
        for q_id, answer in answers.items():
            print(f'    {q_id}: {str(answer)[:60]}')
```

### Pass 3 — Apply answers to mobile-inbox.json
```python
# Match answer keys to inbox item IDs, mark as answered
INBOX_PATH = 'G:/My Drive/Projects/_studio/mobile-inbox.json'
inbox = json.load(open(INBOX_PATH, encoding='utf-8'))
applied = 0
for row in rows:
    for q_id, answer in row.get('answers', {}).items():
        for item in inbox:
            if item.get('id') == q_id and item.get('status') == 'pending':
                item['status'] = 'answered'
                item['answer'] = answer
                item['answered_at'] = row.get('submitted_at', '')[:19]
                applied += 1
print(f'Pass 3: {applied} answers applied to inbox items')
json.dump(inbox, open(INBOX_PATH, 'w'), indent=2, ensure_ascii=False)
```

### Pass 4 — Clean resolved questions (archive non-pending)
```python
# Items answered >7 days ago: move to inbox-ledger, remove from active inbox
from datetime import datetime, timedelta

LEDGER_PATH = 'G:/My Drive/Projects/_studio/inbox-ledger.json'
ledger = json.load(open(LEDGER_PATH)) if os.path.exists(LEDGER_PATH) else {'archived': [], 'stats': {}}

cutoff = (datetime.now() - timedelta(days=7)).isoformat()
to_archive = []
to_keep = []

for item in inbox:
    answered_at = item.get('answered_at', '')
    if item.get('status') == 'answered' and answered_at and answered_at < cutoff:
        to_archive.append(item)
    else:
        to_keep.append(item)

ledger['archived'].extend(to_archive)
print(f'Pass 4: {len(to_archive)} items archived to ledger, {len(to_keep)} remain active')
```

### Pass 5 — Update inbox-ledger.json
```python
ledger['stats'] = {
    'last_sync': datetime.now().isoformat(),
    'total_archived': len(ledger['archived']),
    'active_count': len(to_keep),
    'pending_count': sum(1 for i in to_keep if i.get('status') == 'pending'),
    'answered_count': sum(1 for i in to_keep if i.get('status') == 'answered'),
}
json.dump(ledger, open(LEDGER_PATH, 'w'), indent=2, ensure_ascii=False)
print(f'Pass 5: inbox-ledger.json updated — {len(ledger["archived"])} archived total')
```

### Pass 6 — Regenerate mobile-inbox.json from ground truth
```python
# Rebuild active inbox: keep pending + recently answered (last 7 days) + add new from state files
new_items = []
existing_ids = {i['id'] for i in to_keep}

# Add questions from state.json files not already in inbox
for pq in all_pending:
    q_id = f'state-{pq["project"]}-{hash(pq["question"]) % 99999}'
    if q_id not in existing_ids:
        new_items.append({
            'id': q_id,
            'project': pq['project'],
            'question': pq['question'],
            'type': 'project_question',
            'status': 'pending',
            'created': datetime.now().isoformat()[:10],
        })
        existing_ids.add(q_id)

final_inbox = to_keep + new_items
json.dump(final_inbox, open(INBOX_PATH, 'w'), indent=2, ensure_ascii=False)
print(f'Pass 6: mobile-inbox.json regenerated — {len(final_inbox)} items ({len(new_items)} new)')
```

### Pass 7 — Push to GitHub + update session-status.json
```python
import subprocess, sys
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from session_logger import update_status

subprocess.run(['git', '-C', 'G:/My Drive/Projects/_studio', 'add',
                'mobile-inbox.json', 'inbox-ledger.json'], check=True)
result = subprocess.run(
    ['git', '-C', 'G:/My Drive/Projects/_studio', 'diff', '--cached', '--stat'],
    capture_output=True, text=True
)
if result.stdout.strip():
    subprocess.run(['git', '-C', 'G:/My Drive/Projects/_studio', 'commit',
                    '-m', 'chore(inbox): daily sync'], check=True)
    subprocess.run(['git', '-C', 'G:/My Drive/Projects/_studio', 'push',
                    'origin', 'master'], check=True)
    print('Pass 7: pushed to GitHub')
else:
    print('Pass 7: no changes to push')

update_status(
    add_completed=[f'inbox-manager daily sync: {len(final_inbox)} active, {applied} answers applied'],
    next_recommended='Check mobile-inbox for pending whiteboard decisions',
)
```

## Running Inbox Manager
```
Load inbox-manager.md. Run daily sync now.
```

## Schedule
Add to Windows Task Scheduler: daily at 08:00 alongside orchestrator-briefing.bat
```
python "G:/My Drive/Projects/_studio/inbox_manager_sync.py"
```
