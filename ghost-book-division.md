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

### Pass 1 — Find Ghost Book Candidates
```bash
python -c "
import urllib.request, json, time, os

OUTPUT = 'G:/My Drive/Projects/job-match/../ghost-book/candidates.json'
os.makedirs('G:/My Drive/Projects/ghost-book', exist_ok=True)

# Topics where books failed due to data gaps now fillable
search_topics = [
    # Materials science
    ('hemp composite materials industrial', '1980', '2005'),
    ('graphene applications manufacturing', '1990', '2010'),
    # Computing/AI
    ('neural network practical applications', '1985', '2000'),
    ('machine learning business applications', '1995', '2008'),
    # Alternative energy
    ('hydrogen fuel cell vehicles', '1990', '2005'),
    ('solar panel efficiency residential', '1985', '2005'),
    # Ancient technology
    ('vedic mathematics computing algorithms', '1960', '2000'),
    ('ancient metallurgy impossible artifacts', '1970', '2010'),
    # Medicine
    ('microbiome gut health disease', '1990', '2008'),
    ('psychedelic therapy clinical', '1960', '1975'),
    # Economics
    ('universal basic income feasibility', '1960', '2000'),
    ('circular economy waste elimination', '1980', '2005'),
]

# Search Internet Archive for these books
candidates = []
for topic, year_from, year_to in search_topics:
    encoded = urllib.request.quote(topic)
    url = (f'https://archive.org/advancedsearch.php?q={encoded}'
           f'+mediatype:texts+date:[{year_from} TO {year_to}]'
           f'&fl=identifier,title,date,creator,subject'
           f'&output=json&rows=10')
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        docs = data.get('response', {}).get('docs', [])
        for doc in docs:
            candidates.append({
                'topic': topic,
                'title': doc.get('title', ''),
                'author': doc.get('creator', ''),
                'date': doc.get('date', ''),
                'identifier': doc.get('identifier', ''),
                'archive_url': f'https://archive.org/details/{doc.get(\"identifier\",\"\")}',
                'status': 'candidate'
            })
        print(f'  {topic[:40]}: {len(docs)} books found')
    except Exception as e:
        print(f'  {topic[:40]}: ERROR — {e}')
    time.sleep(1)

json.dump({'candidates': candidates, 'count': len(candidates)},
          open('G:/My Drive/Projects/ghost-book/candidates.json', 'w'), indent=2)
print(f'Total candidates: {len(candidates)}')
"
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

## Running Ghost Book Division
```
Load ghost-book-division.md. Run all 4 passes. Find viable books and concatenation opportunities.
```

## Output Files
- `ghost-book/candidates.json` — books found in archive
- `ghost-book/validated.json` — premises validated against 2026 data
- `ghost-book/concat-opportunities.json` — multi-book merge opportunities
- `ghost-book/ai-author-specs.json` — AI author character specs → Art Department
