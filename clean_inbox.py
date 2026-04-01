import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

f = 'G:/My Drive/Projects/_studio/mobile-inbox.json'
d = json.load(open(f, encoding='utf-8'))

before = len([i for i in d if i.get('status') not in ('resolved','RESOLVED','auto-resolved')])

# Mark whiteboard items as resolved - they belong in whiteboard.json, not inbox
# Also mark build-queue items (status='build') as resolved
wb_resolved = 0
build_resolved = 0
for item in d:
    iid = item.get('id', '')
    title = item.get('question', item.get('title', ''))
    status = item.get('status', '')
    
    # Whiteboard items in inbox
    if 'WHITEBOARD' in title or iid.startswith('wb-top'):
        if status not in ('resolved', 'RESOLVED'):
            item['status'] = 'resolved'
            item['resolved_date'] = '2026-03-31'
            item['resolved_note'] = 'whiteboard-not-inbox'
            wb_resolved += 1
    
    # build-queue items already actioned
    elif status == 'build':
        item['status'] = 'resolved'
        item['resolved_date'] = '2026-03-31'
        item['resolved_note'] = 'build-queue-actioned'
        build_resolved += 1

after = len([i for i in d if i.get('status') not in ('resolved','RESOLVED','auto-resolved')])

print('Whiteboard items removed from inbox: ' + str(wb_resolved))
print('Build-queue items resolved: ' + str(build_resolved))
print('Pending before: ' + str(before) + ' -> after: ' + str(after))

# Show what remains
remaining = [i for i in d if i.get('status') not in ('resolved','RESOLVED','auto-resolved')]
print()
print('Remaining ' + str(len(remaining)) + ' pending:')
for i in remaining:
    print('  [' + str(i.get('project','?')) + '] ' + str(i.get('question', i.get('title','?')))[:70])

json.dump(d, open(f, 'w', encoding='utf-8'), indent=2)
