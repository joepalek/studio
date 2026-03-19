import urllib.request, urllib.parse, json, time, os
from datetime import datetime

BASE = 'G:/My Drive/Projects/_studio/vintage'
os.makedirs(BASE, exist_ok=True)

CONFIG = json.load(open('G:/My Drive/Projects/_studio/studio-config.json'))
GEMINI_KEY = CONFIG.get('gemini_api_key', '')

DECADES = ['1920s','1930s','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s']

def wiki_fetch(title):
    params = urllib.parse.urlencode({
        'action': 'query',
        'titles': title,
        'prop': 'extracts',
        'exintro': True,
        'explaintext': True,
        'format': 'json',
        'exsectionformat': 'plain',
        'exchars': 3000,
    })
    url = f'https://en.wikipedia.org/w/api.php?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': 'VintageAgent/1.0 (research)'})
    r = urllib.request.urlopen(req, timeout=15)
    data = json.loads(r.read())
    pages = data.get('query', {}).get('pages', {})
    for page in pages.values():
        return page.get('extract', '')
    return ''

def gemini_structure(decade, raw_text):
    prompt = f"""You are building a decade reference profile for the {decade}.
Based on this Wikipedia content and your knowledge, return a structured JSON profile.

Wikipedia content:
{raw_text[:2000]}

Return ONLY valid JSON with this exact structure:
{{
  "decade": "{decade}",
  "slang": ["term1", "term2", "term3", "term4", "term5", "term6", "term7", "term8", "term9", "term10"],
  "concerns": ["concern1", "concern2", "concern3", "concern4", "concern5"],
  "aspirations": ["what people wanted to own or achieve - 5 items"],
  "fashion": {{
    "men": "2 sentence description",
    "women": "2 sentence description",
    "colors": ["color1", "color2", "color3"]
  }},
  "food": ["defining food/drink 1", "defining food/drink 2", "defining food/drink 3", "defining food/drink 4", "defining food/drink 5"],
  "entertainment": {{
    "tv": ["show1", "show2", "show3"],
    "music": ["artist/genre 1", "artist/genre 2", "artist/genre 3"],
    "movies": ["movie1", "movie2", "movie3"],
    "games": ["game/activity 1", "game/activity 2"]
  }},
  "technology": {{
    "home": ["tech item 1", "tech item 2", "tech item 3"],
    "aspirational": ["tech people wanted 1", "tech people wanted 2"],
    "work": ["work tech 1", "work tech 2"]
  }},
  "defining_products": ["product1", "product2", "product3", "product4", "product5"],
  "failed_products": [
    {{"name": "product name", "why_failed": "brief reason", "modern_gap": "is this gap still unfilled in 2026?"}}
  ],
  "ebay_hot_now": ["trending vintage item 1", "trending vintage item 2", "trending vintage item 3"],
  "ebay_sleepers": ["undervalued item 1", "undervalued item 2", "undervalued item 3"],
  "character_voice": {{
    "catchphrases": ["phrase1", "phrase2", "phrase3"],
    "worldview": "2 sentence description of how someone from this era sees the world",
    "speech_patterns": "1 sentence on how they talk",
    "taboo_topics": ["thing they wouldn't discuss openly 1", "thing 2"]
  }},
  "story_accuracy": ["common anachronism writers make 1", "common anachronism 2", "common anachronism 3"]
}}"""

    payload = json.dumps({'contents': [{'parts': [{'text': prompt}]}]}).encode()
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}'
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, timeout=30)
    text = json.loads(r.read())['candidates'][0]['content']['parts'][0]['text'].strip()
    text = text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

print(f'Building decade profiles: {", ".join(DECADES)}')
print(f'Output: {BASE}')
print()

all_profiles = []
for decade in DECADES:
    print(f'=== {decade} ===')

    # Pass 1: Wikipedia raw data
    raw_parts = []
    for title in [decade, f'Culture of the {decade}', f'Technology in the {decade}']:
        try:
            text = wiki_fetch(title)
            if text:
                raw_parts.append(text)
                print(f'  Wiki "{title}": {len(text)} chars')
        except Exception as e:
            print(f'  Wiki "{title}": ERROR - {str(e)[:40]}')
        time.sleep(0.3)

    raw_combined = '\n\n'.join(raw_parts)

    # Save raw
    raw_path = os.path.join(BASE, f'{decade}-raw.json')
    json.dump({'decade': decade, 'raw_text': raw_combined, 'fetched': datetime.now().isoformat()},
              open(raw_path, 'w'), indent=2)

    # Pass 2: Gemini structure
    if not GEMINI_KEY:
        print(f'  SKIP Gemini — no key')
        continue

    try:
        profile = gemini_structure(decade, raw_combined)
        profile_path = os.path.join(BASE, f'{decade}-profile.json')
        json.dump(profile, open(profile_path, 'w'), indent=2)
        slang_sample = ', '.join(profile.get('slang', [])[:3])
        failed = len(profile.get('failed_products', []))
        hot = len(profile.get('ebay_hot_now', []))
        print(f'  Profile built: slang=[{slang_sample}...], {failed} failed products, {hot} eBay hot items')
        all_profiles.append(profile)
    except Exception as e:
        print(f'  Gemini ERROR: {str(e)[:80]}')

    time.sleep(2)  # Gemini rate limit

# Pass 3: eBay intelligence extract
print('\n=== Extracting eBay Intelligence ===')
ebay_intel = {'hot_items': [], 'sleepers': [], 'product_gaps': []}
for profile in all_profiles:
    decade = profile.get('decade', '')
    for item in profile.get('ebay_hot_now', []):
        ebay_intel['hot_items'].append({'decade': decade, 'item': item})
    for item in profile.get('ebay_sleepers', []):
        ebay_intel['sleepers'].append({'decade': decade, 'item': item})
    for fp in profile.get('failed_products', []):
        if fp.get('modern_gap'):
            ebay_intel['product_gaps'].append({
                'decade': decade,
                'product': fp.get('name', ''),
                'why_failed': fp.get('why_failed', ''),
                'modern_gap': fp.get('modern_gap', ''),
                'type': 'product_gap',
                'whiteboard_tags': ['product_archaeology', 'vintage', f'vintage-{decade}']
            })

json.dump(ebay_intel, open(os.path.join(BASE, 'ebay-vintage-intel.json'), 'w'), indent=2)
print(f'  Hot items: {len(ebay_intel["hot_items"])}')
print(f'  Sleepers: {len(ebay_intel["sleepers"])}')
print(f'  Product gaps: {len(ebay_intel["product_gaps"])}')

# Pass 4: Character voice library
print('\n=== Building Character Voice Library ===')
voice_lib = {}
for profile in all_profiles:
    decade = profile.get('decade', '')
    voice_lib[decade] = profile.get('character_voice', {})
    voice_lib[decade]['slang'] = profile.get('slang', [])
    voice_lib[decade]['story_accuracy'] = profile.get('story_accuracy', [])

json.dump(voice_lib, open(os.path.join(BASE, 'character-voice-library.json'), 'w'), indent=2)
print(f'  Voice profiles: {len(voice_lib)} decades')

# Push product gaps to whiteboard
WHITEBOARD = 'G:/My Drive/Projects/_studio/whiteboard.json'
wb = {'updated': datetime.now().isoformat(), 'items': []}
if os.path.exists(WHITEBOARD):
    wb = json.load(open(WHITEBOARD))

existing = {i.get('title','').lower() for i in wb.get('items', [])}
pushed = 0
for gap in ebay_intel['product_gaps']:
    title = gap.get('product', '')
    if title.lower() not in existing:
        wb.setdefault('items', []).append({
            'id': f'vint-{len(wb["items"])+1:04d}',
            'type': 'product_gap',
            'title': title,
            'description': gap.get('modern_gap', ''),
            'decade_origin': gap.get('decade', ''),
            'why_failed': gap.get('why_failed', ''),
            'tags': gap.get('whiteboard_tags', []),
            'added': datetime.now().isoformat(),
            'status': 'new'
        })
        existing.add(title.lower())
        pushed += 1

json.dump(wb, open(WHITEBOARD, 'w'), indent=2)
print(f'  Pushed {pushed} product gaps to whiteboard.json')

print(f'\nDone. {len(all_profiles)} decade profiles built.')
print(f'Files saved to {BASE}')
