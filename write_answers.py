import json
from datetime import datetime

NOW = datetime.now().isoformat()[:19]
TODAY = datetime.now().strftime("%Y-%m-%d")

inbox_path = "G:/My Drive/Projects/_studio/mobile-inbox.json"
inbox = json.load(open(inbox_path, encoding='utf-8', errors='replace'))
if isinstance(inbox, dict):
    inbox = inbox.get('items', [])

new_items = [
    {
        "id": f"idea-ebay-listing-creator-{TODAY}",
        "project": "_studio",
        "type": "new_project_idea",
        "title": "eBay Listing Creator",
        "question": "Should we create a new project for eBay listing creation — separate from Listing Optimizer?",
        "context": (
            "Joe mentioned needing a listing/lookup project for CREATION of new eBay listings "
            "(vs Listing Optimizer which handles bulk optimization of existing listings via CSV). "
            "Two related tools: (1) Listing Creator — guided flow for creating new listings from scratch, "
            "potentially photo-driven. (2) Visual Inventory Lookup — dynamic Google Photos-style browser "
            "of Joe's inventory. Both complement Listing Optimizer. Could be one project or two. "
            "Joe has 572+ active listings on joedealsonline."
        ),
        "status": "pending",
        "created": TODAY,
        "tags": ["ebay", "new-project", "inventory", "visual-lookup"],
        "source": "joe-session-2026-03-31"
    }
]

# Don't add duplicates
existing_ids = {i.get('id') for i in inbox}
added = 0
for item in new_items:
    if item['id'] not in existing_ids:
        inbox.append(item)
        added += 1
        print(f"  added: {item['id']}")

json.dump(inbox, open(inbox_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"mobile-inbox.json updated — {added} item(s) added")
