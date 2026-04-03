import json
import urllib.request
import urllib.parse
import time
from pathlib import Path

OUTPUT_DIR = Path('G:/My Drive/Projects/job-match/source-discovery/')

print('Querying Common Crawl CDX for job posting patterns...')

# Common Crawl crawl ID we verified above
crawl_id = 'CC-MAIN-2026-12'

# Patterns that indicate job posting sites
patterns = [
    '*.indeed.com/jobs*',
    '*.linkedin.com/jobs*',
    '*.monster.com/jobs*',
    '*.dice.com/jobs*',
    '*.builtin.com/jobs*',
    '*.greenhouse.io/jobs*',
    '*careers.company.com*',
    '*jobs.company.com*',
    '*recruit*.com*'
]

all_results = []
errors = []

for pattern in patterns:
    print(f'\n  Searching: {pattern}')
    try:
        # CDX API query
        cdx_url = f'https://index.commoncrawl.org/{crawl_id}-index?url={pattern}&filter=statuscode:200&output=json&limit=100'
        
        r = urllib.request.urlopen(cdx_url, timeout=15)
        data = json.loads(r.read().decode())
        
        # data is array: first row is metadata, rest are results
        if isinstance(data, list) and len(data) > 1:
            count = len(data) - 1
            print(f'    Found: {count} URLs')
            all_results.extend(data[1:])  # Skip header row
        else:
            print(f'    Found: 0 URLs')
            
    except Exception as e:
        print(f'    ERROR: {e}')
        errors.append({'pattern': pattern, 'error': str(e)})
    
    time.sleep(1)  # Rate limiting

print(f'\n=== SUMMARY ===')
print(f'Total URLs found: {len(all_results)}')
print(f'Patterns with errors: {len(errors)}')

# Save results
results = {
    'timestamp': str(time.time()),
    'crawl_id': crawl_id,
    'patterns_queried': len(patterns),
    'total_urls': len(all_results),
    'urls': all_results,
    'errors': errors
}

output_file = OUTPUT_DIR / 'common-crawl-job-results.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f'Results saved to: {output_file}')
