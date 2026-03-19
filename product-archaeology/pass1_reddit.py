import urllib.request, urllib.parse, json, time, os
from datetime import datetime

BASE = 'G:/My Drive/Projects/_studio/product-archaeology'
os.makedirs(BASE, exist_ok=True)
WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'

SIGNAL_PHRASES = [
    'great concept but', 'love the idea but', 'if only they had',
    'promising but abandoned', 'used to be great before', 'company went under',
    'wish someone would make', 'nobody has built this yet',
    'discontinued but amazing', 'ahead of its time', 'patent but never built',
    'still waiting for someone', 'nothing else does what', 'miss this so much',
    'should have been massive', 'acquired and killed', 'someone needs to bring',
    'would pay good money for', 'market gap since', 'spiritual successor',
]

findings = []

def has_signal(text):
    t = text.lower()
    for phrase in SIGNAL_PHRASES:
        if phrase in t:
            return phrase
    return None

def fetch_subreddit(sub, sorts=('top', 'hot'), limit=100):
    results = []
    for sort in sorts:
        url = f'https://www.reddit.com/r/{sub}/{sort}.json?limit={limit}&t=all'
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 ProductArchaeologyBot/1.0 (contact: research)'
            })
            r = urllib.request.urlopen(req, timeout=15)
            data = json.loads(r.read())
            posts = data.get('data', {}).get('children', [])
            print(f'  r/{sub} ({sort}): {len(posts)} posts fetched')
            results.extend(posts)
        except Exception as e:
            print(f'  r/{sub} ({sort}): ERROR - {str(e)[:60]}')
        time.sleep(3)
    return results

# Target subreddits
TARGET_SUBS = [
    'shutdownsaddened',
    'discontinued',
    'DeadApps',
    'nostalgia',
    'patientgamers',
]

print('=== Reddit Product Archaeology ===')
for sub in TARGET_SUBS:
    posts = fetch_subreddit(sub)
    matched = 0
    for post in posts:
        p = post.get('data', {})
        title = p.get('title', '')
        body = p.get('selftext', '')
        combined = f'{title} {body}'
        signal = has_signal(combined)
        score = p.get('score', 0)

        # For shutdown/discontinued subs, capture all posts; others require signal match
        if sub in ('shutdownsaddened', 'discontinued', 'DeadApps') or signal:
            findings.append({
                'product_name': title[:80],
                'category': 'discontinued_product',
                'original_problem_solved': body[:300].strip() if body else '',
                'why_it_failed': 'discontinued',
                'is_problem_still_unsolved': True,
                '2026_viability': 'MEDIUM',
                'review_signal': signal or title[:60],
                'signal_type': 'abandonment',
                'source': f'reddit_r_{sub}',
                'source_url': f'https://reddit.com{p.get("permalink","")}',
                'reddit_score': score,
                'date_found': datetime.now().isoformat(),
                'whiteboard_tags': ['product_archaeology', 'reddit', sub]
            })
            matched += 1

    print(f'  r/{sub}: {matched} archaeology items captured')

# Also scan top comments in shutdownsaddened for context
print('\n=== Scanning comment bodies for signal phrases ===')
for sub in ('shutdownsaddened', 'discontinued'):
    url = f'https://www.reddit.com/r/{sub}/top.json?limit=25&t=month'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 ProductArchaeologyBot/1.0'
        })
        r = urllib.request.urlopen(req, timeout=15)
        posts = json.loads(r.read()).get('data', {}).get('children', [])
        for post in posts:
            p = post.get('data', {})
            post_id = p.get('id', '')
            permalink = p.get('permalink', '')
            if not post_id:
                continue
            # Fetch comments
            comments_url = f'https://www.reddit.com{permalink}.json?limit=10'
            try:
                req2 = urllib.request.Request(comments_url, headers={
                    'User-Agent': 'Mozilla/5.0 ProductArchaeologyBot/1.0'
                })
                r2 = urllib.request.urlopen(req2, timeout=10)
                comment_data = json.loads(r2.read())
                if len(comment_data) > 1:
                    comments = comment_data[1].get('data', {}).get('children', [])
                    for c in comments[:5]:
                        cd = c.get('data', {})
                        body = cd.get('body', '')
                        signal = has_signal(body)
                        if signal and cd.get('score', 0) > 5:
                            findings.append({
                                'product_name': f'[Comment signal] {p.get("title","")[:60]}',
                                'category': 'comment_signal',
                                'original_problem_solved': body[:300],
                                'why_it_failed': 'discontinued',
                                'is_problem_still_unsolved': True,
                                '2026_viability': 'MEDIUM',
                                'review_signal': signal,
                                'signal_type': 'resurrection',
                                'source': f'reddit_r_{sub}_comments',
                                'source_url': f'https://reddit.com{permalink}',
                                'date_found': datetime.now().isoformat(),
                                'whiteboard_tags': ['product_archaeology', 'reddit', 'comment_signal']
                            })
            except:
                pass
            time.sleep(1)
    except Exception as e:
        print(f'  Comment scan r/{sub}: {str(e)[:50]}')
    time.sleep(2)

print(f'\nTotal Reddit findings: {len(findings)}')

# Save pass output
json.dump({
    'generated': datetime.now().isoformat(),
    'total': len(findings),
    'findings': findings
}, open(os.path.join(BASE, 'pass1-reddit.json'), 'w'), indent=2)

# Merge with existing results
master_path = 'G:/My Drive/Projects/_studio/product-archaeology-results.json'
if os.path.exists(master_path):
    master = json.load(open(master_path))
    existing_names = {r.get('product_name','').lower()[:40] for r in master.get('results', [])}
    added = 0
    for f in findings:
        key = f.get('product_name','').lower()[:40]
        if key not in existing_names:
            master.setdefault('results', []).append(f)
            existing_names.add(key)
            added += 1
    master['count'] = len(master['results'])
    master['updated'] = datetime.now().isoformat()
    json.dump(master, open(master_path, 'w'), indent=2)
    print(f'Merged {added} new items into product-archaeology-results.json (total: {master["count"]})')

# Push HIGH-signal items to whiteboard
wb = {'updated': datetime.now().isoformat(), 'items': []}
if os.path.exists(WHITEBOARD):
    wb = json.load(open(WHITEBOARD))

existing_wb = {i.get('title','').lower() for i in wb.get('items', [])}
pushed = 0
# Push items with strong signals or high reddit score
for item in findings:
    name = item.get('product_name', '')
    score = item.get('reddit_score', 0)
    signal = item.get('review_signal', '')
    high_signal = any(p in signal.lower() for p in [
        'wish someone', 'nobody has built', 'needs to bring back',
        'market gap', 'still waiting', 'would pay'
    ])
    if (score > 100 or high_signal) and name.lower() not in existing_wb:
        wb.setdefault('items', []).append({
            'id': f'arch-reddit-{len(wb["items"])+1:04d}',
            'type': 'product_archaeology',
            'title': name,
            'description': item.get('original_problem_solved', '')[:200],
            'viability': '2026_viability',
            'signal': signal,
            'source': item.get('source', ''),
            'source_url': item.get('source_url', ''),
            'reddit_score': score,
            'tags': item.get('whiteboard_tags', []),
            'added': datetime.now().isoformat(),
            'status': 'new'
        })
        existing_wb.add(name.lower())
        pushed += 1

json.dump(wb, open(WHITEBOARD, 'w'), indent=2)
print(f'Pushed {pushed} high-signal items to whiteboard.json')
print('\nDone.')
