"""
scraper_utils.py -- Shared scraping utilities for job-match company registry
"""
import urllib.request, urllib.parse, time, random, json, os
from urllib.error import HTTPError, URLError
from datetime import datetime

AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 Safari/604.1',
]

SUPERVISOR_INBOX = 'G:/My Drive/Projects/_studio/supervisor-inbox.json'

CAREER_PATHS = [
    '/careers',
    '/jobs',
    '/hiring',
    '/work-with-us',
    '/join-us',
    '/join-our-team',
    '/career-opportunities',
    '/open-positions',
    '/careers/open-positions',
]

CAREER_KEYWORDS = ['job', 'career', 'position', 'opening', 'hiring', 'apply', 'vacancy', 'role']


def random_delay(min_s=2.0, max_s=8.0):
    time.sleep(random.uniform(min_s, max_s))


def fetch(url, retries=3, timeout=12):
    """
    Fetch a URL with rotating user agents, retry + exponential backoff,
    and error classification.

    Returns dict:
      url, status, content, js_likely, blocked, error, redirect (optional)
    """
    for attempt in range(retries):
        agent = random.choice(AGENTS)
        random_delay()
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
            })
            r = urllib.request.urlopen(req, timeout=timeout)
            content = r.read(16384).decode('utf-8', errors='ignore')
            return {
                'url': url, 'status': r.status, 'content': content,
                'js_likely': _is_js_rendered(content),
                'blocked': False, 'error': None,
            }

        except HTTPError as e:
            if e.code == 403:
                return {'url': url, 'status': 403, 'content': '',
                        'js_likely': False, 'blocked': True, 'error': '403 Forbidden'}
            if e.code == 429:
                backoff = (2 ** attempt) * 10  # 10s, 20s, 40s
                time.sleep(backoff)
                continue
            if e.code in (301, 302):
                location = e.headers.get('Location', '')
                return {'url': url, 'status': e.code, 'content': '',
                        'js_likely': False, 'blocked': False, 'error': None,
                        'redirect': location}
            return {'url': url, 'status': e.code, 'content': '',
                    'js_likely': False, 'blocked': False, 'error': f'HTTP {e.code}'}

        except URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {'url': url, 'status': 0, 'content': '',
                    'js_likely': False, 'blocked': False, 'error': str(e)}

        except Exception as e:
            return {'url': url, 'status': 0, 'content': '',
                    'js_likely': False, 'blocked': False, 'error': str(e)}

    return {'url': url, 'status': 0, 'content': '',
            'js_likely': False, 'blocked': False, 'error': 'Max retries exceeded'}


def _is_js_rendered(content):
    if len(content) < 2000:
        return True
    js_signals = [
        '<noscript>', 'id="root"', 'id="app"', '__NEXT_DATA__',
        '__INITIAL_STATE__', 'window.__REDUX', 'react-root',
        'ng-version=', 'data-reactroot', 'window.__APP_STATE',
    ]
    return sum(1 for s in js_signals if s in content) >= 2


def has_career_content(content):
    """Confirm the page is actually a jobs/careers page, not a generic 200."""
    return any(kw in content.lower() for kw in CAREER_KEYWORDS)


def assign_tier(result):
    """Classify a fetch result into Tier 1 / 2 / 3."""
    if result.get('blocked') or result.get('status') == 403:
        return 3
    if result.get('status') == 429:
        return 3
    if result.get('js_likely'):
        return 2
    if result.get('status') == 200:
        return 1
    if result.get('status') in (301, 302):
        return 1  # follow redirect and recheck
    return 3


def guess_domain(name):
    """Guess a .com domain from a company name."""
    import re
    suffixes = r'\b(inc|llc|corp|ltd|co|company|group|holdings|technologies|' \
               r'solutions|services|international|global|enterprises|partners)\b'
    clean = re.sub(suffixes, '', name.lower())
    clean = re.sub(r'[^a-z0-9]', '', clean.strip())
    return clean + '.com' if clean else ''


def find_career_url(domain):
    """
    Try each CAREER_PATHS on the domain.
    Returns first validated result dict, or None if nothing found.
    """
    for path in CAREER_PATHS:
        url = f'https://{domain}{path}'
        result = fetch(url, retries=2)
        if result['status'] == 200 and has_career_content(result['content']):
            result['career_path'] = path
            return result
        if result['status'] in (301, 302) and result.get('redirect'):
            # Follow one redirect
            redir = result['redirect']
            if not redir.startswith('http'):
                redir = f'https://{domain}{redir}'
            r2 = fetch(redir, retries=1)
            if r2['status'] == 200 and has_career_content(r2['content']):
                r2['career_path'] = path
                r2['url'] = redir
                return r2
        if result.get('blocked') or result.get('status') == 429:
            break  # stop trying paths if we're blocked
    return None


def report_to_supervisor(url, issue, context=''):
    """Append a scraper failure to supervisor-inbox.json."""
    inbox = []
    if os.path.exists(SUPERVISOR_INBOX):
        try:
            inbox = json.load(open(SUPERVISOR_INBOX))
            if isinstance(inbox, dict):
                inbox = inbox.get('items', [])
        except Exception:
            inbox = []
    inbox.append({
        'id': f'scraper-fail-{int(time.time())}',
        'type': 'scraper_failure',
        'url': url,
        'issue': issue,
        'context': context,
        'reported_at': datetime.now().isoformat(),
        'status': 'pending',
        'priority': 'medium',
    })
    json.dump(inbox, open(SUPERVISOR_INBOX, 'w'), indent=2)
