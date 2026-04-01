import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
STUDIO = 'G:/My Drive/Projects/_studio'

# Check mobile-inbox.json
mob = json.load(open(STUDIO + '/mobile-inbox.json', encoding='utf-8'))
RESOLVED = ('resolved','RESOLVED','auto-resolved','build','done','DONE')
pending = [i for i in mob if i.get('status') not in RESOLVED]
answered = [i for i in mob if i.get('status') in ('answered',)]
print('=== mobile-inbox.json ===')
print('Total:', len(mob))
print('Pending:', len(pending))
print('Answered:', len(answered))
for i in pending:
    print('  [' + i.get('project','?') + '] ' + i.get('question','')[:65])

# Check supervisor-inbox.json
sup = json.load(open(STUDIO + '/supervisor-inbox.json', encoding='utf-8'))
sup_list = sup if isinstance(sup, list) else sup.get('items', [])
sup_pending = [i for i in sup_list if i.get('status') not in RESOLVED]
print()
print('=== supervisor-inbox.json ===')
print('Total:', len(sup_list), '  Pending:', len(sup_pending))
for i in sup_pending:
    print('  [' + i.get('urgency','?') + '] ' + i.get('title','')[:65])

# Check decision-log.json for recent entries
dl_path = STUDIO + '/decision-log.json'
if os.path.exists(dl_path):
    dl = json.load(open(dl_path, encoding='utf-8'))
    entries = dl if isinstance(dl, list) else dl.get('decisions', dl.get('entries', []))
    print()
    print('=== decision-log.json (' + str(len(entries)) + ' entries) ===')
    for e in entries[-5:]:
        print('  ' + str(e.get('date',''))[:10] + ' [' + str(e.get('project','?')) + '] ' + str(e.get('question', e.get('decision','?')))[:60])

# Check state.json for each project
print()
print('=== Project state.json files ===')
for proj_dir in os.listdir('G:/My Drive/Projects'):
    state_path = 'G:/My Drive/Projects/' + proj_dir + '/state.json'
    if os.path.exists(state_path):
        try:
            s = json.load(open(state_path, encoding='utf-8'))
            pending_q = s.get('pending_questions', s.get('decisions', []))
            if pending_q:
                plist = [q for q in pending_q if isinstance(q, dict) and q.get('status') not in RESOLVED]
                if plist:
                    print('  ' + proj_dir + ': ' + str(len(plist)) + ' pending')
                    for q in plist[:2]:
                        print('    - ' + str(q.get('question', q.get('text','?')))[:60])
        except: pass
