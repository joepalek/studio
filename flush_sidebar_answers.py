"""
flush_sidebar_answers.py
Reads sb_answers from sidebar localStorage export and writes them to mobile-inbox.json.
Run manually or add to nightly Task Scheduler after SidebarInject.
Usage: python flush_sidebar_answers.py [answers_json_string]
"""
import sys, json, os
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STUDIO = 'G:/My Drive/Projects/_studio'

# Read answers - can be passed as arg or piped
if len(sys.argv) > 1:
    answers = json.loads(sys.argv[1])
else:
    print('Usage: python flush_sidebar_answers.py \'{"id1":{"answer":"...","ts":"..."},...}\'')
    print('Or call via bridge POST /answer for live updates.')
    sys.exit(0)

mob_path = STUDIO + '/mobile-inbox.json'
mob = json.load(open(mob_path, encoding='utf-8'))
dl_path  = STUDIO + '/decision-log.json'
dl = json.load(open(dl_path, encoding='utf-8')) if os.path.exists(dl_path) else []

updated = 0
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

for item_id, data in answers.items():
    answer = data.get('answer', '')
    for item in mob:
        if item.get('id') == item_id and item.get('status') not in ('answered', 'resolved'):
            item['status'] = 'answered'
            item['answer'] = answer
            item['answered_at'] = data.get('ts', now)
            item['answered_via'] = 'sidebar-flush'
            updated += 1
            dl.append({'id': item_id, 'project': item.get('project',''), 
                       'question': item.get('question','')[:80],
                       'answer': answer, 'date': now, 'source': 'sidebar'})
            break

json.dump(mob, open(mob_path, 'w', encoding='utf-8'), indent=2)
json.dump(dl,  open(dl_path,  'w', encoding='utf-8'), indent=2)
print('Flushed ' + str(updated) + ' answers to mobile-inbox.json')
