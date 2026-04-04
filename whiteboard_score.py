
# EXPECTED_RUNTIME_SECONDS: 180
import json, time, os, sys
sys.path.insert(0, "G:/My Drive/Projects/_studio")
from datetime import datetime
from ai_gateway import score as gw_score

WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'
INBOX_KEY = 'studio_inbox_items'

wb = json.load(open(WHITEBOARD, encoding='utf-8', errors='replace'))
items = wb.get('items', [])

unscored = [i for i in items if not i.get('gemini_score')]
print(f'Whiteboard: {len(items)} total, {len(unscored)} unscored')

def score_item(item):
    prompt = f"""Score this product/book/idea for 2026 build or publish viability.

Type: {item.get('type', 'unknown')}
Title: {item.get('title', '')}
Description: {item.get('description', '')}
Tags: {', '.join(item.get('tags', []))}
Source: {item.get('source', '')}
Decade origin: {item.get('decade_origin', 'N/A')}
Why failed: {item.get('why_failed', 'N/A')}
Signal: {item.get('signal', item.get('review_signal', 'N/A'))}

Return ONLY valid JSON:
{{
  "total_score": 1-10,
  "market_gap_score": 1-10,
  "build_feasibility": 1-10,
  "revenue_potential": 1-10,
  "urgency": 1-10,
  "why_now": "one sentence on why 2026 is the right time",
  "recommended_action": "BUILD/PUBLISH/PITCH/RESEARCH/KILL",
  "effort_estimate": "days/weeks/months",
  "revenue_estimate": "LARGE/MEDIUM/SMALL/NICHE",
  "top_risk": "biggest single risk"
}}"""
    r = gw_score(prompt, max_tokens=300)
    if not r.success:
        raise Exception(r.error or "gateway returned no response")
    text = r.text.replace('```json', '').replace('```', '').strip()
    return json.loads(text), r.provider

print('Scoring via Gemini...\n')
scored_count = 0
consecutive_failures = 0
MAX_CONSECUTIVE_FAILURES = 3
for item in unscored:
    title = item.get('title', 'Unknown')[:50]
    try:
        score, provider = score_item(item)
        item['gemini_score'] = score
        item['scored_at'] = datetime.now().isoformat()
        item['scored_by'] = provider
        scored_count += 1
        total = score.get('total_score', 0)
        action = score.get('recommended_action', '?')
        print(f'  {total:>2}/10 [{action:<8}] {title} (via {provider})')
        consecutive_failures = 0  # reset on success
    except Exception as e:
        err = str(e)[:50]
        print(f'  ERROR: {title}: {err}')
        consecutive_failures += 1
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            print(f'  CIRCUIT BREAKER: {MAX_CONSECUTIVE_FAILURES} consecutive failures — aborting to avoid API waste')
            break
        if '429' in err or 'quota' in err.lower():
            print('  Rate limit -- pausing 30s')
            time.sleep(30)
    time.sleep(4)

# Save scored whiteboard
wb['updated'] = datetime.now().isoformat()
json.dump(wb, open(WHITEBOARD, 'w', encoding='utf-8'), indent=2)
print(f'\nScored {scored_count} items. Saved whiteboard.json')

# Find top 10 by total_score
all_scored = [i for i in items if i.get('gemini_score')]
all_scored.sort(key=lambda x: x.get('gemini_score', {}).get('total_score', 0), reverse=True)
top10 = all_scored[:10]

print(f'\n=== TOP 10 WHITEBOARD ITEMS ===')
for rank, item in enumerate(top10, 1):
    sc = item.get('gemini_score', {})
    print(f'  #{rank} [{sc.get("total_score",0)}/10] {item.get("title","")[:50]}')
    print(f'       {sc.get("recommended_action","?")} | {sc.get("why_now","")[:60]}')

# Push top 10 to studio inbox
INBOX_PATH = 'G:/My Drive/Projects/_studio/mobile-inbox.json'
inbox_list = json.load(open(INBOX_PATH, encoding='utf-8')) if os.path.exists(INBOX_PATH) else []
if isinstance(inbox_list, dict):
    inbox_list = inbox_list.get('questions', inbox_list.get('items', []))
existing_ids = {q.get('id') for q in inbox_list if isinstance(q, dict)}

pushed = 0
for rank, item in enumerate(top10, 1):
    sc = item.get('gemini_score', {})
    item_id = f'wb-top-{item.get("id","")}'
    if item_id in existing_ids:
        continue
    inbox_list.append({
        'id': item_id,
        'type': 'whiteboard_top10',
        'project': '_studio',
        'question': f'[#{rank} WHITEBOARD] {item.get("title","")}',
        'context': (f'{sc.get("recommended_action","?")} | Score: {sc.get("total_score",0)}/10 | '
                    f'{sc.get("why_now","")}'
                    f' | Est: {sc.get("effort_estimate","?")} | '
                    f'Revenue: {sc.get("revenue_estimate","?")} | Risk: {sc.get("top_risk","")}'),
        'decision_type': 'proactive',
        'priority': 'high' if sc.get('total_score', 0) >= 8 else 'medium',
        'created': datetime.now().isoformat(),
        'status': 'pending'
    })
    existing_ids.add(item_id)
    pushed += 1

json.dump(inbox_list, open(INBOX_PATH, 'w', encoding='utf-8'), indent=2)
print(f'\nPushed {pushed} top-10 items to mobile-inbox.json')

# Heartbeat
import sys; sys.path.insert(0, 'G:/My Drive/Projects/_studio')

import sys as _sys
_sys.path.insert(0, "G:/My Drive/Projects/_studio/utilities")
from constraint_gates import hamilton_watchdog
try:
    from utilities.heartbeat import write as hb_write
    hb_write('whiteboard-scorer', 'clean', f'scored={scored_count} top10_pushed={pushed}')
except Exception as e: print('[heartbeat] ' + str(e)[:60])

print('Done.')
