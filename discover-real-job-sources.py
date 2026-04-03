import json
import urllib.request
import urllib.parse
import time
from pathlib import Path
from xml.etree import ElementTree as ET

OUTPUT_DIR = Path('G:/My Drive/Projects/job-match/source-discovery/')

print('Building job source inventory from public sitemaps and APIs...\n')

results = {
    'timestamp': str(time.time()),
    'sources': [],
    'errors': []
}

# JOB BOARDS WITH PUBLIC SITEMAPS/APIs
job_sources = [
    {'name': 'Indeed', 'sitemap': 'https://www.indeed.com/sitemap_index.xml', 'type': 'sitemap'},
    {'name': 'LinkedIn Jobs', 'sitemap': 'https://www.linkedin.com/jobs/sitemap/', 'type': 'sitemap'},
    {'name': 'Monster', 'sitemap': 'https://www.monster.com/sitemap.xml', 'type': 'sitemap'},
    {'name': 'ZipRecruiter', 'api': 'https://api.ziprecruiter.com/jobs', 'type': 'api'},
    {'name': 'Dice', 'sitemap': 'https://www.dice.com/sitemap.xml', 'type': 'sitemap'},
    {'name': 'Built In', 'sitemap': 'https://builtin.com/sitemap.xml', 'type': 'sitemap'},
    {'name': 'Greenhouse', 'api': 'https://greenhouse.io/jobs', 'type': 'api'},
    {'name': 'Lever', 'api': 'https://api.lever.co/v0/postings', 'type': 'api'},
]

# COMPANY CAREERS PAGES
company_careers = [
    'google.com/careers',
    'amazon.com/careers',
    'microsoft.com/careers',
    'apple.com/careers',
    'meta.com/careers',
    'tesla.com/careers',
    'netflix.com/careers',
    'airbnb.com/careers',
    'stripe.com/careers',
    'github.com/careers',
]

print('[1/3] Testing job board sitemaps...')
for source in job_sources:
    if source['type'] != 'sitemap':
        continue
    
    try:
        url = source['sitemap']
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=5)
        
        print(f'  ✓ {source["name"]} — {url}')
        results['sources'].append({
            'name': source['name'],
            'url': url,
            'status': 'accessible',
            'type': 'sitemap'
        })
    except Exception as e:
        print(f'  ✗ {source["name"]} — {e}')
        results['errors'].append({'source': source['name'], 'error': str(e)})

print('\n[2/3] Testing job board APIs...')
for source in job_sources:
    if source['type'] != 'api':
        continue
    
    try:
        url = source.get('api', '')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=5)
        
        print(f'  ✓ {source["name"]} — {url}')
        results['sources'].append({
            'name': source['name'],
            'url': url,
            'status': 'accessible',
            'type': 'api'
        })
    except Exception as e:
        print(f'  ✗ {source["name"]} — {e}')
        results['errors'].append({'source': source['name'], 'error': str(e)})

print('\n[3/3] Testing company careers pages...')
for company in company_careers[:5]:  # Test first 5
    try:
        url = f'https://{company}/'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=5)
        
        print(f'  ✓ {company}')
        results['sources'].append({
            'name': company,
            'url': url,
            'status': 'accessible',
            'type': 'company_careers'
        })
    except Exception as e:
        print(f'  ✗ {company}')

print(f'\n=== SUMMARY ===')
print(f'Accessible sources: {len([s for s in results["sources"] if s["status"] == "accessible"])}')
print(f'Errors: {len(results["errors"])}')

output_file = OUTPUT_DIR / 'job-sources-real.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f'\nSaved to: {output_file}')
