import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

OUTPUT_DIR = Path('G:/My Drive/Projects/job-match/source-discovery/')

print('Querying Common Crawl CDX for job posting patterns (optimized)...')

crawl_id = 'CC-MAIN-2026-12'

# SMARTER PATTERNS: Specific URLs instead of wildcards
patterns = [
    'indeed.com/jobs',           # Single domain, specific path
    'linkedin.com/jobs',
    'monster.com/jobs',
    'dice.com/jobs',
    'glassdoor.com/jobs',
    'ziprecruiter.com/job',
    'builtin.com/jobs',
    'greenhouse.io',
    'workable.com/jobs',
    'lever.co/jobs'
]

all_urls = []
errors = []

for pattern in patterns:
    print(f'  Searching: {pattern}')
    try:
        # Simplified CDX query: just domain + path, no wildcards
        cdx_url = f'https://index.commoncrawl.org/{crawl_id}-index?url={pattern}&output=json&limit=50&filter=statuscode:200'
        
        r = urllib.request.urlopen(cdx_url, timeout=10)
        data = json.loads(r.read().decode())
        
        # First row is metadata headers, rest are results
        if isinstance(data, list) and len(data) > 1:
            urls = data[1:]  # Skip header
            count = len(urls)
            print(f'    Found: {count} URLs')
            all_urls.extend(urls)
        else:
            print(f'    Found: 0 URLs')
            
    except urllib.error.HTTPError as e:
        msg = f'HTTP {e.code}'
        print(f'    ERROR: {msg}')
        errors.append({'pattern': pattern, 'error': msg})
    except json.JSONDecodeError as e:
        msg = f'Malformed JSON'
        print(f'    ERROR: {msg}')
        errors.append({'pattern': pattern, 'error': msg})
    except Exception as e:
        msg = str(e)
        print(f'    ERROR: {msg}')
        errors.append({'pattern': pattern, 'error': msg})
    
    time.sleep(0.5)  # Gentle rate limiting

print(f'\n=== RESULTS ===')
print(f'Total URLs found: {len(all_urls)}')
print(f'Patterns with errors: {len(errors)}')

if all_urls:
    print(f'\nFirst 5 URLs:')
    for url in all_urls[:5]:
        print(f'  {url}')

# Save
results = {
    'crawl_id': crawl_id,
    'patterns_queried': len(patterns),
    'total_urls_found': len(all_urls),
    'urls': all_urls,
    'errors': errors
}

output_file = OUTPUT_DIR / 'common-crawl-job-urls.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f'\nSaved to: {output_file}')
