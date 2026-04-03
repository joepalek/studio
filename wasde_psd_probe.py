"""Try api_key as URL query param — standard api.data.gov pattern."""
import urllib.request, json
cfg = json.loads(open("G:/My Drive/Projects/_studio/studio-config.json", encoding="utf-8-sig").read())
KEY = cfg["dat.gov_api_key"]

# api.data.gov usually passes key as ?api_key= query param
# Also try the correct USDA FAS OpenData URL patterns
tests = [
    f"https://apps.fas.usda.gov/OpenData/api/psd/commodity?api_key={KEY}",
    f"https://apps.fas.usda.gov/OpenData/api/psd/commodities?api_key={KEY}",
    f"https://apps.fas.usda.gov/OpenData/api/psd/commodity?API_KEY={KEY}",
    # Try query string with X-Api-Key as param name
    f"https://apps.fas.usda.gov/OpenData/api/psd/commodity?X-Api-Key={KEY}",
]

for url in tests:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                    "User-Agent": "StudioAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            print(f"SUCCESS: {url[:80]}")
            print(f"  items={len(data)} sample={str(data[0])[:80]}")
    except Exception as e:
        code = str(e)[:60]
        print(f"FAIL {code}: {url[:80]}")
