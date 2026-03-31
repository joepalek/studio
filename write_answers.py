import json
from datetime import datetime

NOW = datetime.now().isoformat()[:19]
TODAY = datetime.now().strftime("%Y-%m-%d")

inbox_path = "G:/My Drive/Projects/_studio/mobile-inbox.json"
inbox = json.load(open(inbox_path, encoding='utf-8', errors='replace'))
if isinstance(inbox, dict):
    inbox = inbox.get('items', [])

# Remove the placeholder item added earlier
inbox = [i for i in inbox if i.get('id') != f"idea-ebay-listing-creator-{TODAY}"]

# Add the properly scoped item with full context
new_item = {
    "id": f"project-ebay-image-listing-app-{TODAY}",
    "project": "_studio",
    "type": "new_project_idea",
    "title": "eBay Image Listing App (Visual Lookup + Listing Creator)",
    "question": "Ready to formalize and build the eBay Image Listing App as a studio project?",
    "context": (
        "Previously scoped in detail (chat: 5be8454e-aa34-4f60-8750-f4083a222b0c, Mar 13 2026). "
        "Core concept: upload photo of item(s) → Gemini Vision identifies everything in image → "
        "looks up item data + eBay sold prices → generates listing title + suggested price. "
        "Lot logic: items under $15 suggested as lots. All items in image covered in output, "
        "either single or lot listing. Export to eBay via Trading API to create draft listings. "
        "Enhanced vision: multi-source lookup (not just eBay), reroll with picked pictures, "
        "Google Photos-style visual inventory browser as companion feature. "
        "Complements Listing Optimizer (bulk CSV optimizer) — this is the CREATION side. "
        "eBay dev account registration was in progress Mar 13. "
        "Infrastructure overlap: eBay API OAuth (shared with Listing Optimizer + Arbitrage Pulse), "
        "Gemini Vision API already proven in Joe's workflow. "
        "Status: scoped, waiting on eBay Developer Program approval + OAuth setup. "
        "Joe has 572+ active listings on joedealsonline. "
        "Prior chat reference: https://claude.ai/chat/5be8454e-aa34-4f60-8750-f4083a222b0c"
    ),
    "status": "pending",
    "created": TODAY,
    "tags": ["ebay", "new-project", "vision-api", "listing-creator", "visual-lookup", "gemini"],
    "source": "joe-session-2026-03-31",
    "prior_chat": "https://claude.ai/chat/5be8454e-aa34-4f60-8750-f4083a222b0c"
}

inbox.append(new_item)
json.dump(inbox, open(inbox_path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
print(f"Inbox updated — replaced placeholder with full scoped item")
print(f"ID: {new_item['id']}")
