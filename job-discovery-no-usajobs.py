import json
import urllib.request
import urllib.parse
import time
from datetime import datetime
from pathlib import Path
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OUTPUT_DIR = Path('G:/My Drive/Projects/job-match/source-discovery/')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

results = {
    'timestamp': datetime.now().isoformat(),
    'sources': {
        'common_crawl': {'status': 'pending', 'data': []},
        'company_sitemaps': {'status': 'pending', 'data': []},
        'job_boards': {'status': 'pending', 'data': []},
        'state_labor': {'status': 'pending', 'data': []},
        'blockers': []
    }
}

print('[1/4] Testing Common Crawl CDX API...')
try:
    cc_url = 'https://index.commoncrawl.org/collinfo.json'
    r = urllib.request.urlopen(cc_url, timeout=10)
    cc_info = json.loads(r.read().decode())
    
    # Get latest crawl
    latest_crawl = cc_info[0]
    print(f'  Latest crawl: {latest_crawl.get("id")}')
    results['sources']['common_crawl']['status'] = 'ready'
    results['sources']['common_crawl']['data'] = [latest_crawl]
    
except Exception as e:
    print(f'  ERROR: {e}')
    results['sources']['blockers'].append(f'Common Crawl: {e}')

print('[2/4] Testing company sitemaps...')
companies = [
    'google.com', 'amazon.com', 'microsoft.com', 'apple.com', 'meta.com',
    'tesla.com', 'nvidia.com', 'oracle.com', 'salesforce.com', 'adobe.com',
    'ibm.com', 'intel.com', 'cisco.com', 'vmware.com', 'servicenow.com',
    'workday.com', 'linkedin.com', 'github.com', 'stripe.com', 'square.com',
    'shopify.com', 'airbnb.com', 'uber.com', 'lyft.com', 'doordash.com'
]

successful_sitemaps = []
for company in companies[:5]:  # Test first 5
    try:
        sitemap_url = f'https://{company}/sitemap.xml'
        r = urllib.request.urlopen(sitemap_url, timeout=5)
        if r.status == 200:
            successful_sitemaps.append(sitemap_url)
            print(f'  ✓ {company}')
    except:
        pass

results['sources']['company_sitemaps']['status'] = 'partial'
results['sources']['company_sitemaps']['data'] = successful_sitemaps
print(f'  Found {len(successful_sitemaps)}/5 working sitemaps')

print('[3/4] Testing job board APIs...')
job_boards = {
    'indeed': 'https://www.indeed.com/robots.txt',
    'linkedin': 'https://www.linkedin.com/robots.txt',
    'glassdoor': 'https://www.glassdoor.com/robots.txt',
    'ziprecruiter': 'https://www.ziprecruiter.com/robots.txt',
}

board_results = {}
for name, url in job_boards.items():
    try:
        r = urllib.request.urlopen(url, timeout=5)
        board_results[name] = 'accessible'
        print(f'  ✓ {name}')
    except Exception as e:
        board_results[name] = str(e)
        print(f'  ✗ {name}: {e}')

results['sources']['job_boards']['status'] = 'checked'
results['sources']['job_boards']['data'] = board_results

print('[4/4] Testing state labor boards...')
state_boards = {
    'california': 'https://www.labor.ca.gov/',
    'texas': 'https://www.twc.texas.gov/',
    'florida': 'https://www.myflorida.com/jobsandbenefits/',
    'new_york': 'https://www.ny.gov/jobs/',
}

state_results = {}
for state, url in state_boards.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=5)
        state_results[state] = 'accessible'
        print(f'  ✓ {state}')
    except Exception as e:
        state_results[state] = str(e)
        print(f'  ✗ {state}: {e}')

results['sources']['state_labor']['status'] = 'checked'
results['sources']['state_labor']['data'] = state_results

print('\n=== SUMMARY ===')
print(f'Common Crawl: {results["sources"]["common_crawl"]["status"]}')
print(f'Company Sitemaps: {len(successful_sitemaps)} working')
print(f'Job Boards: {len([v for v in board_results.values() if v == "accessible"])} accessible')
print(f'State Labor: {len([v for v in state_results.values() if v == "accessible"])} accessible')
print(f'Total Blockers: {len(results["sources"]["blockers"])}')

# Write results
output_file = OUTPUT_DIR / 'discovery-run-no-usajobs.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
print(f'\nResults saved to: {output_file}')
