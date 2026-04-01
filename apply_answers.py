import sys, json, os
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

STUDIO = 'G:/My Drive/Projects/_studio'

answers = {
    "sre-warn-20260331": {"answer": "Fix now", "ts": "2026-04-01T04:59:54.205Z"},
    "state-acuscan-ar-1653fa6d": {"answer": "Yes, productize it", "ts": "2026-04-01T05:00:26.797Z"},
    "state-arbitrage-pulse-efb8d39d": {"answer": "Tennessee all the time, Illinois when I tell you I am going back home", "ts": "2026-04-01T05:01:07.767Z"},
    "state-arbitrage-pulse-35ebbf89": {"answer": "dismiss till I have a list or items I am looking for. Right now is garage sale season coming... I source more there during that season.. so later when I am looking I will set some up. New project is going to gather Facebook arbitrage... so that may make this further backseat", "ts": "2026-04-01T05:03:02.437Z"},
    "state-arbitrage-pulse-16662fe7": {"answer": "if it is at 40% it is plus 20-25% and fees/taxes so if we invest that much in one item, it has to have a high sell through rate", "ts": "2026-04-01T05:04:21.211Z"},
    "state-nutrimind-86664a3a": {"answer": "All planned features working", "ts": "2026-04-01T05:04:50.301Z"},
    "state-squeeze-empire-74ccd928": {"answer": "Reset each time", "ts": "2026-04-01T05:04:58.307Z"},
    "state-squeeze-empire-f54344c9": {"answer": "Need to setup miro fish to play rounds of games to play all aspects and give feedback to version 1.0 then use that feedback to keep applying logical updates. Then once social media is going, we can turn this over there to market and post and monitor statistics of game play", "ts": "2026-04-01T05:06:48.308Z"}
}

# Load files
mob_path = STUDIO + '/mobile-inbox.json'
dl_path  = STUDIO + '/decision-log.json'
sup_path = STUDIO + '/supervisor-inbox.json'

mob = json.load(open(mob_path, encoding='utf-8'))
dl_raw  = json.load(open(dl_path,  encoding='utf-8')) if os.path.exists(dl_path) else {}
dl = dl_raw.get('decisions', dl_raw.get('entries', [])) if isinstance(dl_raw, dict) else dl_raw
sup = json.load(open(sup_path, encoding='utf-8')) if os.path.exists(sup_path) else []
sup_list = sup if isinstance(sup, list) else sup.get('items', [])

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
mob_updated = 0
sup_updated = 0

# Apply to mobile-inbox.json
for item in mob:
    iid = item.get('id','')
    if iid in answers and item.get('status') not in ('answered','resolved','RESOLVED'):
        item['status'] = 'answered'
        item['answer'] = answers[iid]['answer']
        item['answered_at'] = answers[iid]['ts']
        item['answered_via'] = 'sidebar-localStorage'
        mob_updated += 1
        dl.append({
            'id': iid,
            'project': item.get('project',''),
            'question': item.get('question','')[:100],
            'answer': answers[iid]['answer'],
            'date': answers[iid]['ts'],
            'source': 'sidebar'
        })

# Apply to supervisor-inbox.json (for SRE warning)
sup_updated_list = []
for item in sup_list:
    iid = item.get('id','')
    if iid in answers and item.get('status') not in ('answered','resolved','RESOLVED'):
        item['status'] = 'answered'
        item['answer'] = answers[iid]['answer']
        item['answered_at'] = answers[iid]['ts']
        sup_updated += 1
        dl.append({
            'id': iid,
            'project': item.get('project','studio'),
            'question': item.get('title','')[:100],
            'answer': answers[iid]['answer'],
            'date': answers[iid]['ts'],
            'source': 'sidebar'
        })

# Write back
json.dump(mob, open(mob_path, 'w', encoding='utf-8'), indent=2)
if isinstance(dl_raw, dict):
    dl_raw['decisions'] = dl
    json.dump(dl_raw, open(dl_path, 'w', encoding='utf-8'), indent=2)
else:
    json.dump(dl, open(dl_path, 'w', encoding='utf-8'), indent=2)

# Write supervisor back in original format
if isinstance(sup, dict):
    sup['items'] = sup_list
    json.dump(sup, open(sup_path, 'w', encoding='utf-8'), indent=2)
else:
    json.dump(sup_list, open(sup_path, 'w', encoding='utf-8'), indent=2)

print('mobile-inbox updated: ' + str(mob_updated))
print('supervisor-inbox updated: ' + str(sup_updated))
print('decision-log entries added: ' + str(mob_updated + sup_updated))
print()

# Verify - show remaining pending
pending = [i for i in mob if i.get('status') not in ('answered','resolved','RESOLVED','auto-resolved','build','done')]
print('Remaining pending in mobile-inbox: ' + str(len(pending)))
for i in pending:
    print('  [' + i.get('project','?') + '] ' + i.get('question','')[:60])
