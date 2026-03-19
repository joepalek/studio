# GHOST BOOK DIVISION — BOOK REVISION & CONCATENATION PIPELINE

## Role
You are the Ghost Book Division. You find books whose premises failed
due to missing data, validate them against current knowledge, propose
specific fact-checked revisions, and either publish updated versions
(non-copyright) or pitch revised editions to authors/publishers.

You also identify opportunities to concatenate multiple related books
into stronger unified works, and build AI Author characters from
validated book corpora.

## Revenue Paths

### Path A — Non-Copyright Books
Books published before 1928 (US) are public domain.
Revise, update, publish directly. No permission needed.
Revenue: Direct sales, print-on-demand, ebook.

### Path B — Copyright Books (pitch service)
Books whose data gaps are now fillable.
Deliver: Sample chapter with AI-assisted updates + data sources.
Pitch to: Original author (co-author credit), Publisher (licensed update).
Revenue: Advance + royalty, or flat licensing fee.

### Path C — Book Concatenation
Multiple books covering same topic from different angles.
Merge the best of each into a superior unified work.
Better than any single source book.
Revenue: New book sales, or pitch as definitive edition.

### Path D — AI Author Licensing
Build AI expert character from validated book corpus.
License as: Chatbot for publishers, educational tool, expert system.
Revenue: SaaS licensing per conversation or per user.

## Execution

### Pass 1 — Find Ghost Book Candidates (Three Sources)

Three-source discovery pipeline. Run via script file (not -c) to avoid
backslash issues on Windows:

```bash
python G:/My\ Drive/Projects/ghost-book/pass1_find_candidates.py
```

Script content (`ghost-book/pass1_find_candidates.py`):

```python
import urllib.request, urllib.parse, json, time, os
from datetime import datetime

BASE = 'G:/My Drive/Projects/ghost-book'
os.makedirs(BASE, exist_ok=True)
os.makedirs(BASE + '/source-logs', exist_ok=True)

# Topics where books failed due to data gaps now fillable
# Format: (topic, year_from, year_to, gutenberg_query, openlibrary_subject)
search_topics = [
    # Materials science
    ('hemp composite materials industrial', '1980', '2005', 'hemp fiber', 'hemp'),
    ('graphene applications manufacturing', '1990', '2010', 'graphene', 'graphene'),
    # Computing/AI
    ('neural network practical applications', '1985', '2000', 'neural network', 'neural networks'),
    ('machine learning business applications', '1995', '2008', 'machine learning', 'machine learning'),
    # Alternative energy
    ('hydrogen fuel cell vehicles', '1990', '2005', 'hydrogen fuel cell', 'fuel cells'),
    ('solar panel efficiency residential', '1985', '2005', 'solar energy', 'solar energy'),
    # Ancient technology
    ('vedic mathematics computing algorithms', '1960', '2000', 'vedic mathematics', 'vedic mathematics'),
    ('ancient metallurgy impossible artifacts', '1970', '2010', 'ancient metallurgy', 'metallurgy'),
    # Medicine
    ('microbiome gut health disease', '1990', '2008', 'microbiome gut', 'microbiome'),
    ('psychedelic therapy clinical', '1960', '1975', 'psychedelic therapy', 'psychedelics'),
    # Economics
    ('universal basic income feasibility', '1960', '2000', 'basic income', 'basic income'),
    ('circular economy waste elimination', '1980', '2005', 'circular economy', 'circular economy'),
]

all_candidates = []
seen_ids = set()

def add_candidate(topic, title, author, date, identifier, source, archive_url, copyright_status):
    key = identifier or f'{title}|{author}'
    if key in seen_ids:
        return False
    seen_ids.add(key)
    all_candidates.append({
        'topic': topic,
        'title': title,
        'author': author,
        'date': date,
        'identifier': identifier,
        'archive_url': archive_url,
        'source': source,
        'copyright_status': copyright_status,
        'status': 'candidate'
    })
    return True

# ── SOURCE 1: Internet Archive Advanced Search ────────────────────────────────
print('\n=== SOURCE 1: Internet Archive Advanced Search ===')
for topic, year_from, year_to, gut_q, ol_subject in search_topics:
    query = f'{topic} mediatype:texts date:[{year_from} TO {year_to}]'
    params = urllib.parse.urlencode({
        'q': query,
        'fl': 'identifier,title,date,creator,subject',
        'output': 'json',
        'rows': '15'
    })
    url = f'https://archive.org/advancedsearch.php?{params}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
        r = urllib.request.urlopen(req, timeout=15)
        docs = json.loads(r.read()).get('response', {}).get('docs', [])
        added = 0
        for doc in docs:
            yr = str(doc.get('date', ''))[:4]
            cs = 'public_domain' if yr and int(yr) < 1928 else 'copyright'
            if add_candidate(topic, doc.get('title',''), doc.get('creator',''),
                             doc.get('date',''), doc.get('identifier',''),
                             'ia_search',
                             f'https://archive.org/details/{doc.get("identifier","")}', cs):
                added += 1
        print(f'  {topic[:38]}: {added} new')
    except Exception as e:
        print(f'  {topic[:38]}: ERROR - {str(e)[:50]}')
    time.sleep(0.5)

# ── SOURCE 2: Internet Archive Books Collection (subject search) ──────────────
print('\n=== SOURCE 2: Internet Archive Subject Search ===')
for topic, year_from, year_to, gut_q, ol_subject in search_topics:
    # Two passes: pre-1928 public domain, then 1928-2005 pitch targets
    for era, y1, y2 in [('public_domain', '1800', '1927'), ('copyright', '1928', year_to)]:
        query = f'subject:"{topic}" mediatype:texts date:[{y1} TO {y2}]'
        params = urllib.parse.urlencode({
            'q': query,
            'fl': 'identifier,title,date,creator',
            'output': 'json',
            'rows': '10'
        })
        url = f'https://archive.org/advancedsearch.php?{params}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
            r = urllib.request.urlopen(req, timeout=15)
            docs = json.loads(r.read()).get('response', {}).get('docs', [])
            added = 0
            for doc in docs:
                if add_candidate(topic, doc.get('title',''), doc.get('creator',''),
                                 doc.get('date',''), doc.get('identifier',''),
                                 'ia_subject',
                                 f'https://archive.org/details/{doc.get("identifier","")}', era):
                    added += 1
            if added:
                print(f'  {topic[:35]} [{era[:3]}]: {added} new')
        except Exception as e:
            print(f'  {topic[:35]}: ERROR - {str(e)[:40]}')
        time.sleep(0.5)

# ── SOURCE 3A: Open Library API ───────────────────────────────────────────────
print('\n=== SOURCE 3A: Open Library API ===')
for topic, year_from, year_to, gut_q, ol_subject in search_topics:
    params = urllib.parse.urlencode({
        'q': ol_subject,
        'fields': 'title,author_name,first_publish_year,subject,key',
        'limit': '10'
    })
    url = f'https://openlibrary.org/search.json?{params}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
        r = urllib.request.urlopen(req, timeout=15)
        docs = json.loads(r.read()).get('docs', [])
        added = 0
        for doc in docs:
            yr = doc.get('first_publish_year', 9999)
            cs = 'public_domain' if yr < 1928 else 'copyright'
            key = doc.get('key', '').replace('/works/', '')
            archive_url = f'https://openlibrary.org{doc.get("key","")}'
            authors = doc.get('author_name', [])
            author = authors[0] if authors else ''
            if add_candidate(topic, doc.get('title',''), author,
                             str(yr), key, 'openlibrary', archive_url, cs):
                added += 1
        print(f'  {topic[:38]}: {added} new')
    except Exception as e:
        print(f'  {topic[:38]}: ERROR - {str(e)[:50]}')
    time.sleep(0.5)

# ── SOURCE 3B: Project Gutenberg API ─────────────────────────────────────────
print('\n=== SOURCE 3B: Project Gutenberg API ===')
for topic, year_from, year_to, gut_q, ol_subject in search_topics:
    params = urllib.parse.urlencode({'search': gut_q, 'format': 'json'})
    url = f'https://gutendex.com/books/?{params}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
        r = urllib.request.urlopen(req, timeout=15)
        results = json.loads(r.read()).get('results', [])
        added = 0
        for book in results[:10]:
            authors = [a.get('name','') for a in book.get('authors', [])]
            author = authors[0] if authors else ''
            birth = book.get('authors', [{}])[0].get('birth_year', 0) or 0
            death = book.get('authors', [{}])[0].get('death_year', 0) or 0
            # Gutenberg books are public domain by definition
            identifier = str(book.get('id',''))
            archive_url = f'https://www.gutenberg.org/ebooks/{identifier}'
            if add_candidate(topic, book.get('title',''), author,
                             str(death) if death else '', identifier,
                             'gutenberg', archive_url, 'public_domain'):
                added += 1
        print(f'  {topic[:38]}: {added} new')
    except Exception as e:
        print(f'  {topic[:38]}: ERROR - {str(e)[:50]}')
    time.sleep(0.5)

# ── SOURCE 3C: Wayback CDX scan for book URLs ────────────────────────────────
print('\n=== SOURCE 3C: Wayback CDX Book URL Patterns ===')
cdx_patterns = []
for topic, year_from, year_to, gut_q, ol_subject in search_topics:
    slug = ol_subject.replace(' ', '-').lower()
    cdx_patterns.extend([
        (topic, f'gutenberg.org/ebooks/*{slug}*'),
        (topic, f'archive.org/details/*{slug}*'),
        (topic, f'openlibrary.org/works/*{slug}*'),
    ])

for topic, pattern in cdx_patterns:
    encoded = urllib.parse.quote(pattern, safe='')
    url = (f'http://web.archive.org/cdx/search/cdx'
           f'?url={encoded}&output=json&fl=original&limit=5'
           f'&from=19900101&collapse=urlkey&matchType=prefix')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
        r = urllib.request.urlopen(req, timeout=15)
        rows = json.loads(r.read())
        urls = [row[0] for row in rows[1:]] if len(rows) > 1 else []
        added = 0
        for u in urls:
            identifier = u.split('/')[-1].split('?')[0]
            cs = 'public_domain' if 'gutenberg' in u else 'unknown'
            if add_candidate(topic, identifier, '', '', identifier,
                             'wayback_cdx', u, cs):
                added += 1
        if added:
            print(f'  {pattern[:45]}: {added} URLs')
    except Exception as e:
        pass  # CDX misses are expected, skip noise
    time.sleep(0.3)

# ── SAVE OUTPUT ───────────────────────────────────────────────────────────────
# Group by topic for summary
by_topic = {}
for c in all_candidates:
    t = c['topic']
    by_topic.setdefault(t, []).append(c)

print(f'\n=== RESULTS ===')
for topic, books in sorted(by_topic.items(), key=lambda x: -len(x[1])):
    pd = sum(1 for b in books if b['copyright_status'] == 'public_domain')
    print(f'  {topic[:40]}: {len(books)} total ({pd} public domain)')

output = {
    'generated': datetime.now().isoformat(),
    'total': len(all_candidates),
    'by_source': {
        'ia_search': sum(1 for c in all_candidates if c['source'] == 'ia_search'),
        'ia_subject': sum(1 for c in all_candidates if c['source'] == 'ia_subject'),
        'openlibrary': sum(1 for c in all_candidates if c['source'] == 'openlibrary'),
        'gutenberg': sum(1 for c in all_candidates if c['source'] == 'gutenberg'),
        'wayback_cdx': sum(1 for c in all_candidates if c['source'] == 'wayback_cdx'),
    },
    'public_domain_count': sum(1 for c in all_candidates if c['copyright_status'] == 'public_domain'),
    'candidates': all_candidates
}

json.dump(output, open(BASE + '/candidates-expanded.json', 'w'), indent=2)
print(f'\nTotal unique candidates: {len(all_candidates)}')
print(f'Public domain: {output["public_domain_count"]}')
print(f'Saved to ghost-book/candidates-expanded.json')
```

### Pass 1.5 — Review Signal Mining
Scrape book review sources for negative signals that flag updatable/weak-premise books.
Run via script file:

```bash
python G:/My\ Drive/Projects/ghost-book/pass1b_review_signals.py
```

Script content (`ghost-book/pass1b_review_signals.py`):

```python
import urllib.request, urllib.parse, json, time, os
from datetime import datetime

BASE = 'G:/My Drive/Projects/ghost-book'
os.makedirs(BASE, exist_ok=True)

# Weak-premise signal strings — scan review text for these
WEAK_PREMISE_SIGNALS = [
    'premise is flawed but',
    'outdated when published',
    'data has since shown',
    'theory has been disproven',
    'needs to be updated',
    'lacks supporting evidence',
    'fascinating premise let down by',
    'published too early',
    'evidence was not available',
    'would benefit from revision',
]

# Concatenation opportunity signals
CONCAT_SIGNALS = [
    'should be read alongside',
    'complements perfectly with',
    'covers what',
    'better together with',
    'the missing piece',
    'pairs well with',
    'read in conjunction',
]

TOPICS = [
    'hemp composite industrial',
    'graphene manufacturing',
    'neural network applications',
    'machine learning business',
    'hydrogen fuel cell',
    'solar panel residential',
    'vedic mathematics',
    'ancient metallurgy',
    'microbiome gut health',
    'psychedelic therapy',
    'universal basic income',
    'circular economy',
    # Lore clusters
    'atlantis ancient civilization',
    'sumerian anunnaki',
    'egyptian pyramid construction',
    'gobekli tepe prehistoric',
    'younger dryas impact',
    'piri reis map cartography',
    'nan madol megalithic',
    'yonaguni underwater monument',
]

signals_found = []

# SOURCE A: Open Library subject search — extract edition metadata
# (review text not available via API, but edition count signals popularity + controversy)
print('=== REVIEW SOURCE: Open Library edition signals ===')
for topic in TOPICS:
    params = urllib.parse.urlencode({'q': topic, 'fields': 'title,author_name,first_publish_year,edition_count,ratings_average,ratings_count,key', 'limit': '5'})
    url = f'https://openlibrary.org/search.json?{params}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
        r = urllib.request.urlopen(req, timeout=15)
        docs = json.loads(r.read()).get('docs', [])
        for doc in docs:
            rating = doc.get('ratings_average', 0) or 0
            count = doc.get('ratings_count', 0) or 0
            editions = doc.get('edition_count', 0) or 0
            yr = doc.get('first_publish_year', 9999)
            # Flag: low rating + many ratings = controversial / weak premise
            if count > 50 and rating < 3.5:
                signals_found.append({
                    'topic': topic,
                    'title': doc.get('title',''),
                    'author': (doc.get('author_name') or [''])[0],
                    'year': yr,
                    'signal_type': 'low_rating_high_volume',
                    'rating': rating,
                    'rating_count': count,
                    'edition_count': editions,
                    'source': 'openlibrary',
                    'url': f'https://openlibrary.org{doc.get("key","")}',
                    'revenue_signal': 'pitch_update' if yr >= 1928 else 'direct_publish'
                })
                print(f'  SIGNAL: {doc.get("title","")[:50]} ({yr}) — {rating:.1f}/5 ({count} ratings)')
    except Exception as e:
        print(f'  {topic[:35]}: ERROR - {str(e)[:40]}')
    time.sleep(0.5)

# SOURCE B: Wayback CDX — scan for academic review journal URLs
print('\n=== REVIEW SOURCE: Wayback CDX academic reviews ===')
review_domains = [
    ('jstor.org/stable/*', 'jstor'),
    ('scholar.google.com/scholar*', 'google_scholar'),
    ('academia.edu/*review*', 'academia'),
    ('researchgate.net/publication/*review*', 'researchgate'),
]
for topic in TOPICS[:6]:  # CDX is slow, limit to top topics
    slug = topic.replace(' ', '-').lower()[:20]
    for domain_pattern, source_name in review_domains:
        encoded = urllib.parse.quote(domain_pattern, safe='')
        url = (f'http://web.archive.org/cdx/search/cdx'
               f'?url={encoded}&output=json&fl=original&limit=3'
               f'&from=19950101&collapse=urlkey&matchType=prefix')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GhostBookScout/1.0'})
            r = urllib.request.urlopen(req, timeout=10)
            rows = json.loads(r.read())
            if len(rows) > 1:
                pass  # CDX returns generic domain hits, not topic-specific
        except:
            pass
        time.sleep(0.2)

# SOURCE C: LibraryThing — search via Open Web (no API key needed for basic search)
print('\n=== REVIEW SOURCE: LibraryThing subject search ===')
for topic in TOPICS[:8]:
    params = urllib.parse.urlencode({'search': topic, 'searchtype': 'tag'})
    url = f'https://www.librarything.com/search.php?{params}'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; GhostBookScout/1.0)',
            'Accept': 'text/html'
        })
        r = urllib.request.urlopen(req, timeout=10)
        html = r.read().decode('utf-8', errors='ignore')
        # Count book results as a proxy for topic coverage
        book_count = html.count('class="lt-work-title"')
        if book_count > 0:
            print(f'  {topic[:35]}: {book_count} books on LibraryThing')
    except Exception as e:
        print(f'  {topic[:35]}: {str(e)[:40]}')
    time.sleep(1)

output = {
    'generated': datetime.now().isoformat(),
    'total_signals': len(signals_found),
    'weak_premise_search_strings': WEAK_PREMISE_SIGNALS,
    'concat_signals': CONCAT_SIGNALS,
    'signals': signals_found
}

json.dump(output, open(BASE + '/review-signals.json', 'w'), indent=2)
print(f'\nTotal review signals found: {len(signals_found)}')
print('Saved to ghost-book/review-signals.json')
```

### Pass 2 — Validate Premises Against Current Data
```bash
python -c "
import json, urllib.request, os

candidates = json.load(open('G:/My Drive/Projects/ghost-book/candidates.json'))
c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
key = c.get('gemini_api_key', '')

validated = []
for book in candidates['candidates'][:10]:  # Process 10 at a time
    prompt = f'''A book was published that failed commercially.
Analyze if its premise is now viable in 2026.

Book: {book[\"title\"]}
Author: {book[\"author\"]}
Year: {book[\"date\"]}
Topic area: {book[\"topic\"]}

Answer:
1. What data/technology was likely missing when this was written?
2. Does 2026 data/technology now support the premise? (YES/PARTIAL/NO)
3. What specific updates would make this book valuable today?
4. Revenue path: DIRECT_PUBLISH / PITCH_AUTHOR / PITCH_PUBLISHER / SKIP

Return JSON: {{
  \"viable\": \"YES/PARTIAL/NO\",
  \"missing_data\": \"what was missing\",
  \"updates_needed\": \"specific updates\",
  \"revenue_path\": \"path\",
  \"pitch_angle\": \"one sentence pitch\"
}}'''

    payload = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}'
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}),
            timeout=15
        )
        result = json.loads(r.read())['candidates'][0]['content']['parts'][0]['text'].strip()
        result = result.replace('```json','').replace('```','').strip()
        analysis = json.loads(result)
        book['analysis'] = analysis
        book['status'] = 'validated'
        print(f'  {book[\"title\"][:50]}: {analysis[\"viable\"]} — {analysis[\"revenue_path\"]}')
        if analysis['viable'] in ['YES', 'PARTIAL']:
            validated.append(book)
    except Exception as e:
        print(f'  ERROR: {e}')

json.dump({'validated': validated, 'count': len(validated)},
          open('G:/My Drive/Projects/ghost-book/validated.json', 'w'), indent=2)
print(f'{len(validated)} viable books found')
"
```

### Pass 3 — Find Concatenation Opportunities
```bash
python -c "
import json, urllib.request

c = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
key = c.get('gemini_api_key', '')

# Find topic clusters where multiple books exist
topic_clusters = [
    ['vedic mathematics computing', 'sanskrit algorithms programming', 'ancient math modern computing'],
    ['hemp materials industrial', 'cannabis fiber composites', 'natural fiber engineering'],
    ['microbiome health disease', 'gut bacteria mental health', 'probiotic therapy clinical'],
]

concat_opportunities = []
for cluster in topic_clusters:
    prompt = f'''These books cover related topics:
{chr(10).join(cluster)}

Could they be concatenated into a single superior book?
Return JSON: {{
  \"opportunity\": true/false,
  \"proposed_title\": \"title of merged book\",
  \"value_add\": \"why merged is better than any single book\",
  \"target_audience\": \"who would buy this\",
  \"revenue_estimate\": \"rough market size\"
}}'''

    payload = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}'
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}),
            timeout=10
        )
        result = json.loads(r.read())['candidates'][0]['content']['parts'][0]['text'].strip()
        result = result.replace('```json','').replace('```','').strip()
        opp = json.loads(result)
        if opp.get('opportunity'):
            concat_opportunities.append({'cluster': cluster, 'analysis': opp})
            print(f'  OPPORTUNITY: {opp[\"proposed_title\"]}')
    except Exception as e:
        print(f'  ERROR: {e}')

json.dump(concat_opportunities,
          open('G:/My Drive/Projects/ghost-book/concat-opportunities.json', 'w'), indent=2)
print(f'{len(concat_opportunities)} concatenation opportunities found')
"
```

### Pass 4 — Build AI Author Spec from Validated Books
```bash
python -c "
import json, os

validated_path = 'G:/My Drive/Projects/ghost-book/validated.json'
if not os.path.exists(validated_path):
    print('No validated books yet — run Pass 2 first')
    exit(0)

validated = json.load(open(validated_path))
ai_authors = []

for book in validated.get('validated', [])[:3]:
    if book.get('analysis', {}).get('viable') == 'YES':
        author_spec = {
            'character_name': f'Dr. {book.get(\"author\", \"Author\").split()[-1] if book.get(\"author\") else \"Expert\"}',
            'source_book': book['title'],
            'expertise': book['topic'],
            'knowledge_base': f'ghost-book/corpus/{book[\"identifier\"]}.json',
            'personality': 'Academic expert, speaks with authority but accessibility',
            'revenue_path': 'License to publisher, educational platform, or expert chatbot',
            'status': 'spec_ready'
        }
        ai_authors.append(author_spec)
        print(f'AI Author spec: {author_spec[\"character_name\"]} — {book[\"topic\"][:40]}')

json.dump(ai_authors,
          open('G:/My Drive/Projects/ghost-book/ai-author-specs.json', 'w'), indent=2)
print(f'{len(ai_authors)} AI Author specs created')
print('Send to Art Department for character visual development')
"
```

## Review & Criticism Sources

### Scraping Targets
| Source | URL Pattern | Method |
|---|---|---|
| Goodreads | `goodreads.com/search?q=[TOPIC]&search_type=books` | HTML scrape |
| Google Books | `books.googleapis.com/books/v1/volumes?q=[TOPIC]` | API (no key needed for basic) |
| Amazon reviews | `amazon.com/s?k=[TOPIC]+book` → 1-3 star reviews | HTML scrape |
| LibraryThing | `librarything.com/search.php?search=[TOPIC]` | HTML scrape |
| Academic via CDX | `jstor.org/*`, `academia.edu/*review*` | Wayback CDX |

### Weak-Premise Signal Strings
Search review text for these to identify updatable books:
```
"premise is flawed but"
"outdated when published"
"data has since shown"
"theory has been disproven"
"needs to be updated"
"lacks supporting evidence"
"fascinating premise let down by"
"published too early"
"evidence was not available"
"would benefit from revision"
```

### Concatenation Signals
These phrases in reviews indicate multi-book merge opportunities:
```
"should be read alongside"
"complements perfectly with"
"covers what X missed"
"better together with"
"the missing piece that X needed"
"pairs well with"
"read in conjunction"
```

## Lore Topic Clusters

### Atlantis / Ancient Civilization Cluster
High-value for ghost book pipeline — many outdated books with new archaeological data:
```python
atlantis_topics = [
    ('atlantis plato ancient civilization', '1850', '2005', 'atlantis', 'atlantis'),
    ('ancient civilization flood catastrophe', '1850', '2005', 'flood myth ancient', 'deluge'),
    ('sunken continent archaeology underwater', '1900', '2005', 'underwater ruins', 'lost civilization'),
    ('prehistoric advanced civilization evidence', '1900', '2005', 'prehistoric civilization', 'prehistoric'),
    ('antediluvian technology ancient', '1850', '1990', 'antediluvian', 'antediluvian'),
    ('graham hancock fingerprints gods', '1990', '2010', 'graham hancock', 'ancient mysteries'),
    ('charles hapgood maps ancient sea kings', '1950', '2000', 'hapgood ancient maps', 'ancient maps'),
    ('underwater ruins archaeology ancient', '1970', '2010', 'underwater archaeology', 'underwater ruins'),
]
```

### Lore Pattern Cluster (for Lore Pattern Crawler)
```python
lore_topics = [
    ('sumerian anunnaki ancient astronauts', '1960', '2010', 'sumerian anunnaki', 'anunnaki'),
    ('egyptian pyramid construction theories', '1850', '2010', 'pyramid construction', 'pyramids'),
    ('gobekli tepe prehistoric civilization', '1990', '2015', 'gobekli tepe', 'gobekli tepe'),
    ('younger dryas impact hypothesis comet', '1980', '2010', 'younger dryas comet', 'younger dryas'),
    ('dogon tribe sirius astronomical knowledge', '1950', '2005', 'dogon sirius', 'dogon'),
    ('piri reis map ancient cartography', '1950', '2005', 'piri reis map', 'ancient maps'),
    ('nan madol megalithic construction mystery', '1960', '2010', 'nan madol', 'nan madol'),
    ('yonaguni underwater monument japan', '1980', '2010', 'yonaguni monument', 'yonaguni'),
]
```

To run Pass 1 against lore clusters, append `atlantis_topics + lore_topics` to `search_topics`
in `pass1_find_candidates.py` before running.

## Review Sources Config
Saved to: `ghost-book/review-sources.json`

## Running Ghost Book Division
```
Load ghost-book-division.md. Run all 4 passes. Find viable books and concatenation opportunities.
```

For lore cluster search only:
```
python G:/My Drive/Projects/ghost-book/pass1_atlantis_lore.py
```

## Output Files
- `ghost-book/candidates.json` — original 12-topic search results
- `ghost-book/candidates-expanded.json` — 5-source expanded search results
- `ghost-book/candidates-atlantis-lore.json` — Atlantis + lore cluster results
- `ghost-book/review-signals.json` — low-rated books flagged by review mining
- `ghost-book/review-sources.json` — full review source config
- `ghost-book/validated.json` — premises validated against 2026 data
- `ghost-book/concat-opportunities.json` — multi-book merge opportunities
- `ghost-book/ai-author-specs.json` — AI author character specs -> Art Department
