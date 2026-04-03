import json
import urllib.request
import urllib.parse

usajobs_key = 'UbAQHbtHJcxV7IJ...'  # Use your actual key

# Try with actual keywords instead of wildcard
keywords = ['engineer', 'analyst', 'manager', 'nurse', 'technician']

for keyword in keywords:
    try:
        api_url = 'https://data.usajobs.gov/api/search'
        params = {
            'Keyword': keyword,
            'ResultsPerPage': '1'
        }
        
        query_string = urllib.parse.urlencode(params)
        full_url = f'{api_url}?{query_string}'
        
        req = urllib.request.Request(full_url, headers={
            'User-Agent': 'JobDiscovery/1.0',
            'Authorization-Key': usajobs_key
        })
        
        r = urllib.request.urlopen(req, timeout=15)
        data = json.loads(r.read().decode())
        
        total = data.get('SearchResult', {}).get('TotalMatchingJobs', 0)
        print(f'{keyword:.<20} {total:>10,} jobs')
        
    except Exception as e:
        print(f'{keyword:.<20} ERROR: {e}')
