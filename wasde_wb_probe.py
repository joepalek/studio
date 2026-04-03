"""Check World Bank response and find correct Pink Sheet URL."""
import urllib.request, json

# Check what the World Bank JSON returned
req = urllib.request.Request(
    "https://api.worldbank.org/v2/en/indicator/PCOMM_USD?downloadformat=json",
    headers={"User-Agent": "StudioAgent/1.0"}
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = r.read()
    print("World Bank response:", data[:300])

# Try correct commodity price indicators
# Corn = PMAIZE_USD, Wheat = PWHEAMT_USD, Soybeans = PSOYB_USD
indicators = {
    "Corn":     "PMAIZE_USD",
    "Wheat":    "PWHEAMT_USD",
    "Soybeans": "PSOYB_USD",
    "Cotton":   "PCOTTIND_USD",
    "Rice":     "PRICENPQ_USD",
}
print("\n=== WORLD BANK COMMODITY PRICES ===")
for name, code in indicators.items():
    url = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
           f"?format=json&mrv=3&frequency=M")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "StudioAgent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            # resp[0] = pagination info, resp[1] = data
            if len(resp) > 1 and resp[1]:
                latest = resp[1][0]
                print(f"  {name:12} {code:20} latest: {latest.get('value','?')} "
                      f"{latest.get('date','?')}")
            else:
                print(f"  {name:12} {code} — no data returned")
    except Exception as e:
        print(f"  {name:12} FAIL: {str(e)[:60]}")
