import json
import urllib.request
import urllib.parse

usajobs_key = 'UbAQHbtHJcxV7IJ...'  # Your actual key
your_email = 'your_email@example.com'  # CRITICAL: Use your actual email

api_url = 'https://data.usajobs.gov/api/search'
params = {
    'Keyword': 'engineer',
    'ResultsPerPage': '1'
}

query_string = urllib.parse.urlencode(params)
full_url = f'{api_url}?{query_string}'

# CORRECT headers per USAJOBS documentation
req = urllib.request.Request(full_url, headers={
    'Host': 'data.usajobs.gov',
    'User-Agent': your_email,  # NOT application name - YOUR EMAIL
    'Authorization-Key': usajobs_key
})

try:
    r = urllib.request.urlopen(req, timeout=15)
    data = json.loads(r.read().decode())
    
    total = data.get('SearchResult', {}).get('TotalMatchingJobs', 0)
    print(f'SUCCESS: Found {total} jobs')
    print('Headers were correct!')
    
except urllib.error.HTTPError as e:
    print(f'ERROR: HTTP {e.code}')
