import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().isoformat()[:19]

inbox_path = "G:/My Drive/Projects/_studio/mobile-inbox.json"
inbox = json.load(open(inbox_path, encoding='utf-8', errors='replace'))
if isinstance(inbox, dict):
    inbox = inbox.get('items', [])

# Update both eBay project inbox items to add the product architecture decision
for item in inbox:
    if 'ebay-image-listing-app' in item.get('id','') or 'ebay-consensus-engine' in item.get('id',''):
        existing = item.get('context','')
        if 'PRODUCT ARCH' not in existing:
            item['context'] = existing + (
                " PRODUCT ARCH DECISION (2026-03-31): "
                "Combined as single personal tool for Joe's use. "
                "Split into separate products only if taken to market or beta test groups. "
                "Shared eBay OAuth infrastructure already scaffolded (ebay_oauth.py). "
                "RuName is only missing credential — add to studio-config.json to activate."
            )
            item['updated'] = NOW
            print(f"  updated: {item['id']}")

json.dump(inbox, open(inbox_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print("inbox updated")
