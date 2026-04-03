import json
import urllib.request
import urllib.parse

usajobs_key = 'UbAQHbtHJcxV7IJ...'

api_url = 'https://data.usajobs.gov/api/search'
params = {
    'Keyword': 'engineer',
    'ResultsPerPage': '1',
    'ApiKey': usajobs_key
}

query_string = urllib.parse.urlencode(params)
full_url = f'{api_url}?{query_string}'

req = urllib.request.Request(full_url, headers={
    'Host': 'data.usajobs.gov',
    'User-Agent': 'joepalek@gmail.com'
})

try:
    r = urllib.request.urlopen(req, timeout=15)
    data = json.loads(r.read().decode())
    total = data.get('SearchResult', {}).get('TotalMatchingJobs', 0)
    print(f'SUCCESS: Found {total} jobs')
    print('API key as query param works!')
except urllib.error.HTTPError as e:
    print(f'ERROR: HTTP {e.code}')
    print('Trying alternative format...')
