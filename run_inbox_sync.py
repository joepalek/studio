
# EXPECTED_RUNTIME_SECONDS: 300
"""Inbox Manager Daily Sync — runs all 7 passes."""
import json, os, subprocess, sys, hashlib
from datetime import datetime, timedelta

PROJECTS_ROOT = 'G:/My Drive/Projects'
PROJECTS = [
    'acuscan-ar', 'arbitrage-pulse', 'CTW', 'hibid-analyzer', 'job-match',
    'listing-optimizer', 'nutrimind', 'sentinel-core', 'sentinel-performer',
    'sentinel-viewer', 'squeeze-empire', 'whatnot-apps', '_studio',
    'ghost-book', 'sysguard', 'watchdog',
]

# ── Pass 1 ── Count pending items from all state.json files ──────────────────
all_pending = []
for p in PROJECTS:
    for fname in [f'{p}-state.json', 'state.json']:
        path = os.path.join(PROJECTS_ROOT, p, fname)
        if os.path.exists(path):
            try:
                d = json.load(open(path, encoding='utf-8', errors='replace'))

                # Schema A: rich state (decisions + proactive_questions)
                for item in d.get('decisions', []):
                    if not item.get('answer') and not item.get('answered_date'):
                        all_pending.append({
                            'project': p,
                            'id': item.get('id', ''),
                            'question': item.get('question', ''),
                            'options': item.get('options', []),
                            'recommendation': item.get('recommendation', ''),
                            'context': item.get('context', ''),
                            'type': 'decision',
                            'decision_type': 'required',
                        })
                for item in d.get('proactive_questions', []):
                    if item.get('answer') is None:
                        all_pending.append({
                            'project': p,
                            'id': item.get('id', ''),
                            'question': item.get('question', ''),
                            'context': item.get('context', ''),
                            'unlocks': item.get('unlocks', ''),
                            'type': 'proactive',
                            'decision_type': 'proactive',
                        })

                # Schema B: simple list fields (legacy fallback)
                for q in d.get('questions', d.get('pending_questions', [])):
                    text = q if isinstance(q, str) else q.get('question', str(q))
                    all_pending.append({
                        'project': p,
                        'id': '',
                        'question': text,
                        'type': 'question',
                        'decision_type': 'proactive',
                    })

            except Exception as e:
                print(f'  WARN: could not read {path}: {e}')
            break

# Deduplicate by (project, question text)
seen_pq = set()
deduped = []
for item in all_pending:
    key = (item['project'], item['question'][:60])
    if key not in seen_pq:
        seen_pq.add(key)
        deduped.append(item)
all_pending = deduped

by_project = {}
for item in all_pending:
    by_project.setdefault(item['project'], []).append(item)
print(f'Pass 1: {len(all_pending)} unanswered items across {len(by_project)} projects')
for proj, items in sorted(by_project.items()):
    print(f'  {proj}: {len(items)} ({", ".join(set(i["type"] for i in items))})')

# ── Pass 2 ── Fetch Supabase answers ────────────────────────────────────────
import urllib.request
rows = []
try:
    c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
    key = c.get('supabase_anon_key', '')
    url = c.get('supabase_url', '')
    if not key or not url:
        print('Pass 2: Supabase not configured - skip')
    else:
        req = urllib.request.Request(
            url + '/rest/v1/mobile_answers?order=submitted_at.desc&limit=50',
            headers={'apikey': key, 'Authorization': 'Bearer ' + key}
        )
        r = urllib.request.urlopen(req, timeout=8)
        rows = json.loads(r.read())
        print(f'Pass 2: {len(rows)} answer sessions in Supabase')
        for row in rows:
            raw = row.get('answers', {})
            if isinstance(raw, str):
                try: raw = json.loads(raw)
                except: raw = {}
            answers = raw if isinstance(raw, dict) else {}
            submitted = row.get('submitted_at', '')[:19]
            session = row.get('session_id', '')
            print(f'  session={session} answers={len(answers)} submitted={submitted}')
            for q_id, answer in answers.items():
                print(f'    {q_id}: {str(answer)[:60]}')
except Exception as e:
    print(f'Pass 2: error - {e}')

# ── Pass 3 ── Apply answers to mobile-inbox.json ────────────────────────────
INBOX_PATH = 'G:/My Drive/Projects/_studio/mobile-inbox.json'
inbox = []
if os.path.exists(INBOX_PATH):
    for enc in ('utf-8', 'utf-8-sig', 'latin-1'):
        try:
            raw = open(INBOX_PATH, encoding=enc).read()
            parsed = json.loads(raw)
            inbox = parsed if isinstance(parsed, list) else []
            break
        except Exception:
            continue
    # inbox stays [] if all encodings fail (corrupt file — rebuild from state files)

applied = 0
for row in rows:
    raw_answers = row.get('answers', {})
    if isinstance(raw_answers, str):
        try: raw_answers = json.loads(raw_answers)
        except: raw_answers = {}
    for q_id, answer in (raw_answers.items() if isinstance(raw_answers, dict) else []):
        for item in inbox:
            if item.get('id') == q_id and item.get('status') == 'pending':
                item['status'] = 'answered'
                item['answer'] = answer
                item['answered_at'] = row.get('submitted_at', '')[:19]
                applied += 1
print(f'Pass 3: {applied} answers applied to inbox items')
json.dump(inbox, open(INBOX_PATH, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

# ── Pass 4 ── Archive answered items >7 days old ────────────────────────────
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

# ── Pass 5 ── Update inbox-ledger.json ──────────────────────────────────────
ledger['stats'] = {
    'last_sync': datetime.now().isoformat(),
    'total_archived': len(ledger['archived']),
    'active_count': len(to_keep),
    'pending_count': sum(1 for i in to_keep if i.get('status') == 'pending'),
    'answered_count': sum(1 for i in to_keep if i.get('status') == 'answered'),
}
json.dump(ledger, open(LEDGER_PATH, 'w'), indent=2, ensure_ascii=False)
print(f'Pass 5: inbox-ledger.json updated - {len(ledger["archived"])} archived total')

# ── Pass 6 ── Regenerate mobile-inbox.json from ground truth ────────────────
new_items = []
existing_ids = {i['id'] for i in to_keep}

for pq in all_pending:
    q_id = f'state-{pq["project"]}-{hashlib.md5(pq["question"].encode()).hexdigest()[:8]}'
    if q_id not in existing_ids:
        new_items.append({
            'id': q_id,
            'project': pq['project'],
            'question': pq['question'],
            'type': pq.get('decision_type', 'proactive'),
            'status': 'pending',
            'created': datetime.now().isoformat()[:10],
            'options': pq.get('options', []),
            'recommendation': pq.get('recommendation', ''),
            'context': pq.get('context', ''),
        })
        existing_ids.add(q_id)

final_inbox = to_keep + new_items
json.dump(final_inbox, open(INBOX_PATH, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f'Pass 6: mobile-inbox.json regenerated - {len(final_inbox)} items ({len(new_items)} new)')

# ── Pass 7 ── Push to GitHub + update status.json ───────────────────
sys.path.insert(0, 'G:/My Drive/Projects/_studio/utilities')
from session_logger import update_status

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog

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
    next_recommended='Check mobile-inbox for pending decisions',
)
print('Done.')
