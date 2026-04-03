import json
data = json.loads(open("G:/My Drive/Projects/_studio/data/wasde/price-history.json", encoding="utf-8").read())
for comm, prices in data["commodities"].items():
    if prices:
        print(f"{comm:12}: {prices[0]['date']} to {prices[-1]['date']} ({len(prices)} months) — latest: {prices[-1]['price_usd']}")
    else:
        print(f"{comm:12}: NO DATA")
