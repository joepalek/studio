import urllib.request, urllib.parse, json, time, os
from datetime import datetime

BASE = 'G:/My Drive/Projects/_studio/product-archaeology'
os.makedirs(BASE, exist_ok=True)
WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'

# Nostalgia-specific signal phrases
NOSTALGIA_SIGNALS = [
    'remember when',
    'i miss',
    "they don't make",
    'they dont make',
    'bring back',
    'used to have',
    'nobody makes this anymore',
    'wish they still made',
    'discontinued this',
    'stop making',
    'stopped making',
    'used to be able to',
    'remember being able to',
    'wish i could still get',
]

findings = []

def check_signals(text):
    t = text.lower()
    for phrase in NOSTALGIA_SIGNALS:
        if phrase in t:
            return phrase
    return None

print('=== Reddit r/nostalgia — nostalgia signal scan ===')

for sort in ('top', 'hot', 'new'):
    url = f'https://www.reddit.com/r/nostalgia/{sort}.json?limit=100&t=all'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 ProductArchaeologyBot/1.0 (research)'
        })
        r = urllib.request.urlopen(req, timeout=15)
        data = json.loads(r.read())
        posts = data.get('data', {}).get('children', [])
        matched = 0
        for post in posts:
            p = post.get('data', {})
            title = p.get('title', '')
            body = p.get('selftext', '')
            combined = f'{title} {body}'
            signal = check_signals(combined)
            score = p.get('score', 0)

            if signal:
                findings.append({
                    'product_name': title[:80],
                    'category': 'nostalgia_product',
                    'original_problem_solved': body[:300].strip() if body else '',
                    'why_it_failed': 'discontinued',
                    'is_problem_still_unsolved': True,
                    '2026_viability': 'MEDIUM',
                    'review_signal': signal,
                    'signal_type': 'nostalgia',
                    'source': 'reddit_r_nostalgia',
                    'source_url': f'https://reddit.com{p.get("permalink","")}',
                    'reddit_score': score,
                    'date_found': datetime.now().isoformat(),
                    'whiteboard_tags': ['product_archaeology', 'nostalgia', 'reddit']
                })
                matched += 1
        print(f'  r/nostalgia ({sort}): {len(posts)} posts, {matched} matched')
    except Exception as e:
        print(f'  r/nostalgia ({sort}): ERROR - {str(e)[:60]}')
    time.sleep(2)

# Also scan top comments for signal phrases
print('\n=== Scanning top post comments ===')
comment_hits = 0
try:
    url = 'https://www.reddit.com/r/nostalgia/top.json?limit=25&t=month'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 ProductArchaeologyBot/1.0 (research)'
    })
    r = urllib.request.urlopen(req, timeout=15)
    posts = json.loads(r.read()).get('data', {}).get('children', [])
    for post in posts:
        p = post.get('data', {})
        permalink = p.get('permalink', '')
        if not permalink:
            continue
        try:
            req2 = urllib.request.Request(
                f'https://www.reddit.com{permalink}.json?limit=10',
                headers={'User-Agent': 'Mozilla/5.0 ProductArchaeologyBot/1.0 (research)'}
            )
            r2 = urllib.request.urlopen(req2, timeout=10)
            comment_data = json.loads(r2.read())
            if len(comment_data) > 1:
                for c in comment_data[1].get('data', {}).get('children', [])[:8]:
                    cd = c.get('data', {})
                    body = cd.get('body', '')
                    signal = check_signals(body)
                    if signal and (cd.get('score', 0) or 0) > 10:
                        findings.append({
                            'product_name': f'{p.get("title","")[:60]}',
                            'category': 'nostalgia_comment',
                            'original_problem_solved': body[:300],
                            'why_it_failed': 'discontinued',
                            'is_problem_still_unsolved': True,
                            '2026_viability': 'MEDIUM',
                            'review_signal': signal,
                            'signal_type': 'nostalgia_comment',
                            'source': 'reddit_r_nostalgia_comments',
                            'source_url': f'https://reddit.com{permalink}',
                            'reddit_score': cd.get('score', 0),
                            'date_found': datetime.now().isoformat(),
                            'whiteboard_tags': ['product_archaeology', 'nostalgia', 'comment_signal']
                        })
                        comment_hits += 1
        except:
            pass
        time.sleep(1)
except Exception as e:
    print(f'  Comment scan ERROR: {str(e)[:60]}')

print(f'  Comment signal hits: {comment_hits}')

# Deduplicate by title
seen = set()
unique = []
for f in findings:
    key = f['product_name'].lower()[:50]
    if key not in seen:
        seen.add(key)
        unique.append(f)

print(f'\nTotal nostalgia findings: {len(unique)} (deduplicated from {len(findings)})')

# Save pass output
json.dump({
    'generated': datetime.now().isoformat(),
    'signal_phrases': NOSTALGIA_SIGNALS,
    'total': len(unique),
    'findings': unique
}, open(os.path.join(BASE, 'pass1-nostalgia.json'), 'w'), indent=2)

# Merge into master results
master_path = 'G:/My Drive/Projects/_studio/product-archaeology-results.json'
if os.path.exists(master_path):
    master = json.load(open(master_path))
    existing_names = {r.get('product_name','').lower()[:40] for r in master.get('results', [])}
    added = 0
    for f in unique:
        key = f.get('product_name','').lower()[:40]
        if key not in existing_names:
            master.setdefault('results', []).append(f)
            existing_names.add(key)
            added += 1
    master['count'] = len(master['results'])
    master['updated'] = datetime.now().isoformat()
    json.dump(master, open(master_path, 'w'), indent=2)
    print(f'Merged {added} new into master (total: {master["count"]})')

# Push high-score items to whiteboard
wb = json.load(open(WHITEBOARD)) if os.path.exists(WHITEBOARD) else {'items': []}
existing_wb = {i.get('title','').lower() for i in wb.get('items', [])}
pushed = 0
for item in unique:
    name = item.get('product_name', '')
    if item.get('reddit_score', 0) > 200 and name.lower() not in existing_wb:
        wb.setdefault('items', []).append({
            'id': f'nost-{len(wb["items"])+1:04d}',
            'type': 'product_archaeology',
            'title': name,
            'description': item.get('original_problem_solved', '')[:200],
            'signal': item.get('review_signal', ''),
            'source': 'reddit_r_nostalgia',
            'source_url': item.get('source_url', ''),
            'reddit_score': item.get('reddit_score', 0),
            'tags': item.get('whiteboard_tags', []),
            'added': datetime.now().isoformat(),
            'status': 'new'
        })
        existing_wb.add(name.lower())
        pushed += 1

json.dump(wb, open(WHITEBOARD, 'w'), indent=2)
print(f'Pushed {pushed} high-score items to whiteboard.json')
print('Done.')
