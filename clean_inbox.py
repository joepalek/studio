import json

f = 'G:/My Drive/Projects/_studio/mobile-inbox.json'
d = json.load(open(f, encoding='utf-8'))

# Mark as resolved the decisions answered today in this session
resolved_ids = {
    # job-match - all 4 answered
    'state-job-match-14ffdba1',  # SaaS - answered: SaaS with role-based login
    'state-job-match-79f41ad6',  # employer portal - answered: scraping first
    'state-job-match-379b1402',  # scam db - answered: private
    'state-job-match-0472d4af',  # ratings - answered: dual-axis in v1
    # listing-optimizer - all 5 answered
    'state-listing-optimizer-c159724f',  # personal first
    'state-listing-optimizer-0b8aae0b',  # CSV only
    'state-listing-optimizer-2f37099d',  # SKU: location-based
    'state-listing-optimizer-9609b02c',  # categories: vintage/electronics/books/home
    'state-listing-optimizer-2c74ef17',  # price suggestions: yes
    # whatnot-apps - answered/submitted
    'state-whatnot-apps-c3ac17b9',
    'state-whatnot-apps-26e411a4',
    'state-whatnot-apps-8413a3f4',
}

changed = 0
for item in d:
    if item.get('id') in resolved_ids and item.get('status') == 'pending':
        item['status'] = 'resolved'
        item['resolved_date'] = '2026-03-31'
        changed += 1

print('Marked resolved:', changed)
json.dump(d, open(f, 'w', encoding='utf-8'), indent=2)

# Show remaining unresolved
unresolved = [i for i in d if i.get('status') not in ('resolved','RESOLVED','auto-resolved')]
print('Remaining pending:', len(unresolved))
for i in unresolved:
    print(' -', i.get('project','?'), '|', i.get('question','?')[:70])
