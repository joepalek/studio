import json, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TODAY = datetime.now().strftime("%Y-%m-%d")
NOW = datetime.now().isoformat()[:19]

inbox_path = "G:/My Drive/Projects/_studio/mobile-inbox.json"
inbox = json.load(open(inbox_path, encoding='utf-8', errors='replace'))
if isinstance(inbox, dict):
    inbox = inbox.get('items', [])

moved = 0
for item in inbox:
    iid = item.get('id', '')
    if 'ebay-image-listing-app' in iid or 'ebay-consensus-engine' in iid:
        item['status'] = 'build'
        item['moved_to_build'] = NOW
        item['build_ready'] = True
        moved += 1
        print(f"  moved to build: {item.get('title','?')}")

json.dump(inbox, open(inbox_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Done — {moved} items moved to build queue")
