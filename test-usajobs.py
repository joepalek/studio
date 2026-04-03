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

def load_config():
    try:
        with open('G:/My Drive/Projects/_studio/studio-config.json', 'r') as f:
            config = json.load(f)
        return config.get('usajobs_api_key')
    except Exception as e:
        print(f'Error loading config: {e}')
        return None

print('Loading USAJOBS API key from studio-config.json...')
usajobs_key = load_config()

if usajobs_key:
    print(f'Key loaded: {usajobs_key[:15]}...')
    print('Testing USAJOBS API...')
    
    try:
        api_url = 'https://data.usajobs.gov/api/search'
        params = {'Keyword': '*', 'ResultsPerPage': '1'}
        query_string = urllib.parse.urlencode(params)
        full_url = f'{api_url}?{query_string}'
        
        req = urllib.request.Request(full_url, headers={
            'User-Agent': 'JobDiscovery/1.0',
            'Authorization-Key': usajobs_key
        })
        
        r = urllib.request.urlopen(req, timeout=15)
        data = json.loads(r.read().decode())
        
        search_result = data.get('SearchResult', {})
        total_jobs = search_result.get('TotalMatchingJobs', 0)
        
        print(f'SUCCESS: USAJOBS returned {total_jobs} total matching jobs')
        print('API key is valid and working!')
        
    except urllib.error.HTTPError as e:
        print(f'ERROR: HTTP {e.code} - Authentication failed')
    except Exception as e:
        print(f'ERROR: {e}')
else:
    print('ERROR: No API key found in studio-config.json')
