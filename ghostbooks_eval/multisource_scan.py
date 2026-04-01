import json, os, requests, time, hashlib
from datetime import datetime

BASE_DIR = os.getcwd()
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_raw_multisource.jsonl')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'multisource_scan.log')

with open(os.path.join(BASE_DIR, 'config', 'theory_domains.json')) as f:
    THEORY_DOMAINS = json.load(f)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_msg(msg):
    ts = datetime.now().isoformat()
    entry = f'[{ts}] {msg}'
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def get_theory_keywords():
    keywords = set()
    for domain, config in THEORY_DOMAINS.items():
        keywords.update(config.get('keywords', []))
    return list(keywords)[:15]

def scan_gutendex(keywords):
    log_msg('Scanning Project Gutenberg via Gutendex...')
    books = []
    for keyword in keywords[:8]:
        try:
            url = f'https://gutendex.com/books?search={keyword}'
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for book in data.get('results', [])[:2]:
                    books.append({'identifier': f"pg_{book.get('id')}", 'title': book.get('title', 'Unknown'), 'author': ', '.join([a.get('name', 'Unknown') for a in book.get('authors', [])]) if book.get('authors') else 'Unknown', 'year': 'Unknown', 'description': f"Project Gutenberg #{book.get('id')}", 'source': 'project_gutenberg', 'url': book.get('formats', {}).get('text/html', '')})
                time.sleep(0.3)
        except Exception as e:
            log_msg(f'  Error on "{keyword}": {e}')
    log_msg(f'Gutendex: {len(books)} books')
    return books

def scan_google_books(keywords):
    log_msg('Scanning Google Books...')
    books = []
    for keyword in keywords[:8]:
        try:
            url = f'https://www.googleapis.com/books/v1/volumes?q={keyword}+theory&filter=full&maxResults=10'
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('items', [])[:2]:
                    vol_info = item.get('volumeInfo', {})
                    books.append({'identifier': f"gb_{item.get('id')}", 'title': vol_info.get('title', 'Unknown'), 'author': ', '.join(vol_info.get('authors', ['Unknown'])), 'year': vol_info.get('publishedDate', '')[:4], 'description': vol_info.get('description', '')[:200], 'source': 'google_books', 'url': vol_info.get('previewLink', '')})
                time.sleep(0.3)
        except Exception as e:
            log_msg(f'  Error on "{keyword}": {e}')
    log_msg(f'Google Books: {len(books)} books')
    return books

def scan_hathitrust(keywords):
    log_msg('Scanning HathiTrust...')
    books = []
    for keyword in keywords[:8]:
        try:
            url = f'https://catalog.hathitrust.org/api/volumes/search/json?q={keyword}+theory&ft=ft'
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get('items', [])[:2]:
                    books.append({'identifier': f"ht_{item.get('id')}", 'title': item.get('title', 'Unknown'), 'author': item.get('author', 'Unknown'), 'year': str(item.get('publishDate', ''))[:4], 'description': item.get('description', '')[:200], 'source': 'hathitrust', 'url': f"https://www.hathitrust.org/record/{item.get('id')}"})
                time.sleep(0.3)
        except Exception as e:
            log_msg(f'  Error on "{keyword}": {e}')
    log_msg(f'HathiTrust: {len(books)} books')
    return books

def deduplicate_books(all_books):
    seen = {}
    unique = []
    for book in all_books:
        title = book.get('title', '').lower().strip()
        author = book.get('author', '').lower().strip()
        key = hashlib.md5(f'{title}|{author}'.encode()).hexdigest()
        if key not in seen:
            seen[key] = True
            unique.append(book)
    return unique

def assign_theory_domains(books):
    for book in books:
        title = book.get('title', '').lower()
        desc = book.get('description', '').lower()
        combined = f'{title} {desc}'
        best_domain = 'information_computation'
        for domain, config in THEORY_DOMAINS.items():
            keywords = config.get('keywords', [])
            matches = sum(1 for kw in keywords if kw.lower() in combined)
            if matches > 0:
                best_domain = domain
                break
        book['theory_domain'] = best_domain
    return books

log_msg('=== MULTI-SOURCE BOOK SCANNER ===')
keywords = get_theory_keywords()
log_msg(f'Keywords: {len(keywords)}')

all_books = []
all_books.extend(scan_gutendex(keywords))
all_books.extend(scan_google_books(keywords))
all_books.extend(scan_hathitrust(keywords))

log_msg(f'Total before dedup: {len(all_books)}')
unique_books = deduplicate_books(all_books)
log_msg(f'After dedup: {len(unique_books)}')
unique_books = assign_theory_domains(unique_books)

log_msg(f'Writing to {OUTPUT_FILE}...')
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for book in unique_books:
        f.write(json.dumps(book) + '\n')

log_msg(f'Complete: {len(unique_books)} books')
